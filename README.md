# Dart Rankings

This repository contains code for a side project of mine. I crawl publicly available results of darts matches in my
local area and use them to assign a skill level to all players, similar to the chess ELO system.

I use the TrueSkill system to evaluate a player's performance to get ratings that "converge" with only a handful of matches.
With decent ratings, it is possible to calculate the probability of the outcome of any match.
A short summary of how TrueSkill works can be found [here](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system).

## TODOs

- Currently building a node.js/express app to display leaderboards
- Analysis of rankings and distribution of rankings per ligue
- Player badges for streaks and extraordinary accomplishments

## Usage

Crawl data:
Start selenium in docker:

```sh
docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" -e SE_NODE_MAX_SESSIONS=3 selenium/standalone-firefox:4.17.0-20240123
```

Then execute the script to crawl concurrently:

```sh
python scripts/crawl_concurrent.py --path [PATH] --season 202X --date [YYYY-MM-DD] --associations DBH NDV
```

Create database and populate it :

```sh
python src/schema.py --filename [DB_PATH] && \
python src/insert_data.py -db [DB_PATH] --data [DATA_PATH]
```

Beware: Powershell does not handle wildcards, pass data as `--data $(ls .\data\2023\*55.json | % {$_.FullName}) `
