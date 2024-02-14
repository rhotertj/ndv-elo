import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import Engine, and_, create_engine, select, update
from sqlalchemy.orm import Session, aliased

import schema


def create_human_id(name):
    return name.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]


def get_player_or_create_player_and_human(
    session: Session,
    name: str,
    club_id: int,
    default_competition: int = None,
    association_id=None,
    flush_after_add=False,
):
    """Get a player by club_id and his name. Name will be matched by human object.
    If a player exists without given association id, it is updated.
    If a player does not exists, he and an accompanying human object are created.

    NOTE: Session commits and rollbacks need to be done outside this function!
    Args:
        session (Session): The current db session.
        name (str): Player name
        club_id (int): The id for the club. For doubles, more than one can be given. The first one is used for creation.
        association_id (Union[str,None], optional): The player number within the association. Defaults to None.
    """
    stmt = (
        select(schema.Player)
        .join(schema.Human, schema.Human.id == schema.Player.human)
        .where(and_(schema.Human.name == name, schema.Player.club == club_id))
    )
    player_obj = session.execute(stmt).first()

    if player_obj is None:
        if association_id is not None and "Spieler ist nicht" in association_id:
            logging.info(f"Skip Player {name=} with association_id {association_id=}")
            return
        if name == "---":
            logging.info(
                f"Skip Player {name=} ({club_id=}) with association_id {association_id=}"
            )
            return
        human_uid = create_human_id(name)
        human_obj = schema.Human(id=human_uid, name=name)
        if association_id is None:
            association_id = ""
        player_obj = schema.Player(
            human=human_uid,
            association_id=str(association_id),
            club=club_id,
            default_competition=default_competition,
        )
        session.add(human_obj)
        session.add(player_obj)
        if flush_after_add:
            session.flush()
            session.refresh(player_obj)
    else:
        player_obj = player_obj[0]

    if player_obj.association_id == "" and association_id is not None:
        update_stmt = (
            update(schema.Player)
            .where(schema.Player.id == player_obj.id)
            .values(association_id=str(association_id))
        )
        session.execute(update_stmt)
    return player_obj


# def get_or_create_singles(teammatch: schema.TeamMatch, home_player_name: str, away_player_name: str, result: str):


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


def populate_players(
    engine: Engine, players: list, association: str, competition: str, season: datetime
):
    """Populate the database with players.

    Args:
        engine (Engine): Engine connected to the database.
        players (list): Player list of (id, name, club_name) tuple.

    Raises:
        ValueError: _description_
    """
    with Session(engine) as session:
        session.begin()
        comp_stmt = select(schema.Competition).where(
            and_(
                schema.Competition.association == association,
                schema.Competition.name == competition,
                schema.Competition.year == season.isoformat(),
            )
        )
        comp_obj = session.execute(comp_stmt).first()
        if not comp_obj:
            raise ValueError(
                f"Could not find default competition {association} {competition} for players!"
            )
        for assoc_id, name, club_name in players:
            name = name.strip()
            try:
                # Find club first to search player after name within club
                # Assumption: No name collisions within clubs
                club_stmt = select(schema.Club).where(schema.Club.name == club_name)
                club_obj = session.execute(club_stmt).first()
                if not club_obj:
                    raise ValueError(
                        f"Club not found {club_name}. Please create clubs before players."
                    )

                get_player_or_create_player_and_human(
                    session,
                    name,
                    club_obj[0].id,
                    default_competition=comp_obj[0].id,
                    association_id=assoc_id,
                )
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
                        team_obj = schema.Team(
                            rank=team, club=club_obj.id, year=season.isoformat()
                        )
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
                if assoc in comp:
                    comp.replace("assoc").strip()
                try:
                    comp_obj = (
                        session.query(schema.Competition)
                        .where(
                            and_(
                                schema.Competition.name == comp,
                                schema.Competition.association == assoc,
                                schema.Competition.year == season.isoformat(),
                            )
                        )
                        .first()
                    )
                    if not comp_obj:
                        comp_obj = schema.Competition(
                            name=comp, association=assoc, year=season.isoformat()
                        )
                        session.add(comp_obj)
                        logging.info(f"Added {assoc} {comp}")
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
        logging.debug(f"Processing match {match}")
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
                logging.info(f"No valid double: {home_player} vs {away_player}")
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
        logging.debug(f"Found home team {home_team}")

        away_team_stmt = select(schema.Team).where(
            teammatch_obj.away_team == schema.Team.id
        )
        away_team = session.execute(away_team_stmt).first()[0]
        logging.debug(f"Found away team {away_team}")

        if not doubles:
            # TODO: We need to get player from human table by name first but also filter by club to ensure
            # not to walk into the unlikely case that two identically named humans played at the same time

            home_player = reorder_name(home_player)
            away_player = reorder_name(away_player)

            home_table = aliased(schema.Player)
            home_human_table = aliased(schema.Human)

            away_table = aliased(schema.Player)
            away_human_table = aliased(schema.Human)

            singles_stmt = (
                select(schema.SinglesMatch)
                .join(home_table, home_table.id == schema.SinglesMatch.home_player)
                .join(home_human_table, home_table.human == home_human_table.id)
                .join(away_table, away_table.id == schema.SinglesMatch.away_player)
                .join(away_human_table, away_table.human == away_human_table.id)
                .where(
                    and_(
                        home_human_table.name == home_player,
                        away_human_table.name == away_player,
                        schema.SinglesMatch.team_match == teammatch_obj.id,
                    )
                )
            )
            singles_obj = session.execute(singles_stmt).first()
            logging.debug(f"Found existing singles match {singles_obj} for {match}")

            if not singles_obj:
                logging.debug(f"Could not find existing singles match {singles_obj}")
                if "KEIN EINTRAG" in (home_player, away_player):
                    logging.info(f"Skip match {home_player} vs {away_player}")
                    continue

                home_obj = get_player_or_create_player_and_human(
                    session=session,
                    name=home_player,
                    club_id=home_team.club,
                    flush_after_add=True,
                )

                away_obj = get_player_or_create_player_and_human(
                    session=session,
                    name=away_player,
                    club_id=away_team.club,
                    flush_after_add=True,
                )

                if None in [home_obj, away_obj]:
                    logging.info(
                        f"Skipping match because we could not get or create on of {[home_obj, away_obj]}"
                    )
                    continue

                match_obj = schema.SinglesMatch(
                    team_match=teammatch_obj.id,
                    home_player=home_obj.id,
                    away_player=away_obj.id,
                    result=result,
                    match_number=match_number,
                )
                session.add(match_obj)
                session.flush()
                session.refresh(match_obj)
        else:

            home1_table = aliased(schema.Player)
            home1_human_table = aliased(schema.Human)
            away1_table = aliased(schema.Player)
            away1_human_table = aliased(schema.Human)
            home2_table = aliased(schema.Player)
            home2_human_table = aliased(schema.Human)
            away2_table = aliased(schema.Player)
            away2_human_table = aliased(schema.Human)

            doubles_stmt = (
                select(schema.DoublesMatch)
                .join(home1_table, home1_table.id == schema.DoublesMatch.home_player1)
                .join(home1_human_table, home1_table.human == home1_human_table.id)
                .join(away1_table, away1_table.id == schema.DoublesMatch.away_player1)
                .join(away1_human_table, away1_table.human == away1_human_table.id)
                .join(home2_table, home2_table.id == schema.DoublesMatch.home_player2)
                .join(home2_human_table, home2_table.human == home2_human_table.id)
                .join(away2_table, away2_table.id == schema.DoublesMatch.away_player2)
                .join(away2_human_table, away2_table.human == away2_human_table.id)
                .where(
                    and_(
                        home_player1 == home1_human_table.name,
                        home_team.club == home1_table.club,
                        away_player1 == away1_human_table.name,
                        away_team.club == away1_table.club,
                        home_player2 == home2_human_table.name,
                        home_team.club == home2_table.club,
                        away_player2 == away2_human_table.name,
                        away_team.club == away2_table.club,
                        teammatch_obj.id == schema.DoublesMatch.team_match,
                    )
                )
            )
            doubles_obj = session.execute(doubles_stmt).first()
            if not doubles_obj:

                home1_obj = get_player_or_create_player_and_human(
                    session=session,
                    name=home_player1.strip(),
                    club_id=home_team.club,
                    flush_after_add=True,
                )

                home2_obj = get_player_or_create_player_and_human(
                    session=session,
                    name=home_player2.strip(),
                    club_id=home_team.club,
                    flush_after_add=True,
                )

                away1_obj = get_player_or_create_player_and_human(
                    session=session,
                    name=away_player1.strip(),
                    club_id=away_team.club,
                    flush_after_add=True,
                )

                away2_obj = get_player_or_create_player_and_human(
                    session=session,
                    name=away_player2.strip(),
                    club_id=away_team.club,
                    flush_after_add=True,
                )

                if None in (home1_obj, home2_obj, away1_obj, away2_obj):
                    continue

                match_obj = schema.DoublesMatch(
                    team_match=teammatch_obj.id,
                    home_player1=home1_obj.id,
                    away_player1=away1_obj.id,
                    home_player2=home2_obj.id,
                    away_player2=away2_obj.id,
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
    logging.debug("Start populating team matches")
    with Session(engine) as session:
        session.begin()
        for i, match in enumerate(team_matches):
            # get competition id and home team id
            date = datetime.fromisoformat(match["date"])
            logging.debug(f"--Match to be inserted: {match}")
            try:
                comp_stmt = select(schema.Competition.id).where(
                    and_(
                        schema.Competition.name == match["competition"],
                        schema.Competition.association == match["association"],
                        schema.Competition.year == season.isoformat(),
                    )
                )
                comp_obj = session.execute(comp_stmt).first()
                logging.debug(f"Found competition: {comp_obj}")

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
                logging.debug(f"Found home team {home_obj}")

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
                logging.debug(f"Found away team {away_obj}")

                if not all([comp_obj, home_obj, away_obj]):
                    if "Spielfrei" in [match["home_team"], match["away_team"]]:
                        continue
                    logging.info(
                        f"Could not find Competition or team in database {match['association']} {match['competition']} {season} {match['home_team']} {match['away_team']}"
                    )
                    logging.info(f"{comp_obj, home_obj, away_obj}")
                    continue

                # try to look for exact teammatch
                stmt = select(schema.TeamMatch).where(
                    and_(
                        schema.TeamMatch.date == date.isoformat(),
                        schema.TeamMatch.home_team == home_obj[0],
                        schema.TeamMatch.away_team == away_obj[0],
                        schema.TeamMatch.competition == comp_obj[0],
                    )
                )
                tm_obj = session.execute(stmt).first()
                logging.debug(f"Found already existing teammatch {tm_obj}")

                if not tm_obj:
                    teammatch_ob = schema.TeamMatch(
                        date=date.isoformat(),
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
                    logging.debug(f"Populate matches for {teammatch_ob}")

                populate_matches(session, matches[i], teammatch_ob)

            except:
                session.rollback()
                raise
            else:
                session.commit()


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

        for a, competitions in crawled_results["crawled_competitions"].items():
            for c in competitions:
                populate_clubs_and_teams(
                    engine,
                    crawled_results[a][c]["clubs_teams"],
                    season=crawled_results["season"],
                )
                populate_players(
                    engine,
                    crawled_results[a][c]["players"],
                    a,
                    c,
                    season=crawled_results["season"],
                )
                populate_teammatches(
                    engine,
                    crawled_results[a][c]["team_matches"],
                    crawled_results[a][c]["matches"],
                    season=crawled_results["season"],
                )
