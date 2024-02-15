import logging
import sys
from pathlib import Path

import sqlalchemy

sys.path.append(str(Path(".").absolute()))
from src.rating import compute_ratings

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate the database.")
    logging.basicConfig(encoding="utf-8", level=logging.INFO)

    parser.add_argument(
        "-db", "--database", help="Path to the database.", required=True
    )

    args = parser.parse_args()
    engine = sqlalchemy.create_engine(f"sqlite:///{args.database}")

    compute_ratings(engine)
