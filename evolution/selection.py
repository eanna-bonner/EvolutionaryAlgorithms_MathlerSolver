# evolution/selection.py
from __future__ import annotations

from typing import List
import random

from config import EvolutionConfig
from evolution.genome import Individual


def sort_by_fitness(pop: List[Individual]) -> List[Individual]:
    return sorted(pop, key=lambda ind: ind.fitness, reverse=True)


def select_survivors(pop: List[Individual],
                     evo_cfg: EvolutionConfig) -> List[Individual]:
    """
    Keep top elite_fraction and a random subset of the next mid_fraction.
    Matches your 'fitness bands' / leaderboard idea.
    """
    if not pop:
        return []

    pop_sorted = sort_by_fitness(pop)
    n = len(pop_sorted)

    n_elite = max(1, int(evo_cfg.elite_fraction * n))
    n_mid = max(0, int(evo_cfg.mid_fraction * n))

    elites = pop_sorted[:n_elite]
    mids = pop_sorted[n_elite:n_elite + n_mid]

    survivors = list(elites)
    for ind in mids:
        if random.random() < 0.5:
            survivors.append(ind)

    if not survivors:
        survivors = [pop_sorted[0]]

    return survivors


def tournament_select(pop: List[Individual],
                      k: int = 3) -> Individual:
    """k-way tournament selection."""
    if not pop:
        raise ValueError("Empty population")

    k = min(k, len(pop))
    candidates = random.sample(pop, k)
    return max(candidates, key=lambda ind: ind.fitness)
