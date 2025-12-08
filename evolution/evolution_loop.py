# evolution/evolution_loop.py
from __future__ import annotations

from typing import Callable, List

from logging_config import get_logger
from config import EvolutionConfig
from evolution.genome import Individual
from evolution.selection import select_survivors, tournament_select, sort_by_fitness
from evolution.mutation import mutate_genome
from evolution.crossover import one_point_crossover

logger = get_logger(__name__)

# eval_fn: takes a list of Individuals and mutates their .fitness (and expr)
EvalFn = Callable[[List[Individual]], None]


def run_generation(population: List[Individual],
                   evo_cfg: EvolutionConfig,
                   eval_fn: EvalFn) -> List[Individual]:
    """
    Run one evolutionary generation:
      - Evaluate fitness via eval_fn
      - Select survivors by fitness bands
      - Breed new individuals with crossover + mutation
      - Preserve a small elite
    Returns new population of same size.
    """
    if not population:
        raise ValueError("Empty population")

    # Evaluate current population
    eval_fn(population)

    best = max(population, key=lambda ind: ind.fitness)
    logger.info("Best fitness this generation: %.4f", best.fitness)

    survivors = select_survivors(population, evo_cfg)
    pop_size = len(population)

    # Elites: copy top individuals back into new population
    elites = sort_by_fitness(survivors)[:max(1, int(evo_cfg.elite_fraction * pop_size))]
    new_pop: List[Individual] = [Individual(genome=list(ind.genome)) for ind in elites]

    # Breed until we refill the population
    while len(new_pop) < pop_size:
        p1 = tournament_select(survivors, k=evo_cfg.tournament_size)
        p2 = tournament_select(survivors, k=evo_cfg.tournament_size)

        g1, g2 = one_point_crossover(p1.genome, p2.genome, evo_cfg)
        g1 = mutate_genome(g1, evo_cfg)
        g2 = mutate_genome(g2, evo_cfg)

        new_pop.append(Individual(genome=g1))
        if len(new_pop) < pop_size:
            new_pop.append(Individual(genome=g2))

    return new_pop
