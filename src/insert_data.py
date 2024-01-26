import json
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import Engine, and_, create_engine, select, update
from sqlalchemy.orm import Session, aliased

import schema

# TODO: We need to get the name from the HUMAN now and match humans with player identities,
# find all 7 times where we query players and match the name, join humans first
# ALSO, make some atomic functions like get or create and comment functions and querys :)

def reorder_name(player: str):
    """Reorder lastname, name(s) format into name(s) surname.

    Müller, Hans-Joachim Christoph -> Hans-Joachim Christoph Müller.

    Args:
        player (str): Player name.

    Returns:
        str: Player name
    """
    player = player.strip()
    name_split = player.split(",")
    return f"{' '.join([n.strip() for n in name_split[1:]])} {name_split[0]}".strip()


def populate_players(engine: Engine, players: list):
    """Populate the database with players.

    Args:
        engine (Engine): Engine connected to the database.
        players (list): Player list of (id, name, club_name) tuple.

    Raises:
        ValueError: _description_
    """
    with Session(engine) as session:
        session.begin()
        for assoc_id, name, club_name in players:
            name = name.strip()
            try:
                # check if player exists by assoc_id
                club_stmt = select(schema.Club).where(schema.Club.name == club_name)
                club_obj = session.execute(club_stmt).first()
                if not club_obj:
                    raise ValueError(
                        f"Club not found {club_name}. Please create clubs before players."
                    )

                player_obj = (
                    session.query(schema.Player)
                    .where(
                        (schema.Player.name == name)
                        & (schema.Player.club == club_obj[0].id)
                    )
                    .first()
                )

                if not player_obj:
                    # Player not allowed no play
                    if "Spieler ist nicht" in assoc_id:
                        continue
                    # assume unknown player is also not a known human being
                    human_uid = name.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]
                    human_obj = schema.Human(id=human_uid, name=name)
                    player_obj = schema.Player(
                        name=name,
                        human=human_uid,
                        association_id=str(assoc_id),
                        club=club_obj[0].id,
                    )
                    session.add(human_obj)
                    session.add(player_obj)
                else:
                    if player_obj.association_id == "":
                        update_stmt = (
                            update(schema.Player)
                            .where(schema.Player.id == player_obj.id)
                            .values(association_id=str(assoc_id))
                        )
                        session.execute(update_stmt)
            except:
                session.rollback()
                raise
            else:
                session.commit()


def populate_clubs_and_teams(engine: Engine, clubs_and_teams: dict, season: datetime):
    """Populate the database with clubs and their respective team letters.

    Args:
        engine (Engine): Engine connected to the database.
        clubs_and_teams (dict): A dictionary with clubs as keys and teams a values.
    """
    with Session(engine) as session:
        session.begin()
        for club, teams in clubs_and_teams.items():
            try:
                club_obj = (
                    session.query(schema.Club).where(schema.Club.name == club).first()
                )
                if not club_obj:
                    club_obj = schema.Club(name=club)
                    session.add(club_obj)
                    session.flush()  # push to db
                    session.refresh(club_obj)  # get ids
                for team in teams:
                    team_obj = (
                        session.query(schema.Team)
                        .where(
                            and_(
                                schema.Team.rank == team,
                                schema.Team.club == club_obj.id,
                            )
                        )
                        .first()
                    )
                    if not team_obj:
                        team_obj = schema.Team(rank=team, club=club_obj.id, year=season)
                        session.add(team_obj)
            except:
                session.rollback()
                raise
            else:
                session.commit()


def populate_competitions(
    engine: Engine, associations_competitions: dict, season: datetime
):
    """Populate the database with associations and their respective competitions.

    Args:
        engine (Engine): Engine connected to the database.
        associations_competitions (dict): Dictionary with associations as keys and competitions as values.
    """
    with Session(engine) as session:
        session.begin()
        for assoc, comps in associations_competitions.items():
            for comp in comps:
                try:
                    comp_obj = (
                        session.query(schema.Competition)
                        .where(
                            and_(
                                schema.Competition.name == comp,
                                schema.Competition.association == assoc,
                            )
                        )
                        .first()
                    )
                    if not comp_obj:
                        comp_obj = schema.Competition(
                            name=comp, association=assoc, year=season
                        )
                        session.add(comp_obj)
                except:
                    session.rollback()
                    raise
                else:
                    session.commit()


def populate_matches(
    session: Session, matches: list, teammatch_obj: schema.TeamMatch = None
):
    """Parses players and result from match info and creates singles or doubles match. Links to teammatch if provided.

    Args:
        session (Session): Open session to database.
        matches (list): List of match dicts with unparsed player names.
        teammatch_id (int, optional): Database id of teammatch. Defaults to None.
    """
    if matches is None:
        return
    for match in matches:
        doubles = False
        home_player = match["home_player"]
        result = match["result"]
        away_player = match["away_player"]
        match_number = match["match_number"]

        if "/" in home_player:
            doubles = True
            try:
                home_player1, home_player2 = home_player.split("/")
                away_player1, away_player2 = away_player.split("/")
            except Exception:
                print("No valid double", home_player, "vs.", away_player)
                continue

            home_player1 = reorder_name(home_player1)
            home_player2 = reorder_name(home_player2)
            away_player1 = reorder_name(away_player1)
            away_player2 = reorder_name(away_player2)

        # get club of team
        home_team_stmt = select(schema.Team).where(
            teammatch_obj.home_team == schema.Team.id
        )
        home_team = session.execute(home_team_stmt).first()[0]

        away_team_stmt = select(schema.Team).where(
            teammatch_obj.away_team == schema.Team.id
        )
        away_team = session.execute(away_team_stmt).first()[0]

        if not doubles:

            home_player = reorder_name(home_player)
            away_player = reorder_name(away_player)

            home_table = aliased(schema.Player)
            away_table = aliased(schema.Player)

            singles_stmt = (
                select(schema.SinglesMatch)
                .join(home_table, home_table.id == schema.SinglesMatch.home_player)
                .join(away_table, away_table.id == schema.SinglesMatch.away_player)
                .where(
                    and_(
                        away_table.name == away_player,
                        home_table.name == home_player,
                        schema.SinglesMatch.team_match == teammatch_obj.id,
                    )
                )
            )
            singles_obj = session.execute(singles_stmt).first()

            if not singles_obj:
                # Beware name KEIN EINTRAG
                if "KEIN EINTRAG" in (home_player, away_player):
                    print("Skip", home_player, away_player)
                    continue

                home_stmt = select(schema.Player).where(
                    (schema.Player.name == home_player)
                    & (schema.Player.club == home_team.club)
                )
                home_obj = session.execute(home_stmt).first()

                away_stmt = select(schema.Player).where(
                    (schema.Player.name == away_player)
                    & (schema.Player.club == away_team.club)
                )
                away_obj = session.execute(away_stmt).first()

                if not home_obj:
                    # TODO: check for human with that name -> there cannot be one since player only exists with human
                    # create human too
                    human_home_uid = (
                        home_player.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]
                    )
                    human_home_obj = schema.Human(
                        # create uid, name
                        id=human_home_uid,
                        name=home_player,
                    )
                    home_obj = schema.Player(
                        human=human_home_uid, association_id="", club=home_team.club
                    )
                    session.add(human_home_obj)
                    session.add(home_obj)
                    session.flush()
                    session.refresh(home_obj)
                    home_obj = [home_obj]
                if not away_obj:
                    human_away_uid = (
                        away_player.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]
                    )
                    human_away_obj = schema.Human(name=away_player, id=human_away_uid)
                    away_obj = schema.Player(
                        human=human_away_uid, association_id="", club=away_team.club
                    )
                    session.add(human_away_obj)
                    session.add(away_obj)
                    session.flush()
                    session.refresh(away_obj)
                    away_obj = [away_obj]

                match_obj = schema.SinglesMatch(
                    team_match=teammatch_obj.id,
                    home_player=home_obj[0].id,
                    away_player=away_obj[0].id,
                    result=result,
                    match_number=match_number,
                )
                session.add(match_obj)
                session.flush()
                session.refresh(match_obj)
        else:

            home1_table = aliased(schema.Player)
            away1_table = aliased(schema.Player)
            home2_table = aliased(schema.Player)
            away2_table = aliased(schema.Player)

            doubles_stmt = (
                select(schema.DoublesMatch)
                .join(home1_table, home1_table.id == schema.DoublesMatch.home_player1)
                .join(away1_table, away1_table.id == schema.DoublesMatch.away_player1)
                .join(away2_table, away2_table.id == schema.DoublesMatch.away_player2)
                .join(home2_table, home2_table.id == schema.DoublesMatch.home_player2)
                .where(  # lets hope they dont switch around, i dont want to check all combinations
                    and_(
                        home_player1.strip() == home1_table.name,
                        home_team.club == home1_table.club,
                        away_player1.strip() == away1_table.name,
                        away_team.club == away1_table.club,
                        home_player2.strip() == home2_table.name,
                        home_team.club == home2_table.club,
                        away_player2.strip() == away2_table.name,
                        away_team.club == away2_table.club,
                        teammatch_obj.id == schema.DoublesMatch.team_match,
                    )
                )
            )
            doubles_obj = session.execute(doubles_stmt).first()
            if not doubles_obj:
                home1_stmt = select(schema.Player).where(
                    schema.Player.name == home_player1.strip()
                )
                home1_obj = session.execute(home1_stmt).first()

                away1_stmt = select(schema.Player).where(
                    schema.Player.name == away_player1.strip()
                )
                away1_obj = session.execute(away1_stmt).first()

                home2_stmt = select(schema.Player).where(
                    schema.Player.name == home_player2.strip()
                )
                home2_obj = session.execute(home2_stmt).first()

                away2_stmt = select(schema.Player).where(
                    schema.Player.name == away_player2.strip()
                )
                away2_obj = session.execute(away2_stmt).first()

                if not home1_obj:
                    human_home1_uid = (
                        home_player1.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]
                    )
                    human_home1_obj = schema.Human(
                        id=human_home1_uid, name=home_player1
                    )
                    home1_obj = schema.Player(
                        name=home_player1, association_id="", club=home_team.club
                    )
                    session.add(human_home1_obj)
                    session.add(home1_obj)
                    session.flush()
                    session.refresh(home1_obj)
                    home1_obj = [home1_obj]

                if not home2_obj:
                    human_home2_uid = (
                        home_player2.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]
                    )
                    human_home2_obj = schema.Human(
                        id=human_home2_uid, name=home_player2
                    )
                    home2_obj = schema.Player(
                        human=human_home2_obj, association_id="", club=home_team.club
                    )
                    session.add(human_home2_obj)
                    session.add(home2_obj)
                    session.flush()
                    session.refresh(home2_obj)
                    home2_obj = [home2_obj]

                if not away1_obj:
                    human_away1_uid = (
                        away_player1.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]
                    )
                    human_away1_obj = schema.Human(
                        id=human_away1_uid, name=away_player1
                    )
                    away1_obj = schema.Player(
                        human=human_away1_obj, association_id="", club=away_team.club
                    )
                    session.add(human_away1_obj)
                    session.add(away1_obj)
                    session.flush()
                    session.refresh(away1_obj)
                    away1_obj = [away1_obj]

                if not away2_obj:
                    human_away2_uid = (
                        away_player2.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]
                    )
                    human_away2_obj = schema.Human(
                        id=human_away2_uid, name=away_player2
                    )
                    away2_obj = schema.Player(
                        human=human_away2_obj, association_id="", club=away_team.club
                    )
                    session.add(human_away2_obj)
                    away2_obj = schema.Player(
                        name=away_player2, association_id="", club=away_team.club
                    )
                    session.add(away2_obj)
                    session.flush()
                    session.refresh(away2_obj)
                    away2_obj = [away2_obj]

                match_obj = schema.DoublesMatch(
                    team_match=teammatch_obj.id,
                    home_player1=home1_obj[0].id,
                    away_player1=away1_obj[0].id,
                    home_player2=home2_obj[0].id,
                    away_player2=away2_obj[0].id,
                    result=result,
                    match_number=match_number,
                )

                session.add(match_obj)


def populate_teammatches(
    engine: Engine, team_matches: list, matches: list, season: datetime
):
    """Populates the database with teammatches. Also calls function to create respective matches.

    Args:
        engine (Engine): Engine connected to the database.
        team_matches (list): List of team_match dicts containing competition, teams, date and result.
        matches (list): List of matches, matching indices of team matches.
    """
    with Session(engine) as session:
        session.begin()
        for i, match in enumerate(team_matches):
            # get competition id and home team id
            date = datetime.fromisoformat(match["date"])
            try:

                comp_stmt = select(schema.Competition.id).where(
                    and_(
                        schema.Competition.name == match["competition"],
                        schema.Competition.association == match["association"],
                        schema.Competition.year == season,
                    )
                )
                comp_obj = session.execute(comp_stmt).first()

                home_stmt = (
                    select(schema.Team.id)
                    .join(schema.Club)
                    .where(
                        and_(
                            schema.Team.rank == match["home_team"][-1],
                            schema.Club.name == match["home_team"][:-2],
                        )
                    )
                )
                home_obj = session.execute(home_stmt).first()

                away_stmt = (
                    select(schema.Team.id)
                    .join(schema.Club)
                    .where(
                        and_(
                            schema.Team.rank == match["away_team"][-1],
                            schema.Club.name == match["away_team"][:-2],
                        )
                    )
                )
                away_obj = session.execute(away_stmt).first()

                if not all([comp_obj, home_obj, away_obj]):
                    if "Spielfrei" in [match["home_team"], match["away_team"]]:
                        continue
                    print(
                        f"Could not find Competition or team in database {match['competition']} {match['home_team']} {match['away_team']}"
                    )
                    continue

                # try to look for exact teammatch
                stmt = select(schema.TeamMatch).where(
                    and_(
                        schema.TeamMatch.date == date,
                        schema.TeamMatch.home_team == home_obj[0],
                        schema.TeamMatch.away_team == away_obj[0],
                        schema.TeamMatch.competition == comp_obj[0],
                    )
                )
                tm_obj = session.execute(stmt).first()

                if not tm_obj:

                    teammatch_ob = schema.TeamMatch(
                        date=date,
                        competition=comp_obj[0],
                        result=match["result"],
                        home_team=home_obj[0],
                        away_team=away_obj[0],
                    )
                    session.add(teammatch_ob)
                    session.flush()
                    session.refresh(teammatch_ob)
                else:
                    teammatch_ob = tm_obj[0]

                populate_matches(session, matches[i], teammatch_ob)

            except:
                session.rollback()
                raise
            else:
                session.commit()


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Populate the database.")

    parser.add_argument(
        "-db", "--database", help="Path to the database.", required=True
    )
    parser.add_argument(
        "--data",
        help="Path to the data to be inserted. Expecting a json file",
        required=True,
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    engine = create_engine(f"sqlite:///{args.database}")

    with open(data_path, "r") as f:
        crawled_results = json.load(f)
    crawled_results["season"] = datetime.fromisoformat(crawled_results["season"])

    populate_competitions(
        engine,
        crawled_results["crawled_competitions"],
        season=crawled_results["season"],
    )

    for a, competitions in crawled_results["crawled_competitions"].items():
        for c in competitions:
            populate_clubs_and_teams(
                engine,
                crawled_results[a][c]["clubs_teams"],
                season=crawled_results["season"],
            )
            populate_players(engine, crawled_results[a][c]["players"])
            populate_teammatches(
                engine,
                crawled_results[a][c]["team_matches"],
                crawled_results[a][c]["matches"],
                season=crawled_results["season"],
            )
