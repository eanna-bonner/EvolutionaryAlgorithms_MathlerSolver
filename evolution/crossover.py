# evolution/crossover.py
from __future__ import annotations

from typing import List, Tuple
import random

from config import EvolutionConfig


def one_point_crossover(g1: List[int],
                        g2: List[int],
                        evo_cfg: EvolutionConfig) -> Tuple[List[int], List[int]]:
    """One-point crossover. If it doesn’t trigger, parents are copied through."""
    if len(g1) != len(g2):
        raise ValueError("Genomes must have same length for crossover")

    if len(g1) < 2 or random.random() > evo_cfg.crossover_rate:
        return list(g1), list(g2)

    point = random.randint(1, len(g1) - 1)
    c1 = g1[:point] + g2[point:]
    c2 = g2[:point] + g1[point:]
    return c1, c2
