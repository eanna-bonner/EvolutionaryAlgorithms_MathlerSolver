# evolution/mutation.py
from __future__ import annotations

from typing import List
import random

from config import EvolutionConfig


def mutate_genome(genome: List[int],
                  evo_cfg: EvolutionConfig) -> List[int]:
    """
    Per-gene mutation with probability evo_cfg.mutation_rate.
    Codons are replaced uniformly in [0, 255].
    """
    rate = evo_cfg.mutation_rate
    if rate <= 0.0:
        return list(genome)

    new = list(genome)
    for i in range(len(new)):
        if random.random() < rate:
            new[i] = random.randint(0, 255)
    return new

def hard_mutate_genome(
    genome: List[int],
    evo_cfg: EvolutionConfig,   
) -> List[int]:
    """
    Force mutation on at least one gene, preferring character influencing codons
    (indices >= min_char_index).
    """
    min_char_index = evo_cfg.min_char_index
    rate = evo_cfg.mutation_rate
    if random.random() < 2*rate:
        # Mutate a structural codon
        codon_to_mutate = random.randint(0, min_char_index - 1)
    else:
        codon_to_mutate = random.randint(min_char_index, len(genome) - 1)
    genome[codon_to_mutate] += 1
    return genome
