import json
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

sys.path.append("S:/Dokumente/Code/ndv-elo/src")
# Linux parent directory
sys.path.append(str(Path(".").absolute()))
import os

from src.insert import (
    populate_clubs_and_teams,
    populate_competitions,
    populate_players,
    populate_teammatches,
)
from src.schema import (
    Base,
    Club,
    Competition,
    DoublesMatch,
    Player,
    SinglesMatch,
    TeamMatch,
)

DB_PATH = "test.db"
DB_URL = f"sqlite:///{DB_PATH}"
TEST_DATA_PATH = "./test/testdata.json"
competition = "Kreisliga 5"
association = "DBH"

with open(TEST_DATA_PATH, "r") as f:
    data = json.load(f)
    data["season"] = datetime.fromisoformat(data["season"])


@pytest.fixture(scope="session")
def db_engine():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    return engine

def test_duplicate_insert_competitions(db_engine):
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Competition)
        result = session.execute(stmt)
        n_comps_0 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_comps_0 == 0
    populate_competitions(db_engine, data["crawled_competitions"], data["season"])
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Competition)
        result = session.execute(stmt)
        n_comps_1 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_comps_1 == len(data["crawled_competitions"])
    populate_competitions(db_engine, data["crawled_competitions"], data["season"])
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Competition)
        result = session.execute(stmt)
        n_comps_2 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_comps_1 == n_comps_2

def test_duplicate_insert_clubs(db_engine):
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Club)
        result = session.execute(stmt)
        n_clubs_0 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_clubs_0 == 0
    populate_clubs_and_teams(
        db_engine,
        data[association][competition]["clubs_teams"],
        competition=competition,
        association=association,
        season=data["season"],
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Club)
        result = session.execute(stmt)
        n_clubs_1 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_clubs_1 == len(data[association][competition]["clubs_teams"])
    populate_clubs_and_teams(
        db_engine,
        data[association][competition]["clubs_teams"],
        competition=competition,
        association=association,
        season=data["season"],
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Club)
        result = session.execute(stmt)
        n_clubs_2 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_clubs_1 == n_clubs_2




def test_duplicate_insert_players(db_engine):
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Player)
        result = session.execute(stmt)
        n_players_0 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_players_0 == 0
    populate_players(
        db_engine,
        data[association][competition]["players"],
        association=association,
        competition=competition,
        season=data["season"],
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Player)
        result = session.execute(stmt)
        n_players_1 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_players_1 == len(data[association][competition]["players"])
    populate_players(
        db_engine,
        data[association][competition]["players"],
        association=association,
        competition=competition,
        season=data["season"],
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(Player)
        result = session.execute(stmt)
        n_players_2 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_players_1 == n_players_2


def test_duplicate_insert_teammatches(db_engine):
    with Session(db_engine) as session:
        stmt_double = select(func.count()).select_from(DoublesMatch)
        result_double = session.execute(stmt_double)
        n_double_0 = result_double.scalar()

        stmt_single = select(func.count()).select_from(SinglesMatch)
        result_single = session.execute(stmt_single)
        n_single_0 = result_single.scalar()

        stmt_teammatch = select(func.count()).select_from(TeamMatch)
        result_teammatch = session.execute(stmt_teammatch)
        n_teammatch_0 = result_teammatch.scalar()
    # trunk-ignore(bandit/B101)
    assert n_double_0 == 0
    # trunk-ignore(bandit/B101)
    assert n_single_0 == 0
    # trunk-ignore(bandit/B101)
    assert n_teammatch_0 == 0
    populate_teammatches(
        db_engine,
        data[association][competition]["team_matches"],
        data[association][competition]["matches"],
        season=data["season"],
    )
    with Session(db_engine) as session:
        stmt_double = select(func.count()).select_from(DoublesMatch)
        result_double = session.execute(stmt_double)
        n_double_1 = result_double.scalar()

        stmt_single = select(func.count()).select_from(SinglesMatch)
        result_single = session.execute(stmt_single)
        n_single_1 = result_single.scalar()

        stmt_teammatch = select(func.count()).select_from(TeamMatch)
        result_teammatch = session.execute(stmt_teammatch)
        n_teammatch_1 = result_teammatch.scalar()
    # trunk-ignore(bandit/B101)
    assert n_teammatch_1 == len(data[association][competition]["team_matches"])

    n_matches = sum([len(m) for m in data[association][competition]["matches"]])
    # trunk-ignore(bandit/B101)
    assert (
        n_double_1 + n_single_1 == n_matches - 4
    )  # corrupted data has one duplicate match
    populate_teammatches(
        db_engine,
        data[association][competition]["team_matches"],
        data[association][competition]["matches"],
        season=data["season"],
    )
    with Session(db_engine) as session:
        stmt_double = select(func.count()).select_from(DoublesMatch)
        result_double = session.execute(stmt_double)
        n_double_2 = result_double.scalar()

        stmt_single = select(func.count()).select_from(SinglesMatch)
        result_single = session.execute(stmt_single)
        n_single_2 = result_single.scalar()

        stmt_teammatch = select(func.count()).select_from(TeamMatch)
        result_teammatch = session.execute(stmt_teammatch)
        n_teammatch_2 = result_teammatch.scalar()
    # trunk-ignore(bandit/B101)
    assert n_teammatch_2 == n_teammatch_1

    n_matches = sum([len(m) for m in data[association][competition]["matches"]])
    # trunk-ignore(bandit/B101)
    assert n_double_1 + n_single_1 == n_double_2 + n_single_2
