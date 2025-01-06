import json
from turtle import xcor
from sqlalchemy import Column, Integer, String
from models.base import Base
import itertools
from sqlalchemy.orm import relationship
import numpy as np
from models.round import Round
from scipy.cluster.hierarchy import linkage, fcluster

from util.strings import to_pdgalive_link

class Layout(Base):
    __tablename__ = 'Layouts'
    layout_id = Column(Integer, primary_key=True, autoincrement=True)
    layout_name = Column(String(200), nullable=False)
    num_holes = Column(Integer, nullable=False)
    pars = Column(String(200), nullable=False)
    distances = Column(String(200), nullable=True)
    total_par = Column(Integer, nullable=False)
    total_distance = Column(Integer, nullable=True)
    round = relationship("Round", back_populates="layout", uselist=False)

    def to_dict(self) -> dict:
        return {
            "layout_name": self.layout_name,
            "num_holes": self.num_holes,
            "pars": self.pars,
            "distances": self.distances,
            "total_par": self.total_par,
            "total_distance": self.total_distance
        }

class AggregateLayout:
    def __init__(self, rounds: list[Round]):
        """
        Generates an aggregate layout by averaging a list of layouts.
        Assumes that the list is non-empty and layouts have valid data.
        """
        self.rounds = rounds
        self.layouts = [x.layout for x in rounds]
        self.scores = itertools.chain([x.scores for x in rounds])
        self.num_layouts = len(self.layouts)
        self.num_tournaments = len(set([x.event_id for x in rounds]))
        self.num_holes = self.layouts[0].num_holes
        self.distances = self.averaged_distances()
        self.total_distance = int(np.mean([x.total_distance for x in self.layouts]))
        self.pars = [int(x) for x in self.layouts[0].pars.split(', ')]
        self.total_par = self.layouts[0].total_par
        self.layout_names = [x.layout_name for x in self.layouts]
        self.layout_tokens = self.tokenize_layout_names()
        self.descriptive_name = self.get_descriptive_name()
        self.par_rating = int(np.mean([x.par_rating for x in self.rounds]))
        self.stroke_value = int(np.mean([x.stroke_value for x in self.rounds]))

    def to_dict(self) -> dict:
        return {
            "num_layouts": self.num_layouts,
            "num_tournaments": self.num_tournaments,
            "num_holes": self.num_holes,
            "distances": self.distances,
            "total_distance": self.total_distance,
            "pars": self.pars,
            "total_par": self.total_par,
            "layout_names": self.layout_names,
            "layout_tokens": self.layout_tokens,
            "descriptive_name": self.descriptive_name,
            "par_rating": self.par_rating,
            "stroke_value": self.stroke_value
        }

    def averaged_distances(self) -> list[int]:
        str_distances = [x.distances.split(', ') for x in self.layouts]
        int_distances = [[int(x) for x in y] for y in str_distances]
        distances = []
        for i in range(self.num_holes):
            averaged_distance = int(np.mean([int_distances[j][i] for j in range(self.num_layouts)]))
            distances.append(averaged_distance)
        return distances

    def get_descriptive_name(self) -> str:
        filtered_tokens = [token for token in self.layout_tokens if len(token) > 2]
        filtered_tokens = [token for token in filtered_tokens if not token.isnumeric()]
        return ', '.join(filtered_tokens[0:5])
    
    def tokenize_layout_names(self) -> list[str]:
        tokens = []
        frequencies = {}
        for name in self.layout_names:
            tokens.extend(name.lower().split(' '))
        for token in tokens:
            if token in frequencies:
                frequencies[token] += 1
            else:
                frequencies[token] = 1
        sorted_frequencies = sorted(frequencies.items(), key=lambda item: item[1], reverse=True)
        sorted_tokens: list[str] = [token for (token, _) in sorted_frequencies]
        filtered_tokens = [x for x in sorted_tokens if x.isalnum() and len(x) > 2]
        return filtered_tokens
    
    def score_layout_tokens(self, keywords: list[str]) -> int:
        # TODO need more sophisticated algorithm
        return len([x for x in keywords if x.lower() in self.layout_tokens])

    def hole_distances(self, columns: int = 3) -> list[str]:
        holes_per_column = (len(self.distances) // columns)
        holes_per_column += 1 if len(self.distances) % columns != 0 else 0
        hole_columns = []
        for c in range(columns):
            start = c*holes_per_column
            dists = self.distances[c*holes_per_column:(c+1)*holes_per_column]
            pars = self.pars[c*holes_per_column:(c+1)*holes_per_column]
            hole_columns.append('\n'.join([f"H{start+i+1} p{pars[i]} {dists[i]}" for i, _ in enumerate(dists)]))
        return hole_columns
    
    def score_rating(self, score: int) -> int:
        return self.par_rating - score * self.stroke_value
    
    def calculate_variance(self) -> int:
        distances = [x.total_distance for x in self.layouts]
        return int(np.std(distances))
    
    def course_metadata(self) -> str:
        return (f"Par {self.total_par}, Distance {self.total_distance} feet")
    
    def layout_links(self) -> list[str]:
        event_ids = set([x.event_id for x in self.rounds])
        return [f"[{x}]({to_pdgalive_link(x)})" for x in event_ids]

def cluster_rounds(rounds: list[Round], maxgap):
    if not rounds:
        return []  # Return an empty list for empty input

    # Extract the attribute values
    distances = [x.layout.total_distance for x in rounds]

    # Perform hierarchical clustering
    linkage_matrix = linkage([[x] for x in distances], method='single')
    cluster_labels = fcluster(linkage_matrix, t=maxgap, criterion='distance')

    # Group objects based on cluster labels
    clusters = {}
    for round, label in zip(rounds, cluster_labels):
        clusters.setdefault(label, []).append(round)

    # Convert clusters to ranges of `total_distance`
    ranges = [
        (
            min(x.layout.total_distance for x in cluster),
            max(x.layout.total_distance for x in cluster),
        )
        for cluster in clusters.values()
    ]

    return list(clusters.values()), ranges

def filter_rounds(rounds: list[Round]) -> list[Round]:
    """
    Filters out layouts that do not have necessary data to be aggregated
    Args:
        layouts (list[Layout])
    Returns:
        list[Layout]: A list of Layout objects with complete distances, pars, total distance, etc.
    """
    filtered_rounds = []
    for round in rounds:
        # print(json.dumps(round.layout.to_dict(), indent=4))
        layout: Layout = round.layout
        hole_distances: list[str] = layout.distances.split(', ')
        pars: list[str] = layout.pars.split(', ')
        if len(hole_distances) != layout.num_holes:
            continue
        if len(pars) != layout.num_holes:
            continue
        if not all(x.isdigit() for x in hole_distances):
            continue
        if not all(x.isdigit() for x in pars):
            continue
        filtered_rounds.append(round)
    return filtered_rounds
    
def aggregate_layouts(rounds: list[Round], threshold: int = 0.5) -> list[AggregateLayout]:
    """
    Groups rounds into comparable layouts based on their hole distances, total distance, and par.
    Args:
        rounds (list[Round]): A list of Round objects to be grouped.
    Returns:
        list[Layout]: A list of Layout objects, each representing a group of comparable rounds.
    """
    if not rounds:
        return []
    aggregated_layouts: list[AggregateLayout] = []
    rounds = filter_rounds(rounds)
    clustered_rounds, ranges = cluster_rounds(rounds, 200)

    # BETTER SOLUTION
    # 1. remove layouts without distance data
    # 2. group layouts based on pars
    # 3. remove distance outliers
    # 
    rounds.sort(key=lambda x: x.layout.pars)
    for cluster in clustered_rounds:
        for _, group in itertools.groupby(cluster, key=lambda x: x.layout.pars):
            group_list = list(group)

            # TODO remove distance outliers
            if len(group_list) == 0:
                continue

            layout = AggregateLayout(group_list)
            aggregated_layouts.append(layout)

    aggregated_layouts.sort(key=lambda x: x.num_layouts, reverse=True)
    return aggregated_layouts
