from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Human(Base):

    __tablename__ = "human_table"

    id = Column(String, unique=True, primary_key=True)
    name = Column(String)

    # other stuff may follow
    # global rating?
    def __repr__(self) -> str:
        return f"Human {self.id=} {self.name=}"


class Player(Base):

    __tablename__ = "player_table"

    id = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    human = Column(String, ForeignKey("human_table.id"), index=True)
    club = Column(Integer, ForeignKey("club_table.id"), nullable=True)
    association_id = Column(String)
    default_competition = Column(
        Integer, ForeignKey("competition_table.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"Player {self.club=} {self.human=}, {self.association_id=}, {self.default_competition=}"


class Competition(Base):

    __tablename__ = "competition_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    association = Column(String)
    year = Column(String)

    def __repr__(self) -> str:
        return f"Competition {self.id=} {self.name=} {self.association=} {self.year=}"


class Club(Base):

    __tablename__ = "club_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)

    def __repr__(self) -> str:
        return f"Club Data Instance {self.id=} {self.name=}"


class Team(Base):

    __tablename__ = "team_table"

    id = Column(Integer, primary_key=True)
    rank = Column(String)
    club = Column(Integer, ForeignKey("club_table.id"))
    year = Column(String)

    def __repr__(self) -> str:
        return f"Team {self.id=} {self.rank=} {self.club=} {self.year=}"


class TeamMatch(Base):

    __tablename__ = "teammatch_table"

    id = Column(Integer, primary_key=True)
    date = Column(String)
    competition = Column(Integer, ForeignKey("competition_table.id"))
    result = Column(String)
    home_team = Column(Integer, ForeignKey("team_table.id"))
    away_team = Column(Integer, ForeignKey("team_table.id"))
    used_for_rating = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"teammatch {self.id=} {self.date=} {self.competition=} {self.result=} {self.home_team=} {self.away_team=}"


class SinglesMatch(Base):

    __tablename__ = "singlesmatch_table"

    id = Column(Integer, primary_key=True)
    team_match = Column(Integer, ForeignKey("teammatch_table.id"), nullable=True)
    home_player = Column(Integer, ForeignKey("player_table.id"))
    away_player = Column(Integer, ForeignKey("player_table.id"))
    result = Column(String)  # this could be expanded to home legs, away legs, sets ...
    match_number = Column(Integer)

    def __repr__(self) -> str:
        return f"SinglesMatch {self.id=} {self.team_match=} {self.home_player=} {self.away_player=} {self.result=}"


class DoublesMatch(Base):

    __tablename__ = "doublesmatch_table"

    id = Column(Integer, primary_key=True)
    team_match = Column(Integer, ForeignKey("teammatch_table.id"), nullable=True)
    home_player1 = Column(Integer, ForeignKey("player_table.id"))
    home_player2 = Column(Integer, ForeignKey("player_table.id"))
    away_player1 = Column(Integer, ForeignKey("player_table.id"))
    away_player2 = Column(Integer, ForeignKey("player_table.id"))
    result = Column(String)  # this could be expanded to home legs, away legs, sets ...
    match_number = Column(Integer)


class SkillRating(Base):

    __tablename__ = "skillrating_table"

    id = Column(Integer, primary_key=True)
    player = Column(Integer, ForeignKey("player_table.id"))
    competition = Column(Integer, ForeignKey("competition_table.id"))
    rating_mu = Column(Float)
    rating_sigma = Column(Float)
    latest_update = Column(String)

    def __repr__(self) -> str:
        return f"SkillRating {self.id=} {self.player=} {self.competition=} {self.rating_mu=} {self.rating_sigma=}"
