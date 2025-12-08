# evolution/genome.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import random


@dataclass
class Individual:
    genome: List[int]
    expr: Optional[str] = None
    fitness: float = float("-inf")


def create_random_genome(genome_length: int,
                         codon_min: int = 0,
                         codon_max: int = 255) -> List[int]:
    """Uniform random codons in [codon_min, codon_max]."""
    return [random.randint(codon_min, codon_max) for _ in range(genome_length)]


def create_random_individual(genome_length: int,
                             codon_min: int = 0,
                             codon_max: int = 255) -> Individual:
    """Individual with a fresh random genome."""
    return Individual(
        genome=create_random_genome(genome_length, codon_min, codon_max)
    )


def init_population(size: int,
                    genome_length: int,
                    codon_min: int = 0,
                    codon_max: int = 255) -> List[Individual]:
    """Create an initial random population."""
    return [
        create_random_individual(genome_length, codon_min, codon_max)
        for _ in range(size)
    ]
