import logging
from datetime import datetime

import trueskill
from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session
from tqdm import tqdm

from .schema import DoublesMatch, Player, SinglesMatch, SkillRating, TeamMatch

# TODO Document change in new table


def get_or_create_player_rating(
    session: Session, player_id: int, competition_id: int, match_date: datetime
):
    player_rating_stmt = select(SkillRating).where(
        (SkillRating.player == player_id) & (SkillRating.competition == competition_id)
    )
    player_rating = session.execute(player_rating_stmt).first()

    if not player_rating:
        player_rating = SkillRating(
            player=player_id,
            competition=competition_id,
            rating_mu=trueskill.MU,
            rating_sigma=trueskill.SIGMA,
            latest_update=match_date,
        )
        session.add(player_rating)
        session.commit()
        session.refresh(player_rating)
    else:
        (player_rating,) = player_rating

    return player_rating


def reset_ratings(engine: Engine):
    """Reset all ratings back to (25, 8.33).

    Args:
        engine (Engine): Engine connected to the database.
    """
    with Session(engine) as session:
        stmt = update(SkillRating).values(rating_mu=25, rating_sigma=8.3333)
        session.execute(stmt)
        session.commit()


def update_singles(session: Session, team_match: TeamMatch, singles: list):
    for (single,) in singles:

        home_player_rating = get_or_create_player_rating(
            session=session,
            player_id=single.home_player,
            competition_id=team_match.competition,
            match_date=team_match.date,
        )

        away_player_rating = get_or_create_player_rating(
            session=session,
            player_id=single.away_player,
            competition_id=team_match.competition,
            match_date=team_match.date,
        )

        try:
            home_wins = single.result[0] > single.result[2]  # home:away
        except Exception:
            logging.info(f"Skipping {single} because of invalid result")
            continue

        home_ts = trueskill.Rating(
            mu=home_player_rating.rating_mu,
            sigma=home_player_rating.rating_sigma,
        )
        away_ts = trueskill.Rating(
            mu=away_player_rating.rating_mu,
            sigma=away_player_rating.rating_sigma,
        )

        if home_wins:
            home_ts, away_ts = trueskill.rate_1vs1(home_ts, away_ts)
        else:
            away_ts, home_ts = trueskill.rate_1vs1(away_ts, home_ts)

        # TODO Document update

        update_home_stmt = (
            update(SkillRating)
            .where(SkillRating.id == home_player_rating.id)
            .values(
                rating_mu=home_ts.mu,
                rating_sigma=home_ts.sigma,
                latest_update=team_match.date,
            )
        )
        update_away_stmt = (
            update(SkillRating)
            .where(SkillRating.id == away_player_rating.id)
            .values(
                rating_mu=away_ts.mu,
                rating_sigma=away_ts.sigma,
                latest_update=team_match.date,
            )
        )
        session.execute(update_home_stmt)
        session.execute(update_away_stmt)
        session.commit()


def update_doubles(session: Session, team_match: TeamMatch, doubles: list):
    for (double,) in doubles:

        home_player1_rating = get_or_create_player_rating(
            session=session,
            player_id=double.home_player1,
            competition_id=team_match.competition,
            match_date=team_match.date,
        )

        home1_ts = trueskill.Rating(
            mu=home_player1_rating.rating_mu,
            sigma=home_player1_rating.rating_sigma,
        )

        home_player2_rating = get_or_create_player_rating(
            session=session,
            player_id=double.home_player2,
            competition_id=team_match.competition,
            match_date=team_match.date,
        )

        home2_ts = trueskill.Rating(
            mu=home_player2_rating.rating_mu,
            sigma=home_player2_rating.rating_sigma,
        )

        away_player1_rating = get_or_create_player_rating(
            session=session,
            player_id=double.away_player1,
            competition_id=team_match.competition,
            match_date=team_match.date,
        )

        away1_ts = trueskill.Rating(
            mu=away_player1_rating.rating_mu,
            sigma=away_player1_rating.rating_sigma,
        )

        away_player2_rating = get_or_create_player_rating(
            session=session,
            player_id=double.away_player2,
            competition_id=team_match.competition,
            match_date=team_match.date,
        )

        away2_ts = trueskill.Rating(
            mu=away_player2_rating.rating_mu,
            sigma=away_player2_rating.rating_sigma,
        )

        home_team_ratings = [home1_ts, home2_ts]
        away_team_ratings = [away1_ts, away2_ts]

        try:
            home_wins = double.result[0] > double.result[2]
        except Exception:
            logging.info(f"Skipping {double} because of invalid result")
            continue
        ranks = [0, 1] if home_wins else [1, 0]

        (new_home1_ts, new_home2_ts), (new_away1_ts, new_away2_ts) = trueskill.rate(
            [home_team_ratings, away_team_ratings], ranks=ranks
        )
        update_home1_stmt = (
            update(SkillRating)
            .where(SkillRating.id == home_player1_rating.id)
            .values(
                rating_mu=new_home1_ts.mu,
                rating_sigma=new_home1_ts.sigma,
                latest_update=team_match.date,
            )
        )
        session.execute(update_home1_stmt)

        update_home2_stmt = (
            update(SkillRating)
            .where(SkillRating.id == home_player2_rating.id)
            .values(
                rating_mu=new_home2_ts.mu,
                rating_sigma=new_home2_ts.sigma,
                latest_update=team_match.date,
            )
        )
        session.execute(update_home2_stmt)

        update_away1_stmt = (
            update(SkillRating)
            .where(SkillRating.id == away_player1_rating.id)
            .values(
                rating_mu=new_away1_ts.mu,
                rating_sigma=new_away1_ts.sigma,
                latest_update=team_match.date,
            )
        )
        session.execute(update_away1_stmt)

        update_away2_stmt = (
            update(SkillRating)
            .where(SkillRating.id == away_player2_rating.id)
            .values(
                rating_mu=new_away2_ts.mu,
                rating_sigma=new_away2_ts.sigma,
                latest_update=team_match.date,
            )
        )
        session.execute(update_away2_stmt)
        session.commit()


def compute_ratings(engine: Engine):
    """Compute ratings for a competition by iterating through all its matches.
    Currently only takes singles into account.

    Args:
        engine (Engine): Engine connected to the database.
        competition (str): Name of the competition.
    """
    with Session(engine) as session:
        stmt = (
            select(TeamMatch)
            # trunk-ignore(ruff/E712)
            .where(TeamMatch.used_for_rating == False).order_by(TeamMatch.date)
        )
        team_matches = session.execute(stmt).all()
        for team_match in tqdm(team_matches):
            (team_match,) = team_match

            singles_stmt = select(SinglesMatch).where(
                SinglesMatch.team_match == team_match.id
            )
            doubles_stmt = select(DoublesMatch).where(
                DoublesMatch.team_match == team_match.id
            )
            singles = session.execute(singles_stmt).all()
            doubles = session.execute(doubles_stmt).all()

            update_singles(session, team_match, singles)
            update_doubles(session, team_match, doubles)

            update_stmt = (
                update(TeamMatch)
                .where(TeamMatch.id == team_match.id)
                .values(used_for_rating=True)
            )
            session.execute(update_stmt)

        exists_subq = (
            select(SkillRating).where(SkillRating.player == Player.id).exists()
        )
        players_wo_rating_stmt = select(Player).where(~exists_subq)
        players_wo_rating = session.execute(players_wo_rating_stmt)

        for (player,) in tqdm(players_wo_rating):
            player_rating = SkillRating(
                player=player.id,
                competition=player.default_competition,
                rating_mu=trueskill.MU,
                rating_sigma=trueskill.SIGMA,
                latest_update=team_match.date,
            )
            session.add(player_rating)
            session.commit()
