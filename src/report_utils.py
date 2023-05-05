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
from common_queries import get_positions_for_player

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
    all_players = sorted(all_players, key=lambda p : p.rating.mu, reverse=True) 

    home_map = plt.colormaps["Greens"]
    away_map = plt.colormaps["Purples"]

    gs = (grid_spec.GridSpec(len(all_players), 1))
    fig = plt.figure(figsize=(8,6))

    ax_objs = []
    for i, player in enumerate(all_players):
        # creating new axes object and appending to ax_objs
        ax_objs.append(fig.add_subplot(gs[i:i+1, 0:]))

        plot = ax_objs[-1].plot(x, norm.pdf(x, player.rating.mu, player.rating.sigma) , alpha=1, color="#f0f0f0")
        color_mapping = home_map if player in home_players else away_map
        ax_objs[-1].fill_between(x, norm.pdf(x, player.rating.mu, player.rating.sigma) , color=color_mapping((i*16)+64))

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

        ax_objs[-1].text(-1, 0, player.name, fontsize=14, ha="right")

    gs.update(hspace= -0.5)
    plt.tight_layout()
    return fig


# plot previous lineup per player
def plot_player_positions_bar(players):
    sns.set_style("darkgrid")
    fig, ax = plt.subplots(len(players), 2, figsize=(14,10), sharex=True, sharey=True)
    plt.xticks(ticks=[1,2,3,4])

    skill_colormap = plt.colormaps["jet"]

    sorted_players = sorted(players, key=lambda p : p.rating.mu)

    for i, player in enumerate(sorted_players):
        home_positions, away_positions = get_positions_for_player(player.id)
        home_bins, home_occurences = np.unique(home_positions, return_counts=True)
        away_bins, away_occurences = np.unique(away_positions, return_counts=True)

        ax[i, 0].bar(home_bins, home_occurences, color=skill_colormap((i * 10) + 80))
        ax[i, 1].bar(away_bins, away_occurences, color=skill_colormap((i * 10) + 80))
        # ax[i, 0].set_ylabel(away_players[i][0], rotation=0)
        ax[i, 0].text(-0.1, 1, player.name, fontsize=14, ha="right")

    return fig

def plot_paired_skill_distributions(home_players, away_players):
    x = np.linspace(0, 50, 1000)
    y_home = []
    for player in home_players: 
        y = norm.pdf(x, player.rating.mu, player.rating.sigma)
        y_home.append(y)

    y_away = []
    for player in away_players:
        x = np.linspace(0, 50, 1000)
        y = norm.pdf(x, player.rating.mu, player.rating.sigma)
        y_away.append(y)


    fig, axes = plt.subplots(len(home_players), len(away_players), sharey=True, figsize=(20,16))
    
    home_indices = list(range(len(home_players)))
    away_indices = list(range(len(away_players)))

    for h, a in itertools.product(home_indices, away_indices):
        axes[h, a].plot(x ,y_home[h], alpha=1, color="green")
        axes[h, a].fill_between(x ,y_home[h], alpha=0.4, color="green")
        axes[h, a].plot(x, y_away[a], color="blue")
        axes[h, a].fill_between(x ,y_away[a], color="blue", alpha=0.4)

        axes[h, 0].set_ylabel(home_players[h].name)
        axes[-1, a].set_xlabel(away_players[a].name)

    plt.yticks(ticks=[])
    return fig

def plot_match_qualities(players_a, players_b):
    qualities = np.zeros((len(players_a), len(players_b)))
    a_indices = list(range(len(players_a)))
    b_indices = list(range(len(players_b)))

    for i_pa, i_pb in itertools.product(a_indices, b_indices):
        player_a = players_a[i_pa]
        player_b = players_b[i_pb]
        pa_win = win_probability([player_a.rating], [player_b.rating])
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

def plot_positions():
    # get usual match positions into player tuple first, then, plot histogram here
    pass

def best_fixture(players):
    # get combination with highest combined winning percentage
    pass


