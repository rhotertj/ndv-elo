import json
import sys
from datetime import datetime

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

sys.path.append("S:/Dokumente/Code/ndv-elo/src")
import os

import schema
from insert_data import (
    populate_clubs_and_teams,
    populate_competitions,
    populate_players,
    populate_teammatches,
)

DB_PATH = "test.db"
DB_URL = f"sqlite:///{DB_PATH}"
TEST_DATA_PATH = "./test/testdata.json"

with open(TEST_DATA_PATH, "r") as f:
    TEST_DATA = json.load(f)
    TEST_DATA["season"] = datetime.fromisoformat(TEST_DATA["season"])


@pytest.fixture(scope="session")
def db_engine():
    os.remove(DB_PATH)
    from schema import Base

    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    return engine


def test_duplicate_insert_clubs(db_engine):
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Club)
        result = session.execute(stmt)
        n_clubs_0 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_clubs_0 == 0
    populate_clubs_and_teams(
        db_engine, TEST_DATA["DBH"]["Kreisliga 5"]["clubs_teams"], TEST_DATA["season"]
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Club)
        result = session.execute(stmt)
        n_clubs_1 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_clubs_1 == len(TEST_DATA["DBH"]["Kreisliga 5"]["clubs_teams"])
    populate_clubs_and_teams(
        db_engine, TEST_DATA["DBH"]["Kreisliga 5"]["clubs_teams"], TEST_DATA["season"]
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Club)
        result = session.execute(stmt)
        n_clubs_2 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_clubs_1 == n_clubs_2


def test_duplicate_insert_players(db_engine):
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Player)
        result = session.execute(stmt)
        n_players_0 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_players_0 == 0
    populate_players(db_engine, TEST_DATA["DBH"]["Kreisliga 5"]["players"])
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Player)
        result = session.execute(stmt)
        n_players_1 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_players_1 == len(TEST_DATA["DBH"]["Kreisliga 5"]["players"])
    populate_players(db_engine, TEST_DATA["DBH"]["Kreisliga 5"]["players"])
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Player)
        result = session.execute(stmt)
        n_players_2 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_players_1 == n_players_2


def test_duplicate_insert_competitions(db_engine):
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Competition)
        result = session.execute(stmt)
        n_comps_0 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_comps_0 == 0
    populate_competitions(
        db_engine, TEST_DATA["crawled_competitions"], TEST_DATA["season"]
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Competition)
        result = session.execute(stmt)
        n_comps_1 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_comps_1 == len(TEST_DATA["crawled_competitions"])
    populate_competitions(
        db_engine, TEST_DATA["crawled_competitions"], TEST_DATA["season"]
    )
    with Session(db_engine) as session:
        stmt = select(func.count()).select_from(schema.Competition)
        result = session.execute(stmt)
        n_comps_2 = result.scalar()
    # trunk-ignore(bandit/B101)
    assert n_comps_1 == n_comps_2


def test_duplicate_insert_teammatches(db_engine):
    with Session(db_engine) as session:
        stmt_double = select(func.count()).select_from(schema.DoublesMatch)
        result_double = session.execute(stmt_double)
        n_double_0 = result_double.scalar()

        stmt_single = select(func.count()).select_from(schema.SinglesMatch)
        result_single = session.execute(stmt_single)
        n_single_0 = result_single.scalar()

        stmt_teammatch = select(func.count()).select_from(schema.TeamMatch)
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
        TEST_DATA["DBH"]["Kreisliga 5"]["team_matches"],
        TEST_DATA["DBH"]["Kreisliga 5"]["matches"],
        season=TEST_DATA["season"],
    )
    with Session(db_engine) as session:
        stmt_double = select(func.count()).select_from(schema.DoublesMatch)
        result_double = session.execute(stmt_double)
        n_double_1 = result_double.scalar()

        stmt_single = select(func.count()).select_from(schema.SinglesMatch)
        result_single = session.execute(stmt_single)
        n_single_1 = result_single.scalar()

        stmt_teammatch = select(func.count()).select_from(schema.TeamMatch)
        result_teammatch = session.execute(stmt_teammatch)
        n_teammatch_1 = result_teammatch.scalar()
    # trunk-ignore(bandit/B101)
    assert n_teammatch_1 == len(TEST_DATA["DBH"]["Kreisliga 5"]["team_matches"])

    n_matches = sum([len(m) for m in TEST_DATA["DBH"]["Kreisliga 5"]["matches"]])
    # trunk-ignore(bandit/B101)
    assert n_double_1 + n_single_1  == n_matches - 1 # corrupted data has one duplicate match
    populate_teammatches(
        db_engine,
        TEST_DATA["DBH"]["Kreisliga 5"]["team_matches"],
        TEST_DATA["DBH"]["Kreisliga 5"]["matches"],
        season=TEST_DATA["season"],
    )
    with Session(db_engine) as session:
        stmt_double = select(func.count()).select_from(schema.DoublesMatch)
        result_double = session.execute(stmt_double)
        n_double_2 = result_double.scalar()

        stmt_single = select(func.count()).select_from(schema.SinglesMatch)
        result_single = session.execute(stmt_single)
        n_single_2 = result_single.scalar()

        stmt_teammatch = select(func.count()).select_from(schema.TeamMatch)
        result_teammatch = session.execute(stmt_teammatch)
        n_teammatch_2 = result_teammatch.scalar()
    # trunk-ignore(bandit/B101)
    assert n_teammatch_2 == n_teammatch_1

    n_matches = sum([len(m) for m in TEST_DATA["DBH"]["Kreisliga 5"]["matches"]])
    # trunk-ignore(bandit/B101)
    assert n_double_1 + n_single_1 == n_double_2 + n_single_2
