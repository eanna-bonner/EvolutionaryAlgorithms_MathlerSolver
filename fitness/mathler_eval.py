# fitness/mathler_eval.py
from __future__ import annotations

from typing import List

from config import FitnessConfig
from evolution.genome import Individual
from grammar import decode_genome_to_expr, MappingError
from fitness import score_expression
from engine import GuessResult


def make_eval_population_mathler(target_value: float,
                                 history: List[GuessResult],
                                 cfg: FitnessConfig):
    """
    Factory that returns an eval_fn suitable for the evolution loop.

    The returned function:
      - decodes each individual's genome to an expr
      - scores it with score_expression
      - stores expr and fitness on the Individual
    """

    def eval_population(population: List[Individual]) -> None:
        for ind in population:
            try:
                expr = decode_genome_to_expr(ind.genome)
            except MappingError:
                # Unmappable genome: treat as very bad
                ind.expr = None
                ind.fitness = float("-inf")
                continue

            # We let score_expression handle evaluation and scoring.
            fitness = score_expression(expr, target_value, history, cfg)

            ind.expr = expr
            ind.fitness = fitness

    return eval_population
