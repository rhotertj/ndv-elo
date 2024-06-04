import logging
from datetime import datetime

from sqlalchemy import Engine, and_, select
from sqlalchemy.orm import Session, aliased

from ..schema import (
    Club,
    Competition,
    DoublesMatch,
    Human,
    Player,
    SinglesMatch,
    Team,
    TeamMatch,
)
from .player import get_player_or_create_player_and_human, reorder_name

# TODO: Separate functions for creating a singles or doubles match, orchestrate by populate_matches


def populate_matches(session: Session, matches: list, teammatch_obj: TeamMatch = None):
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
        home_team_stmt = select(Team).where(teammatch_obj.home_team == Team.id)
        home_team = session.execute(home_team_stmt).first()[0]
        logging.debug(f"Found home team {home_team}")

        away_team_stmt = select(Team).where(teammatch_obj.away_team == Team.id)
        away_team = session.execute(away_team_stmt).first()[0]
        logging.debug(f"Found away team {away_team}")

        if not doubles:
            # TODO: We need to get player from human table by name first but also filter by club to ensure
            # not to walk into the unlikely case that two identically named humans played at the same time

            home_player = reorder_name(home_player)
            away_player = reorder_name(away_player)

            home_table = aliased(Player)
            home_human_table = aliased(Human)

            away_table = aliased(Player)
            away_human_table = aliased(Human)

            singles_stmt = (
                select(SinglesMatch)
                .join(home_table, home_table.id == SinglesMatch.home_player)
                .join(home_human_table, home_table.human == home_human_table.id)
                .join(away_table, away_table.id == SinglesMatch.away_player)
                .join(away_human_table, away_table.human == away_human_table.id)
                .where(
                    and_(
                        home_human_table.name == home_player,
                        away_human_table.name == away_player,
                        SinglesMatch.team_match == teammatch_obj.id,
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

                match_obj = SinglesMatch(
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

            home1_table = aliased(Player)
            home1_human_table = aliased(Human)
            away1_table = aliased(Player)
            away1_human_table = aliased(Human)
            home2_table = aliased(Player)
            home2_human_table = aliased(Human)
            away2_table = aliased(Player)
            away2_human_table = aliased(Human)

            doubles_stmt = (
                select(DoublesMatch)
                .join(home1_table, home1_table.id == DoublesMatch.home_player1)
                .join(home1_human_table, home1_table.human == home1_human_table.id)
                .join(away1_table, away1_table.id == DoublesMatch.away_player1)
                .join(away1_human_table, away1_table.human == away1_human_table.id)
                .join(home2_table, home2_table.id == DoublesMatch.home_player2)
                .join(home2_human_table, home2_table.human == home2_human_table.id)
                .join(away2_table, away2_table.id == DoublesMatch.away_player2)
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
                        teammatch_obj.id == DoublesMatch.team_match,
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

                match_obj = DoublesMatch(
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
                comp_stmt = select(Competition.id).where(
                    and_(
                        Competition.name == match["competition"],
                        Competition.association == match["association"],
                        Competition.year == season.isoformat(),
                    )
                )
                comp_obj = session.execute(comp_stmt).first()
                logging.debug(f"Found competition: {comp_obj}")

                home_team_name = match["home_team"].replace("(Jgd.)", "").strip()
                away_team_name = match["away_team"].replace("(Jgd.)", "").strip()

                home_stmt = (
                    select(Team.id)
                    .join(Club)
                    .where(
                        and_(
                            Team.rank == home_team_name[-1],
                            Club.name == home_team_name[:-2],
                            Team.year == season.isoformat(),
                        )
                    )
                )
                home_obj = session.execute(home_stmt).first()
                logging.debug(f"Found home team {home_obj}")

                away_stmt = (
                    select(Team.id)
                    .join(Club)
                    .where(
                        and_(
                            Team.rank == away_team_name[-1],
                            Club.name == away_team_name[:-2],
                            Team.year == season.isoformat(),
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
                stmt = select(TeamMatch).where(
                    and_(
                        TeamMatch.date == date.isoformat(),
                        TeamMatch.home_team == home_obj[0],
                        TeamMatch.away_team == away_obj[0],
                        TeamMatch.competition == comp_obj[0],
                    )
                )
                tm_obj = session.execute(stmt).first()
                logging.debug(f"Found already existing teammatch {tm_obj}")

                if not tm_obj:
                    teammatch_ob = TeamMatch(
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
