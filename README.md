# Dart Rankings

This repository contains code for a side project of mine. I crawl publicly available results of darts matches in my 
local area and use them to assign a skill level to all players, similar to the chess ELO system.

I use the TrueSkill system to evaluate a player's performance to get ratings that "converge" with only a handful of matches.
With decent ratings, it is possible to calculate the probability of the outcome of any match.
A short summary of how TrueSkill works can be found [here](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system).

## TODOs

 - Analysis of rankings and distribution of rankings per ligue
 - A MongoDB schema for our relational DB schema
 - A node.js / express frontend that displays leaderboards and probabilities of winning
 - Player badges for streaks and extraordinary accomplishments

## Usage

Crawl data:
```sh
python src/crawler.py --path [PATH] --season 202X --date [YYYY-MM-DD] --associations DBH NDV
```
Create database and populate it :
```sh
python src/data.py --filename [DB_PATH] && \
python src/insert_data.py -db [DB_PATH] --data [DATA_PATH]
```
