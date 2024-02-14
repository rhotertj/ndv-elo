from datetime import datetime

from sqlalchemy import Engine, and_
from sqlalchemy.orm import Session

# import ..schema
from ..schema import (
    Club,
    Team
)

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
                    session.query(Club).where(Club.name == club).first()
                )
                if not club_obj:
                    club_obj = Club(name=club)
                    session.add(club_obj)
                    session.flush()  # push to db
                    session.refresh(club_obj)  # get ids
                for team in teams:
                    team_obj = (
                        session.query(Team)
                        .where(
                            and_(
                                Team.rank == team,
                                Team.club == club_obj.id,
                            )
                        )
                        .first()
                    )
                    if not team_obj:
                        team_obj = Team(
                            rank=team, club=club_obj.id, year=season.isoformat()
                        )
                        session.add(team_obj)
            except:
                session.rollback()
                raise
            else:
                session.commit()
