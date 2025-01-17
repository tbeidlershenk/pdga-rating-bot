# HotRound

![Uptime Robot status](https://img.shields.io/uptimerobot/status/m798326084-f2659ca54689c996a957c4f5?up_message=online&down_message=offline&style=flat-square&link=https://stats.uptimerobot.com/IvJUZPjdWN)

**HotRound** aggregates PDGA sanctioned tournament data to calculate accurate disc golf round ratings for casual, non-sanctioned rounds.

**[hotround.site](https://hotround.site)** • **[Discord Bot](https://discord.com/oauth2/authorize?client_id=1300645264591294475)**

### How it works

The tool uses a database of `~10,000` courses, `~20,000` tournaments, `~300,000` rounds to generate ratings for any arbitrary course and tee/basket layout.

PDGALive layouts often differ by small amounts from tournament to tournament, with different names and pin-positions. HotRound groups layouts by similarity metrics, such as `distance` and `par` of each hole using a fuzzy-matching algorithm.

### Example Usage

![Website example](./assets/website_1.png)

### Built using

The frontend site is built using the `Flask` web framework to serve a `ReactJS` application. The discord bot is built using the `Disnake` python library. The dataset used by the project was scraped using `Selenium` and stored in a `SQLite` database. Applications are then deployed using `Docker` and `Heroku`.

[![My Skills](https://skillicons.dev/icons?i=python,flask,react,selenium,sqlite,heroku,docker)](https://skillicons.dev)

### Contributing

Contact me at tbeidlershenk@gmail.com if you have ideas / feedback or are interested in contributing! I am looking to continue developing this project and potentially working with other devs.

### Credits

The data used in this project was sourced through web scraping from [PDGALive](https://pdga.com/live) and is not being used for commercial purposes.
