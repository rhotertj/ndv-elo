import json
import pickle
import os
from datetime import datetime

def dict_to_json(d: dict):
    d = json.dumps(d)
    jd = json.loads(d)
    return jd

def main():
    with open("/home/jim/Code/ndv-elo/data/assocs_comps.pkl", "rb") as f:
        assocs_comps = pickle.load(f)
    with open("/home/jim/Code/ndv-elo/data/players_DBH_DBH Bezirksliga 2.pkl", "rb") as f:
        players = pickle.load(f)
    with open("/home/jim/Code/ndv-elo/data/teamsclubs_DBH_DBH Bezirksliga 2.pkl", "rb") as f:
        teamsclubs = pickle.load(f)
    with open("/home/jim/Code/ndv-elo/data/matches_DBH_DBH Bezirksliga 2.pkl", "rb") as f:
        matches = pickle.load(f)
    with open("/home/jim/Code/ndv-elo/data/matchdays_DBH_DBH Bezirksliga 2.pkl", "rb") as f:
        matchdays = pickle.load(f)

    #print(dict_to_json(assocs_comps)) # {association : [competitions]}

    #print(dict_to_json(players)) #[[ID, Name, Club]...]
    def save_as_json(
            path : str,
            crawled_date : datetime,
            from_date: datetime,
            crawled_competitions : dict,
            clubs_teams: dict,
            players: dict,
            team_matches: dict,
            matches: dict 
    ):
        result = {}
        result["crawled_date"] = crawled_date.isoformat()
        result["from_date"] = from_date.isoformat()
        result["crawled_competitions"] = {"DBH" : ["DBH Bezirksliga 2"]}
        for a, cs in result["crawled_competitions"].items():
            for c in cs:
                result[a] = {c:{}}
                result[a][c]["clubs_teams"] = {club : list(teams) for club, teams in clubs_teams.items()}
                result[a][c]["matches"] = matches
                result[a][c]["players"] = players
                for match in team_matches:
                    match["date"] = match["date"].isoformat()
                result[a][c]["team_matches"] = team_matches

        with open(path, "w+") as f:
            json.dump(result, f)

    save_as_json(
        path="dbh_bzl2.json",
        crawled_date=datetime(2023, 1, 1),
        from_date=datetime(2022, 8, 1),
        crawled_competitions=assocs_comps,
        clubs_teams=teamsclubs,
        players=players,
        team_matches=matchdays,
        matches=matches
    )

    #print(dict_to_json(matches)) # list of lists, each inner list corresponds to a matchday and holds matches
    # matches are {home_player, away_player, result}


    #for match in matchdays:
    #    match["date"] = match["date"].isoformat()
    
    #print(dict_to_json(matchdays)) # [{date, home_team, away_team, result, legs, competition, association}]

if __name__ == "__main__":
    main()
    with open("dbh_bzl2.json", "r") as f:
        result = json.load(f)
    print(result)

    # new format: json, note that dates are isoformat strings
    # crawled_at: date
    # from_date: date
    # crawled_comptetitions: assocs_comps
    # clubs_teams: clubs_teams
    # players: players
    # team_matches: matchdays
    # matches: matches 