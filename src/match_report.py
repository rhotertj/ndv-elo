import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.gridspec as grid_spec
from matplotlib.colors import ListedColormap
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


def plot_ridge_skill_distributions(home_players, away_players):
    # https://matplotlib.org/matplotblog/posts/create-ridgeplots-in-matplotlib/
    x = np.linspace(0, 50, 1000)

    all_players = home_players + away_players
    all_players = sorted(all_players, key=lambda p : p[2].mu, reverse=True) 

    home_map = plt.colormaps["Greens"]
    away_map = plt.colormaps["Purples"]

    gs = (grid_spec.GridSpec(len(all_players), 1))
    fig = plt.figure(figsize=(8,6))

    ax_objs = []
    for i, player in enumerate(all_players):
        # creating new axes object and appending to ax_objs
        ax_objs.append(fig.add_subplot(gs[i:i+1, 0:]))

        plot = ax_objs[-1].plot(x, norm.pdf(x, player[2].mu, player[2].sigma) , alpha=1, color="#f0f0f0")
        color_mapping = home_map if player in home_players else away_map
        ax_objs[-1].fill_between(x, norm.pdf(x, player[2].mu, player[2].sigma) , color=color_mapping((i*16)+64))

        # make background transparent
        rect = ax_objs[-1].patch
        rect.set_alpha(0)

        # remove borders, axis ticks, and labels
        ax_objs[-1].set_yticklabels([])

        # remove spines
        spines = ["top","right","left","bottom"]
        for s in spines:
            ax_objs[-1].spines[s].set_visible(False)

        # only allow x ticks at the very bottom
        if i == len(all_players) - 1:
            ax_objs[-1].set_xlabel("Skill Rating", fontsize=14)
        else:
            ax_objs[-1].set_xticklabels([])

        ax_objs[-1].text(-1, 0, player[0], fontsize=14, ha="right")

    gs.update(hspace= -0.5)
    plt.tight_layout()
    return fig

def plot_paired_skill_distributions(home_players, away_players):
    plt.clf()
    sns.set_context("notebook")
    sns.set_style("white")

    x = np.linspace(0, 50, 1000)
    y_home = []
    for player in home_players: 
        y = norm.pdf(x, player[2].mu, player[2].sigma)
        y_home.append(y)

    y_away = []
    for player in away_players:
        x = np.linspace(0, 50, 1000)
        y = norm.pdf(x, player[2].mu, player[2].sigma)
        y_away.append(y)


    fig, axes = plt.subplots(len(home_players), len(away_players), sharey=True, figsize=(20,16))
    
    home_indices = list(range(len(home_players)))
    away_indices = list(range(len(away_players)))

    for h, a in itertools.product(home_indices, away_indices):
        axes[h, a].plot(x ,y_home[h], alpha=1, color="green")
        axes[h, a].fill_between(x ,y_home[h], alpha=0.4, color="green")
        axes[h, a].plot(x, y_away[a], color="blue")
        axes[h, a].fill_between(x ,y_away[a], color="blue", alpha=0.4)

        axes[h, 0].set_ylabel(home_players[h][0])
        axes[-1, a].set_xlabel(away_players[a][0])

    plt.yticks(ticks=[])
    return fig

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
    f = plt.figure(figsize=(14,10))

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

def read_positions_for_player(player_id):
    engine = create_engine("sqlite:///../darts.db")
    with Session(engine) as session:
        home_stmt = select(data.SinglesMatch.match_number).where(data.SinglesMatch.home_player == player_id)
        away_stmt = select(data.SinglesMatch.match_number).where(data.SinglesMatch.away_player == player_id)
        home_positions = [r[0] for r in session.execute(home_stmt).all()]
        away_positions = [r[0] for r in session.execute(away_stmt).all()]

    return home_positions, away_positions


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
