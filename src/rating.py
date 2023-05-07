from sqlalchemy import select, insert, update, create_engine, Date, Engine
from sqlalchemy.orm import Session, aliased
from pathlib import Path
import trueskill
import data
import pickle as pkl
from tqdm import tqdm
from datetime import datetime
from common_queries import get_associations_and_competitions

def reset_ratings(engine : Engine):
    """Reset all ratings back to (25, 8.33).

    Args:
        engine (Engine): Engine connected to the database.
    """    
    with Session(engine) as session:
        stmt = update(data.SkillRating).values(rating_mu=25, rating_sigma=8.3333)
        session.execute(stmt)
        session.commit()

def compute_ratings(engine : Engine, competition : data.Competition):
    """Compute ratings for a competition by iterating through all its matches.
    Currently only takes singles into account.

    Args:
        engine (Engine): Engine connected to the database.
        competition (str): Name of the competition.
    """    
    # TODO Doubles
    with Session(engine) as session:
        stmt = select(data.TeamMatch).where(data.TeamMatch.competition == competition.id).order_by(data.TeamMatch.date)
        team_matches = session.execute(stmt).all()
        for match in team_matches:
            match = match[0]
            if match.used_for_rating:
                continue
            else:
                update_stmt = update(data.TeamMatch).where(data.TeamMatch.id == match.id).values(used_for_rating=True)
                session.execute(update_stmt)

            singles_stmt = select(data.SinglesMatch).where(data.SinglesMatch.team_match == match.id)
            # doubles_stmt = select(data.DoublesMatch).where(data.DoublesMatch.team_match == match[0].id)
            singles = session.execute(singles_stmt).all()
            # doubles = session.execute(doubles_stmt).all()
            
            for single in singles:
                
                home_player_rating_stmt = select(data.SkillRating).where((data.SkillRating.player == single[0].home_player) & (data.SkillRating.competition == competition.id))
                home_player_rating = session.execute(home_player_rating_stmt).first()
                if not home_player_rating:
                    home_player_rating = data.SkillRating(
                        player=single[0].home_player,
                        competition=competition.id,
                        rating_mu=25,
                        rating_sigma=8.3333,
                        latest_update=match.date
                    )
                    session.add(home_player_rating)
                    session.commit()
                    session.refresh(home_player_rating)
                else:
                    home_player_rating = home_player_rating[0]

                away_player_rating_stmt = select(data.SkillRating).where((data.SkillRating.player == single[0].away_player) & (data.SkillRating.competition == competition.id))
                away_player_rating = session.execute(away_player_rating_stmt).first()
                if not away_player_rating:
                    away_player_rating = data.SkillRating(
                        player=single[0].away_player,
                        competition=competition.id,
                        rating_mu=25,
                        rating_sigma=8.3333,
                        latest_update=match.date
                    )
                    session.add(away_player_rating)
                    session.commit()
                    session.refresh(away_player_rating)
                else:
                    away_player_rating = away_player_rating[0]

                home_wins = single[0].result[0] > single[0].result[2] # h:a
                home_ts = trueskill.Rating(mu=home_player_rating.rating_mu, sigma=home_player_rating.rating_sigma)
                away_ts = trueskill.Rating(mu=away_player_rating.rating_mu, sigma=away_player_rating.rating_sigma)
                
                if home_wins:
                    home_ts, away_ts = trueskill.rate_1vs1(home_ts, away_ts)
                else:
                    away_ts, home_ts = trueskill.rate_1vs1(away_ts, home_ts)

                update_home_stmt = update(data.SkillRating).where(data.SkillRating.id == home_player_rating.id).values(
                    rating_mu=home_ts.mu,
                    rating_sigma=home_ts.sigma,
                    latest_update=match.date
                )
                update_away_stmt = update(data.SkillRating).where(data.SkillRating.id == away_player_rating.id).values(
                    rating_mu=away_ts.mu,
                    rating_sigma=away_ts.sigma,
                    latest_update=match.date
                )
                session.execute(update_home_stmt)
                session.execute(update_away_stmt)
                session.commit()

    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Populate the database.'
    )

    parser.add_argument('-db', "--database", help="Path to the database.", required=True)
    parser.add_argument('--season', help="What season we crawl. Expects YYYY (will be set to first of august that year.)", required=True, type=int)

    args = parser.parse_args()
    season = datetime(args.season, 8, 1)
    engine = create_engine(f"sqlite:///{args.database}")

    competitions = get_associations_and_competitions(engine, association="DBH", season=season)
    for c in competitions:
        c = c[0]
        compute_ratings(engine, c)
    # reset_ratings()

    # for association in ["DBH", "NDV"]:
    #     print("Compute ratings for", association)
    #     for comp in tqdm(assocs_comps[association]):
    #         compute_ratings(comp)

    #SELECT * FROM skillrating_table JOIN player_table ON skillrating_table.player = player_table.id ORDER BY skillrating_table.rating_mu DESC