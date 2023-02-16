from sqlalchemy import select, insert, update, create_engine, Date, and_
from sqlalchemy.orm import Session, aliased
from tqdm import tqdm
import datetime

import os
import pickle as pkl
import data
from pathlib import Path

def reorder_name(player):
    player = player.strip()
    name_split = player.split(",")
    return f"{' '.join([n.strip() for n in name_split[1:]])} {name_split[0]}".strip()

#TODO: Players have a club but no team, maybe create "temporary" id for more matches
def populate_players(engine, players):
    with Session(engine) as session:
        session.begin()
        for id, name, club_name in players:
            name = name.strip()
            try:
                player_obj = session.query(data.Player).where(data.Player.id == id).first()
                club_stmt = select(data.Club).where(data.Club.name == club_name)
                club_obj = session.execute(club_stmt).first()
                if not club_obj:
                    raise ValueError(f"Club not found {club_name}")
                
                if not player_obj:
                    if "Spieler ist nicht" in id:
                        continue
                    player_obj = data.Player(
                        name=name,
                        id=id,
                        club=club_obj[0].id
                    )
                    session.add(player_obj)
            except:
                
                session.rollback()
                raise
                
            else:
                session.commit()

def populate_clubs_and_teams(engine, clubs_and_teams):
    with Session(engine) as session:
        session.begin()
        for club, teams in clubs_and_teams.items():
            try:
                club_obj = session.query(data.Club).where(data.Club.name == club).first()
                if not club_obj:
                    club_obj = data.Club(name=club)
                    session.add(club_obj)
                    session.flush() # push to db
                    session.refresh(club_obj) # get ids
                for team in teams:
                    team_obj = session.query(data.Team).where(and_(data.Team.rank == team, data.Team.club == club_obj.id)).first()
                    if not team_obj:
                        team_obj = data.Team(rank=team, club=club_obj.id, year=datetime.date(2022, 1, 8))
                        session.add(team_obj)
            except:
                session.rollback()
                raise
            else:
                session.commit()
        
def populate_competitions(engine, associations_competitions):
    with Session(engine) as session:
        session.begin()
        for assoc, comps in associations_competitions.items():
            for comp in comps:
                try:
                    comp_obj = session.query(data.Competition).where(and_(data.Competition.name == comp, data.Competition.association == assoc)).first()
                    if not comp_obj:
                        comp_obj = data.Competition(
                            name=comp,
                            association=assoc,
                            year=datetime.date(2022, 1, 8)
                        )
                        session.add(comp_obj)
                except:
                    session.rollback()
                    raise
                else:
                    session.commit()

def populate_matches(session, matches, teammatch_id=None):
    if matches is None:
        return
    for i, match in enumerate(matches):
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
            except:
                print("No valid double", home_player, "vs.", away_player)
                continue
            
            home_player1 = reorder_name(home_player1)
            home_player2 = reorder_name(home_player2)
            away_player1 = reorder_name(away_player1)
            away_player2 = reorder_name(away_player2)

        if not doubles:

            home_player = reorder_name(home_player)
            away_player = reorder_name(away_player)

            home_table = aliased(data.Player)
            away_table = aliased(data.Player)

            singles_stmt = select(data.SinglesMatch).join(
                home_table, home_table.id == data.SinglesMatch.home_player
            ).join(
                    away_table, away_table.id == data.SinglesMatch.away_player
                ).where(
                    and_(away_table.name == away_player, home_table.name == home_player, data.SinglesMatch.team_match == teammatch_id)
                )
            singles_obj = session.execute(singles_stmt).first()

            if not singles_obj:
                # TODO Sanity check club of player here!!!
                # Pass team_match object instead of ID and check for club
                home_stmt = select(data.Player.id).where(data.Player.name == home_player)
                home_obj = session.execute(home_stmt).first()

                away_stmt = select(data.Player.id).where(data.Player.name == away_player)
                away_obj = session.execute(away_stmt).first()

                if not all([home_obj, away_obj]):
                    print(f"One or both of players f{(home_player, away_player)} could not be found.")
                    continue

                match_obj = data.SinglesMatch(
                    team_match=teammatch_id,
                    home_player=home_obj[0],
                    away_player=away_obj[0],
                    result=result,
                    match_number=match_number
                )
                session.add(match_obj)
                session.flush()
                session.refresh(match_obj)
        else:

            home1_table = aliased(data.Player)
            away1_table = aliased(data.Player)
            home2_table = aliased(data.Player)
            away2_table = aliased(data.Player)

            doubles_stmt = select(data.DoublesMatch).join(
                home1_table, home1_table.id == data.DoublesMatch.home_player1
                ).join(
                    away1_table, away1_table.id == data.DoublesMatch.away_player1
                ).join(
                    away2_table, away2_table.id == data.DoublesMatch.away_player2
                ).join(
                    home2_table, home2_table.id == data.DoublesMatch.home_player2
                ).where( # lets hope they dont switch around, i dont want to check all combinations
                    and_(home_player1.strip() == home1_table.name,
                    away_player1.strip() == away1_table.name,
                    home_player2.strip() == home2_table.name,
                    away_player2.strip() == away2_table.name,
                    teammatch_id == data.DoublesMatch.team_match)
                )
            doubles_obj = session.execute(doubles_stmt).first()
            if not doubles_obj:
                home1_stmt = select(data.Player).where(data.Player.name == home_player1.strip())
                home1_obj = session.execute(home1_stmt).first()

                away1_stmt = select(data.Player).where(data.Player.name == away_player1.strip())
                away1_obj = session.execute(away1_stmt).first()

                home2_stmt = select(data.Player).where(data.Player.name == home_player2.strip())
                home2_obj = session.execute(home2_stmt).first()

                away2_stmt = select(data.Player).where(data.Player.name == away_player2.strip())
                away2_obj = session.execute(away2_stmt).first()

                if not all([home1_obj, home2_obj, away1_obj, away2_obj]):
                    print("Error at", match, flush=True)
                    print(f"One of these players does not exist: {(home_player1, home_player2, away_player1, away_player2)}")
                    continue
                
                match_obj = data.DoublesMatch(
                    team_match=teammatch_id,
                    home_player1=home1_obj[0].id,
                    away_player1=away1_obj[0].id,
                    home_player2=home2_obj[0].id,
                    away_player2=away2_obj[0].id,
                    result=result,
                    match_number=match_number
                )

                session.add(match_obj)

def populate_teammatches(engine, team_matches, matches):
    with Session(engine) as session:
        session.begin()
        for i, match in enumerate(team_matches):
            # get competition id and home team id
            date = match["date"]
            try:
                
                comp_stmt = select(data.Competition.id).where(and_(data.Competition.name == match["competition"], data.Competition.association == match["association"]))
                comp_obj = session.execute(comp_stmt).first()

                home_stmt = select(data.Team.id).join(data.Club).where(and_(data.Team.rank == match["home_team"][-1], data.Club.name == match["home_team"][:-2]))
                home_obj = session.execute(home_stmt).first()

                away_stmt = select(data.Team.id).join(data.Club).where(and_(data.Team.rank == match["away_team"][-1], data.Club.name == match["away_team"][:-2]))
                away_obj = session.execute(away_stmt).first()

                if not all([comp_obj, home_obj, away_obj]):
                    if "Spielfrei" in [match['home_team'], match['away_team']]:
                        continue
                    print(f"Could not find Competition or team in database {match['competition']} {match['home_team']} {match['away_team']}")
                    continue
                
                # try to look for exact teammatch
                stmt = select(data.TeamMatch).where(
                    and_(data.TeamMatch.date == date, 
                    data.TeamMatch.home_team == home_obj[0],
                    data.TeamMatch.away_team == away_obj[0],
                    data.TeamMatch.competition == comp_obj[0])
                    )
                tm_obj = session.execute(stmt).first()

                if not tm_obj:
                
                    teammatch_ob = data.TeamMatch(
                        date = date,
                        competition=comp_obj[0],
                        result=match["result"],
                        home_team=home_obj[0],
                        away_team=away_obj[0],
                    )
                    session.add(teammatch_ob)
                    session.flush()
                    session.refresh(teammatch_ob)
                    team_match_id = teammatch_ob.id
                else:
                    team_match_id = tm_obj[0].id

                
                populate_matches(session, matches[i], team_match_id)
                
            except:
                session.rollback()
                raise
            else:
                session.commit()


if __name__ == "__main__":

    engine = create_engine("sqlite:///darts.db")
    data_path = Path("./data")
    
    with open(data_path / "assocs_comps.pkl", "rb") as f:
        ac = pkl.load(f)

    populate_competitions(engine, ac)

    

    club_pickles = [f for f in os.listdir(data_path) if f.startswith("teamsclubs")]
    player_pickles = [f for f in os.listdir(data_path) if f.startswith("players")]
    matches_pickles = [f for f in os.listdir(data_path) if f.startswith("matches") and ("NDV" in f or "DBH" in f)]
    teammatches_pickles = [f for f in os.listdir(data_path) if f.startswith("matchdays") and ("NDV" in f or "DBH" in f)]

    for i in range(len(club_pickles)):

        clubfile = club_pickles[i]
        playerfile = player_pickles[i]
        
        with open(data_path / playerfile, "rb") as f:
            players = pkl.load(f, encoding="UTF-8")
        with open(data_path / clubfile, "rb") as f:
            clubs = pkl.load(f, encoding="UTF-8")

        populate_clubs_and_teams(engine, clubs)
        populate_players(engine, players)

    for i in range(len(matches_pickles)):
        matchfile = matches_pickles[i]
        teammatchfile = teammatches_pickles[i]

        with open(data_path / teammatchfile, "rb") as f:
            team_matches = pkl.load(f, encoding="UTF-8")
        with open(data_path / matchfile, "rb") as f:
            matches = pkl.load(f, encoding="UTF-8")

        
        populate_teammatches(engine, team_matches, matches)

    
