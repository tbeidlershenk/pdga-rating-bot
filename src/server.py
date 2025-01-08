import sys
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from util.configuration import load_config_into_env
from util.database import Database
from waitress import serve
from logger import logger

app = Flask(__name__, static_folder='../site/build', static_url_path='/')
CORS(app)

status_none = -1
status_success = 0
status_error_no_matches = 1
status_error_no_layouts = 2
status_error_no_rounds = 3

@app.route('/', methods=['GET'])
def home():
    logger.info("Loaded home page")
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/courses', methods=['GET'])
def courses():
    db = Database(os.getenv("db_connection"))
    courses = db.query_courses()
    db.close()
    return jsonify([course.readable_course_name for course in courses])

@app.route('/api/rating/<course_name>', methods=['GET'])
def rating(course_name: str):
    db = Database(os.getenv("db_connection"))
    aggregated_layouts = db.query_aggregate_layouts(course_name)
    db.close()

    # TODO not sure if this is the best way to filter out weird data
    returned_layouts = [x for x in aggregated_layouts if x.num_rounds >= 10]
    num_results = len(returned_layouts)
    logger.info(f"Generated {num_results} layouts for {course_name}")
    
    if num_results == 0:
        return jsonify({
            "status": status_error_no_matches,
            "course_name": course_name,
            "num_results": 0,
            "layouts": []
        }), 200
    
    return jsonify({
        "status": status_success,
        "course_name": course_name,
        "num_results": num_results,
        "layouts": [x.to_dict() for x in returned_layouts]
    }), 200
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 server.py <config_file>")
        sys.exit(1)

    config_file_path = sys.argv[1]
    load_config_into_env(config_file_path)
    if os.getenv("debug") == "True":
        app.run(host='0.0.0.0', port=80)
    else:
        serve(app, host='0.0.0.0', port=80)
