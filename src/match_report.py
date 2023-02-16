# For a given match in the future, get competing players, plot their rating and determine best fixture for given subset of players
# also check who played at what position!
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import itertools

import trueskill
from scipy.stats import norm
from sqlalchemy import select, insert, update, create_engine, Date, and_
from sqlalchemy.orm import Session, aliased
import data

def win_probability(team1, team2):
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = np.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)

def plot_skill_distributions(players):
    # TODO: FaceGrid seems to be way too tricky, try comparing gaussion dist plots
    x_values = np.linspace(0, 50, 1000)
    data = {
        "name" : [f"{p[0]} ({p[1]})" for p in players],
        "team" : [str(p[1])[:3] for p in players],
        "mu" : [p[2].mu for p in players],
        "sigma" : [p[2].sigma for p in players],
        "skill_dist" : np.stack([norm.pdf(x_values,p[2].mu,p[2].sigma) for p in players])

    }
    d = norm.pdf(x_values,0,1)
    print(type(d), d.shape)
    print(data["skill_dist"].shape)
    
    df = pd.DataFrame(data)
    ridge_plot = sns.FacetGrid(df, row="name", hue="team", aspect=10, height=1.5)
    ridge_plot.map(sns.kdeplot, "skill_dist", clip_on=False, shade=True, alpha=0.7, lw=4, bw=.2)
    # ridge_plot.map(plt.axhline, y=0, lw=4, clip_on=False)

    return ridge_plot


def read_player_skill_for_team(club_name, competition, ignore_players=None):
    if ignore_players is None:
        ignore_players = []

    engine = create_engine("sqlite:///../darts.db")
    with Session(engine) as session:
        # select club from clubname
        club_stmt = select(data.Club.id).where(data.Club.name == club_name)
        club_id = session.execute(club_stmt).first()
        # select competition from name
        comp_stmt = select(data.Competition.id).where(data.Competition.name == competition)
        comp_id = session.execute(comp_stmt).first()
        # select team matches for competition
        team_match_stmt = select(data.TeamMatch.id).where(data.TeamMatch.competition == comp_id[0])
        team_matches_id = session.execute(team_match_stmt).all()

        # iterate over team_matches of this competition
        # extract players that played for the relevant club
        relevant_matches = []
        for team_match_id in team_matches_id:
            players_home_stmt = select(data.SinglesMatch, data.Player).join(
                data.Player, data.SinglesMatch.home_player == data.Player.id
            ).where(
                    (data.SinglesMatch.team_match == team_match_id[0]) & \
                    (data.Player.club == club_id[0])
                )
            home_players_club = session.execute(players_home_stmt).all()
            if home_players_club:
                relevant_matches.extend(home_players_club)

            players_away_stmt = select(data.SinglesMatch, data.Player).join(
                data.Player, data.SinglesMatch.away_player == data.Player.id
            ).where(
                    (data.SinglesMatch.team_match == team_match_id[0]) & \
                    (data.Player.club == club_id[0])
                )
            away_players_club = session.execute(players_away_stmt).all()
            if away_players_club:
                relevant_matches.extend(away_players_club)

        ratings = []
        players_retrieved = []
        for _, player in relevant_matches:
            if player.id in players_retrieved or player.name in ignore_players:
                continue
            rating_stmt = select(data.SkillRating).where((data.SkillRating.player == player.id) & (data.SkillRating.competition == comp_id[0]))
            rating = session.execute(rating_stmt).first()
            player_rating = (player.name, player.id, trueskill.Rating(rating[0].rating_mu, rating[0].rating_sigma))
            players_retrieved.append(player.id)

            ratings.append(player_rating)
    return ratings

def plot_match_qualities(players_a, players_b):
    # Try this?
    # https://seaborn.pydata.org/examples/heat_scatter.html
    qualities = np.zeros((len(players_a), len(players_b)))
    a_indices = list(range(len(players_a)))
    b_indices = list(range(len(players_b)))

    for i_pa, i_pb in itertools.product(a_indices, b_indices):
        player_a = players_a[i_pa]
        player_b = players_b[i_pb]
        pa_win = win_probability([player_a[2]], [player_b[2]])
        qualities[i_pa, i_pb] = pa_win
    sns.set_theme(style="whitegrid")
    f, ax = plt.subplots()

    cmap = sns.color_palette("coolwarm", as_cmap=True)
    chart = sns.heatmap(
        qualities,
        yticklabels=[f"{p[0]} ({p[1]})" for p in players_a],
        xticklabels=[f"{p[0]} ({p[1]})" for p in players_b],
        cmap=cmap,
        vmax=1,
        vmin=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": .5},
        # annot=True
    )
    chart.set_xticklabels(chart.get_xticklabels(), rotation=45, horizontalalignment='right')

    return f

def plot_positions():
    # get usual match positions into player tuple first, then, plot histogram here
    pass

def best_fixture(players):
    # get combination with highest combined winning percentage
    pass

if __name__ == "__main__":
    han96 = read_player_skill_for_team("Hannover 96", "DBH Bezirksliga 2")
    opp = read_player_skill_for_team("Sieben Zwerge Dart Team e.V.", "DBH Bezirksliga 2")
    plot_match_qualities(han96, opp)
