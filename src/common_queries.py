from sqlalchemy import select, insert, update, create_engine, Date, and_, Engine
from sqlalchemy.orm import Session, aliased
from tqdm import tqdm
import datetime
import trueskill
from collections import namedtuple

import schema


def leaderboard(engine: Engine, competition : str, season : datetime, conservative=True):
    # return player and their conservative rating mu - 3sigma
    PlayerRating = namedtuple("PlayerRating", ["name", "id", "rating", "club"])
    with Session(engine) as session:
        # select competition from name
        comp_stmt = select(schema.Competition.id).where((schema.Competition.name == competition) & (schema.Competition.year == season))
        comp_id = session.execute(comp_stmt).first()
        rating_stmt = select(schema.SkillRating, schema.Player, schema.Club).where(
            (schema.SkillRating.player == schema.Player.id) & 
            (schema.SkillRating.competition == comp_id[0]) & 
            (schema.Player.club == schema.Club.id)
        )
        ratings = session.execute(rating_stmt).all()
        leaderboard = []
        for rating, player, club in ratings:
            if player.association_id == "":
                continue
            r = rating.rating_mu - (3 * rating.rating_sigma)
            if not conservative:
                r = rating.rating_mu
            player_rating = PlayerRating(player.name, player.id, r, club.name)
            leaderboard.append(player_rating)
    
    leaderboard = sorted(leaderboard, key = lambda p : p.rating, reverse=True)
    return leaderboard

def get_associations_and_competitions(engine : Engine, association: str = None, season : datetime = None):
    with Session(engine) as session:
        stmt = select(schema.Competition)
        if season:
            stmt = stmt.where(schema.Competition.year == season)
        if association:
            stmt = stmt.where(schema.Competition.association == association)
        result = session.execute(stmt).all()
    return result


def get_previous_matches(engine : Engine, my_players : list, other_players: list):
    """Get previous matches between any two player from the given teams.

    Args:
        engine (Engine): Engine connected to the database.
        my_players (list): List of player tuples.
        other_players (list): List of player tuples.

    Returns:
        _type_: Match strings.
    """    
    with Session(engine) as session:
        stmt = select(schema.SinglesMatch, schema.TeamMatch).join(schema.TeamMatch).where(
            and_(schema.SinglesMatch.home_player.in_([p[1] for p in my_players]), schema.SinglesMatch.away_player.in_([p[1] for p in other_players])) |
            and_(schema.SinglesMatch.away_player.in_([p[1] for p in my_players]), schema.SinglesMatch.home_player.in_([p[1] for p in other_players])) 
        )
        result = session.execute(stmt).all()

    match_strings = []
    for player in my_players:
        player_matches = [(s, t) for s, t in result if player[1] in (s.home_player, s.away_player)]
        for single, team in player_matches:
            prev_single_str = f"{single.home_player} {single.result} {single.away_player}".replace(str(player[1]), player[0])
            prev_team_str = f" @ {team.date}, {team.result}"
            match_strings.append(prev_single_str + prev_team_str)

    for player in other_players:
        match_strings = [match.replace(str(player[1]), player[0]) for match in match_strings]
    
    return match_strings

def get_player_skill_for_team(engine : Engine, club_name : str, competition : str, ignore_players : list = None):
    if ignore_players is None:
        ignore_players = []

    PlayerTuple = namedtuple("PlayerTuple", ["name", "id", "rating"])

    with Session(engine) as session:
        # select club from clubname
        club_stmt = select(schema.Club.id).where(schema.Club.name == club_name)
        club_id = session.execute(club_stmt).first()
        # select competition from name
        comp_stmt = select(schema.Competition.id).where(schema.Competition.name == competition)
        comp_id = session.execute(comp_stmt).first()
        # select team matches for competition
        team_match_stmt = select(schema.TeamMatch.id).where(schema.TeamMatch.competition == comp_id[0])
        team_matches_id = session.execute(team_match_stmt).all()

        # iterate over team_matches of this competition
        # extract players that played for the relevant club
        relevant_matches = []
        for team_match_id in team_matches_id:
            players_home_stmt = select(schema.SinglesMatch, schema.Player).join(
                schema.Player, schema.SinglesMatch.home_player == schema.Player.id
            ).where(
                    (schema.SinglesMatch.team_match == team_match_id[0]) & \
                    (schema.Player.club == club_id[0])
                )
            home_players_club = session.execute(players_home_stmt).all()
            if home_players_club:
                relevant_matches.extend(home_players_club)

            players_away_stmt = select(schema.SinglesMatch, schema.Player).join(
                schema.Player, schema.SinglesMatch.away_player == schema.Player.id
            ).where(
                    (schema.SinglesMatch.team_match == team_match_id[0]) & \
                    (schema.Player.club == club_id[0])
                )
            away_players_club = session.execute(players_away_stmt).all()
            if away_players_club:
                relevant_matches.extend(away_players_club)

        ratings = []
        players_retrieved = []
        for _, player in relevant_matches:
            if player.id in players_retrieved or player.name in ignore_players:
                continue
            rating_stmt = select(schema.SkillRating).where((schema.SkillRating.player == player.id) & (schema.SkillRating.competition == comp_id[0]))
            rating = session.execute(rating_stmt).first()
            player_rating = PlayerTuple(player.name, player.association_id, trueskill.Rating(rating[0].rating_mu, rating[0].rating_sigma))
            players_retrieved.append(player.id)

            ratings.append(player_rating)
    return ratings

def get_positions_for_player(engine : Engine, player_id : int):
    with Session(engine) as session:
        home_stmt = select(schema.SinglesMatch.match_number).where(schema.SinglesMatch.home_player == player_id)
        away_stmt = select(schema.SinglesMatch.match_number).where(schema.SinglesMatch.away_player == player_id)
        home_positions = [r[0] for r in session.execute(home_stmt).all()]
        away_positions = [r[0] for r in session.execute(away_stmt).all()]

    return home_positions, away_positions


if __name__ == "__main__":
    db_path = "./darts-json.db"

    engine = create_engine(f"sqlite:///{db_path}")
    lb = leaderboard(engine, "DBH Bezirksliga 2")
    print(lb)