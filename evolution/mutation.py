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
    min_char_index: int = 4,   # 0-based: codons 0–3 are structural and dont have an effect on selected characters
) -> List[int]:
    """
    Force mutation on at least one gene, preferring character influencing codons
    (indices >= min_char_index).
    """
    codon_to_mutate = random.randint(min_char_index, len(genome) - 1)
    genome[codon_to_mutate] += 1
    return genome
