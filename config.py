# config.py
from dataclasses import dataclass, asdict, field
from typing import Optional
import json

best_config = json.loads(open("./tunes/best_config.json").read())

@dataclass
class EvolutionConfig:
    pop_size: int = best_config["evo_pop_size"]
    genome_length: int = best_config["evo_genome_length"]
    generations_per_guess: int = best_config["evo_generations_per_guess"]
    tournament_size: int = best_config["evo_tournament_size"]
    crossover_rate: float = best_config["evo_crossover_rate"]
    mutation_rate: float = best_config["evo_mutation_rate"]
    elite_fraction: float = best_config["evo_elite_fraction"]
    mid_fraction: float = best_config["evo_mid_fraction"]


@dataclass
class FitnessConfig:
    error_tolerance: float = best_config["fit_error_tolerance"]       # |v - target| must be <= this
    value_weight: float = best_config["fit_value_weight"]          # -|v - target| * value_weight
    green_bonus: float = best_config["fit_green_bonus"]            # per green symbol
    low_gray_bonus: float = best_config["fit_low_gray_bonus"]        # per gray symbol in lowest third
    diversity_bonus_per_symbol: float = best_config["fit_diversity_bonus_per_symbol"]
    diversity_min_symbols: int = best_config["fit_diversity_min_symbols"]
    # Inconsistent with history = invalid


@dataclass
class SolverConfig:
    max_guesses: int = 6          
    max_expr_length: int = 6
    random_seed: Optional[int] = 42
    log_every_generation: bool = True


@dataclass
class AutoTuneConfig:
    num_trials: int = 200
    games_per_trial: int = 30
    max_workers: int = 14
    parameter_search_strategy: str = "random"  # or "random"


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
