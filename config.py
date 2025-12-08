# config.py
from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class EvolutionConfig:
    pop_size: int = 1000
    generations_per_guess: int = 20
    tournament_size: int = 4
    crossover_rate: float = 0.9
    mutation_rate: float = 0.1
    elite_fraction: float = 0.1        # Top 10% always kept
    mid_fraction: float = 0.3          # Next 30% maybe kept
    commutative_mutation_prob: float = 0.3


@dataclass
class FitnessConfig:
    error_tolerance: float = 0.0       # |v - target| must be <= this
    value_weight: float = 1.0          # -|v - target| * value_weight
    green_bonus: float = 20.0
    low_gray_bonus: float = 5.0
    diversity_bonus_per_symbol: float = 1.0
    diversity_min_symbols: int = 5
    hard_consistency: bool = True      # Inconsistent with history = invalid


@dataclass
class SolverConfig:
    max_guesses: int = 6
    max_expr_length: int = 6
    random_seed: Optional[int] = 42
    log_every_generation: bool = True


@dataclass
class AutoTuneConfig:
    num_games: int = 200
    extra_rounds: int = 2
    parameter_search_strategy: str = "grid"  # or "random"


@dataclass
class GlobalConfig:
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    fitness: FitnessConfig = field(default_factory=FitnessConfig)
    solver: SolverConfig = field(default_factory=SolverConfig)
    autotune: AutoTuneConfig = field(default_factory=AutoTuneConfig)


# Single global config instance for now
GLOBAL_CONFIG = GlobalConfig()


def config_to_dict() -> dict:
    """Return the current global config as a plain dict (for JSON logging)."""
    return asdict(GLOBAL_CONFIG)
