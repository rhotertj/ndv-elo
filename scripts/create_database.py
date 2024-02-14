import sys
from pathlib import Path

sys.path.append(str(Path(".").absolute()))
import sqlalchemy

from src.schema import Base

if "__main__" == __name__:
    import argparse

    parser = argparse.ArgumentParser(description="Create a new database")

    parser.add_argument("--filename", required=True, help="Path to the database to be created.")
    args = parser.parse_args()

    fn = args.filename

    engine = sqlalchemy.create_engine(f"sqlite:///{fn}")
    Base.metadata.create_all(engine)
