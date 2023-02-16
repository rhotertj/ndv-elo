from sqlalchemy import select, insert, update, create_engine, Date, and_
from sqlalchemy.orm import Session, aliased

import trueskill
import data


def reset_ratings():
    engine = create_engine("sqlite:///darts.db")
    with Session(engine) as session:
            stmt = update(data.SkillRating).values(rating_mu=25, rating_sigma=8.3333)
            session.execute(stmt)
            session.commit()

def compute_ratings(competition):
    # TODO Doubles
    engine = create_engine("sqlite:///darts.db")
    with Session(engine) as session:
        stmt = select(data.TeamMatch, data.Competition).join(data.Competition).where(data.Competition.name == competition).order_by(data.TeamMatch.date)
        team_matches = session.execute(stmt).all()
        for match in team_matches:
            singles_stmt = select(data.SinglesMatch).where(data.SinglesMatch.team_match == match[0].id)
            # doubles_stmt = select(data.DoublesMatch).where(data.DoublesMatch.team_match == match[0].id)
            singles = session.execute(singles_stmt).all()
            # doubles = session.execute(doubles_stmt).all()
            
            for single in singles:
                
                home_player_rating_stmt = select(data.SkillRating).where((data.SkillRating.player == single[0].home_player) & (data.SkillRating.competition == match[1].id))
                home_player_rating = session.execute(home_player_rating_stmt).first()
                if not home_player_rating:
                    home_player_rating = data.SkillRating(
                        player=single[0].home_player,
                        competition=match[1].id,
                        rating_mu=25,
                        rating_sigma=8.3333
                    )
                    session.add(home_player_rating)
                    session.commit()
                    session.refresh(home_player_rating)
                else:
                    home_player_rating = home_player_rating[0]

                away_player_rating_stmt = select(data.SkillRating).where((data.SkillRating.player == single[0].away_player) & (data.SkillRating.competition == match[1].id))
                away_player_rating = session.execute(away_player_rating_stmt).first()
                if not away_player_rating:
                    away_player_rating = data.SkillRating(
                        player=single[0].away_player,
                        competition=match[1].id,
                        rating_mu=25,
                        rating_sigma=8.3333
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
                    rating_sigma=home_ts.sigma
                )
                update_away_stmt = update(data.SkillRating).where(data.SkillRating.id == away_player_rating.id).values(
                    rating_mu=away_ts.mu,
                    rating_sigma=away_ts.sigma
                )
                session.execute(update_home_stmt)
                session.execute(update_away_stmt)
                session.commit()

    
if __name__ == "__main__":
    # reset_ratings()
    compute_ratings("DBH Bezirksliga 2")
    compute_ratings("DBH Bezirksoberliga")
    #SELECT * FROM skillrating_table JOIN player_table ON skillrating_table.player = player_table.id ORDER BY skillrating_table.rating_mu DESC