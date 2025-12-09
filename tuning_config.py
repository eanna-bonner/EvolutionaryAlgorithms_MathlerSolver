# tuning_config.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvolutionTuningRanges:
    pop_size: tuple[int, int] = (300, 1500)
    genome_length: tuple[int, int] = (10, 30)
    generations_per_guess: tuple[int, int] = (10, 50)
    mutation_rate: tuple[float, float] = (0.01, 0.3)
    crossover_rate: tuple[float, float] = (0.35, 1.0)
    elite_fraction: tuple[float, float] = (0.01, 0.15)
    mid_fraction: tuple[float, float] = (0.1, 0.5)
    tournament_size: tuple[int, int] = (2, 6)


@dataclass
class FitnessTuningRanges:
    error_tolerance: tuple[float, float] = (10.0, 100.0)
    value_weight: tuple[float, float] = (0.5, 2.0)
    green_bonus: tuple[float, float] = (2.0, 20.0)
    low_gray_bonus: tuple[float, float] = (0.1, 5.0)
    diversity_bonus_per_symbol: tuple[float, float] = (0.0, 3.0)
    diversity_min_symbols: tuple[int, int] = (3, 6)
    repeat_guess_penalty: tuple[float, float] = (10.0, 100.0)


@dataclass
class TunerConfig:
    parameter_search_strategy: str = "random"  # or "grid"
    num_trials: int = 200          # how many sampled configs to test
    games_per_trial: int = 20      # how many games per config
    max_workers: int = 14           # parallel processes

    evolution_ranges: EvolutionTuningRanges = field(default_factory=EvolutionTuningRanges)
    fitness_ranges: FitnessTuningRanges = field(default_factory=FitnessTuningRanges)


GLOBAL_TUNER_CONFIG = TunerConfig()
