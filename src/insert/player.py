import logging
import uuid
from datetime import datetime

from sqlalchemy import Engine, and_, select, update
from sqlalchemy.orm import Session

from ..schema import Club, Team, Human, Player, Competition


def create_human_id(name):
    return name.replace(" ", "").lower()[:8] + uuid.uuid4().hex[:8]


def get_player_or_create_player_and_human(
    session: Session,
    name: str,
    club_id: int,
    team: int = None,
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
        select(Player)
        .join(Human, Human.id == Player.human)
        .where(and_(Human.name == name, Player.club == club_id))
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
        human_obj = Human(id=human_uid, name=name)
        if association_id is None:
            association_id = ""
        player_obj = Player(
            human=human_uid,
            association_id=str(association_id),
            club=club_id,
            team=team,
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
            update(Player)
            .where(Player.id == player_obj.id)
            .values(association_id=str(association_id))
        )
        session.execute(update_stmt)

    # TODO Check for Team date, maybe update team
    if player_obj.team is None and team is not None:
        update_stmt = (
            update(Player)
            .where(Player.id == player_obj.id)
            .values(team=team)
        )
        session.execute(update_stmt)
    return player_obj


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
        comp_stmt = select(Competition).where(
            and_(
                Competition.association == association,
                Competition.name == competition,
                Competition.year == season.isoformat(),
            )
        )
        comp_obj = session.execute(comp_stmt).first()
        if not comp_obj:
            raise ValueError(
                f"Could not find default competition {association} {competition} for players!"
            )
        # TODO Player gets team instead of competition
        for assoc_id, name, club_name, team_rank in players:
            name = name.strip()
            try:
                # Find club first to search player after name within club
                # Assumption: No name collisions within clubs
                club_stmt = select(Club).where(Club.name == club_name)
                club_obj = session.execute(club_stmt).first()
                if not club_obj:
                    raise ValueError(
                        f"Club not found {club_name}. Please create clubs before players."
                    )

                team_stmt = select(Team).where(
                    and_(
                        Team.rank == team_rank,
                        Team.club == club_obj[0].id,
                        Team.year == season.isoformat(),
                        Team.competition == comp_obj[0].id
                    )
                )
                team_obj = session.execute(team_stmt).first()
                if team_obj is None:
                    raise ValueError(
                        f"Team not found {club_name, team_rank}. Please create clubs before players."
                    )


                get_player_or_create_player_and_human(
                    session,
                    name,
                    club_obj[0].id,
                    team=team_obj[0].id,
                    association_id=assoc_id,
                )
            except:
                session.rollback()
                raise
            else:
                session.commit()
