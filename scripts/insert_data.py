import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine

sys.path.append(str(Path(".").absolute()))

from src.insert import (
    populate_clubs_and_teams,
    populate_competitions,
    populate_players,
    populate_teammatches,
)

if __name__ == "__main__":
    logging.basicConfig(encoding="utf-8", level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser(description="Populate the database.")

    parser.add_argument(
        "-db", "--database", help="Path to the database.", required=True
    )
    parser.add_argument(
        "--data",
        help="Path to the data to be inserted. Expecting a json file",
        required=True,
        nargs="+",
    )
    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.database}")

    for data_path in args.data:
        data_path = Path(data_path)

        with open(data_path, "r") as f:
            crawled_results = json.load(f)
        crawled_results["season"] = datetime.fromisoformat(crawled_results["season"])

        populate_competitions(
            engine,
            crawled_results["crawled_competitions"],
            season=crawled_results["season"],
        )

        for association, competitions in crawled_results[
            "crawled_competitions"
        ].items():
            for competition in competitions:
                populate_clubs_and_teams(
                    engine,
                    crawled_results[association][competition]["clubs_teams"],
                    season=crawled_results["season"],
                )
                populate_players(
                    engine,
                    crawled_results[association][competition]["players"],
                    association,
                    competition,
                    season=crawled_results["season"],
                )
                populate_teammatches(
                    engine,
                    crawled_results[association][competition]["team_matches"],
                    crawled_results[association][competition]["matches"],
                    season=crawled_results["season"],
                )
