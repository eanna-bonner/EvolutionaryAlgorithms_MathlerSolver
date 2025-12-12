# autotune/autotuner.py
from __future__ import annotations

import copy
import csv
import json
import math
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import GLOBAL_CONFIG, EvolutionConfig, FitnessConfig
from tuning_config import GLOBAL_TUNER_CONFIG, EvolutionTuningRanges, FitnessTuningRanges
from logging_config import setup_logging, get_logger
from evolution import create_random_genome
from grammar import decode_genome_to_expr, MappingError
from engine import safe_eval_expression
from solver import solve_mathler_with_evolution
from utils.rng import seed_everything


logger = get_logger(__name__)


@dataclass
class TrialConfig:
    trial_id: int
    genome_length: int
    evolution: EvolutionConfig
    fitness: FitnessConfig


# ---------- helpers: paths / dirs ----------

def create_tune_run_dir() -> Path:
    """
    Create a timestamped directory under 'tunes/' for this autotune run.
    """
    root = Path(__file__).resolve().parent.parent
    tunes_root = root / "tunes"
    tunes_root.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = tunes_root / f"tune_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


# ---------- helpers: sampling configs ----------

def sample_int(rng: Tuple[int, int]) -> int:
    lo, hi = rng
    return random.randint(lo, hi)


def sample_float(rng: Tuple[float, float]) -> float:
    lo, hi = rng
    return random.uniform(lo, hi)


def sample_evolution_config(ranges: EvolutionTuningRanges,
                            base: EvolutionConfig,
                            genome_length_range: Tuple[int, int]) -> Tuple[EvolutionConfig, int]:
    ev = copy.deepcopy(base)

    ev.pop_size = sample_int(ranges.pop_size)
    ev.generations_per_guess = sample_int(ranges.generations_per_guess)
    ev.mutation_rate = sample_float(ranges.mutation_rate)
    ev.crossover_rate = sample_float(ranges.crossover_rate)
    ev.elite_fraction = sample_float(ranges.elite_fraction)
    ev.mid_fraction = sample_float(ranges.mid_fraction)
    ev.tournament_size = sample_int(ranges.tournament_size)

    genome_length = sample_int(genome_length_range)

    return ev, genome_length


def sample_fitness_config(ranges: FitnessTuningRanges,
                          base: FitnessConfig) -> FitnessConfig:
    ft = copy.deepcopy(base)

    ft.error_tolerance = sample_float(ranges.error_tolerance)
    ft.value_weight = sample_float(ranges.value_weight)
    ft.green_bonus = sample_float(ranges.green_bonus)
    ft.low_gray_bonus = sample_float(ranges.low_gray_bonus)
    ft.diversity_bonus_per_symbol = sample_float(ranges.diversity_bonus_per_symbol)
    ft.diversity_min_symbols = sample_int(ranges.diversity_min_symbols)
    ft.repeat_guess_penalty = sample_float(ranges.repeat_guess_penalty)

    return ft


def sample_trial_config(trial_id: int) -> TrialConfig:
    tuner = GLOBAL_TUNER_CONFIG
    evo_ranges = tuner.evolution_ranges
    fit_ranges = tuner.fitness_ranges

    base_evo = GLOBAL_CONFIG.evolution
    base_fit = GLOBAL_CONFIG.fitness

    evo_cfg, genome_length = sample_evolution_config(
        evo_ranges,
        base_evo,
        genome_length_range=evo_ranges.genome_length,
    )
    fit_cfg = sample_fitness_config(fit_ranges, base_fit)

    return TrialConfig(
        trial_id=trial_id,
        genome_length=genome_length,
        evolution=evo_cfg,
        fitness=fit_cfg,
    )


# ---------- helpers: secret generation ----------

def generate_random_secret_expr(genome_length: int, max_tries: int = 50) -> Tuple[str, float]:
    """
    Generate a random valid 6-char expression using the grammar and eval it.
    We:
      - create a random genome
      - decode to expr
      - eval to get target_value
    """
    from engine.mathler_engine import ExpressionError  # local import to avoid cycles

    for _ in range(max_tries):
        genome = create_random_genome(genome_length)
        try:
            expr = decode_genome_to_expr(genome)
        except MappingError:
            continue

        try:
            value = safe_eval_expression(expr)
        except ExpressionError:
            continue

        # Only accept expressions that are exactly 6 chars, to match game length
        if len(expr) != 6:
            continue

        return expr, value

    # As a last resort, fall back to a simple fixed expression
    return "2+3*4", safe_eval_expression("2+3*4")


# ---------- trial execution ----------

def run_single_trial(trial_cfg: TrialConfig,
                     games_per_trial: int) -> Dict[str, Any]:
    """
    Run multiple Mathler games with a single (evolution, fitness, genome_length) config.
    Returns metrics as a dict that can be logged / written to CSV.
    """
    # Each worker process gets its own seed space
    seed_everything(1234 + trial_cfg.trial_id)

    # Local copy of global config so we don't mutate GLOBAL_CONFIG
    from config import GlobalConfig  
    local_global = copy.deepcopy(GLOBAL_CONFIG)
    local_global.evolution = trial_cfg.evolution
    local_global.fitness = trial_cfg.fitness

    num_solved = 0
    num_games = games_per_trial

    guesses_list: List[int] = []
    target_values: List[float] = []

    total_game_time = 0.0

    for _ in range(num_games):
        secret_expr, target_value = generate_random_secret_expr(trial_cfg.genome_length)
        target_values.append(target_value)

        start = time.perf_counter()
        history = solve_mathler_with_evolution(
            secret_expr=secret_expr,
            global_config=local_global,
        )
        end = time.perf_counter()
        total_game_time += (end - start)

        if history and history[-1].is_correct:
            num_solved += 1
            guesses_list.append(len(history))
        else:
            guesses_list.append(local_global.solver.max_guesses + 4) # failed to solve, count as max + 4 (10 guesses)

    win_rate = num_solved / num_games if num_games > 0 else 0.0
    avg_guesses = (
        sum(guesses_list) / len(guesses_list)
        if guesses_list else local_global.solver.max_guesses + 1
    )
    median_guesses = (
        float(sorted(guesses_list)[len(guesses_list) // 2])
        if guesses_list else float(local_global.solver.max_guesses + 1)
    )
    avg_target_abs = sum(abs(v) for v in target_values) / len(target_values) if target_values else 0.0
    mean_runtime = total_game_time / num_games if num_games > 0 else 0.0

    # Simple scoring function: prioritise win_rate, then guesses
    score = win_rate * 100.0 - avg_guesses * 3.0

    evo_dict = asdict(trial_cfg.evolution)
    fit_dict = asdict(trial_cfg.fitness)

    result: Dict[str, Any] = {
        "trial_id": trial_cfg.trial_id,
        "genome_length": trial_cfg.genome_length,
        "win_rate": win_rate,
        "num_games": num_games,
        "num_solved": num_solved,
        "avg_guesses_solved": avg_guesses,
        "median_guesses_solved": median_guesses,
        "avg_target_abs": avg_target_abs,
        "mean_runtime_sec": mean_runtime,
        "total_runtime_sec": total_game_time,
        "score": score,
    }

    # Flatten evolution and fitness params into the result with prefixes
    for k, v in evo_dict.items():
        result[f"evo_{k}"] = v
    for k, v in fit_dict.items():
        result[f"fit_{k}"] = v

    return result


# ---------- main autotune orchestration ----------

def run_autotune() -> None:
    tuner_cfg = GLOBAL_TUNER_CONFIG

    tune_dir = create_tune_run_dir()
    setup_logging(run_dir=tune_dir)
    global logger
    logger = get_logger(__name__)

    logger.info("Starting autotune run in %s", tune_dir)
    logger.info("Search strategy: %s", tuner_cfg.parameter_search_strategy)
    logger.info("Trials: %d, games_per_trial: %d, max_workers: %d",
                tuner_cfg.num_trials, tuner_cfg.games_per_trial, tuner_cfg.max_workers)

    trials_csv_path = tune_dir / "trials.csv"
    best_config_path = tune_dir / "best_config.json"

    # Prepare CSV
    fieldnames: List[str] = [
        "trial_id",
        "genome_length",
        "win_rate",
        "num_games",
        "num_solved",
        "avg_guesses_solved",
        "median_guesses_solved",
        "avg_target_abs",
        "mean_runtime_sec",
        "total_runtime_sec",
        "score",
    ]

    # We need to add evo_*/fit_* fields dynamically from one sample
    sample_trial = sample_trial_config(0)
    evo_keys = asdict(sample_trial.evolution).keys()
    fit_keys = asdict(sample_trial.fitness).keys()
    fieldnames.extend([f"evo_{k}" for k in evo_keys])
    fieldnames.extend([f"fit_{k}" for k in fit_keys])

    # Set up workers
    results: List[Dict[str, Any]] = []
    best_result: Dict[str, Any] | None = None

    with trials_csv_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        with ProcessPoolExecutor(max_workers=tuner_cfg.max_workers) as executor:
            futures = {}

            for trial_id in range(tuner_cfg.num_trials):
                trial_cfg = sample_trial_config(trial_id)
                fut = executor.submit(run_single_trial, trial_cfg, tuner_cfg.games_per_trial)
                futures[fut] = trial_cfg

            for fut in as_completed(futures):
                trial_cfg = futures[fut]
                try:
                    result = fut.result()
                except Exception as e:
                    logger.exception("Trial %d failed with error: %s", trial_cfg.trial_id, e)
                    continue

                results.append(result)
                writer.writerow(result)
                csvfile.flush()

                logger.info(
                    "Trial %3d: win_rate=%.2f, avg_guesses=%.2f, score=%.2f, pop=%d, genome=%d",
                    result["trial_id"],
                    result["win_rate"],
                    result["avg_guesses_solved"],
                    result["score"],
                    result["evo_pop_size"],
                    result["genome_length"],
                )

                if best_result is None or result["score"] > best_result["score"]:
                    best_result = result
                    logger.info(
                        "New best trial: %d (score=%.2f, win_rate=%.2f, avg_guesses=%.2f)",
                        result["trial_id"],
                        result["score"],
                        result["win_rate"],
                        result["avg_guesses_solved"],
                    )
                    # Write best config to JSON
                    with best_config_path.open("w") as f:
                        json.dump(best_result, f, indent=2)

    logger.info("Autotune run complete. Results in %s", tune_dir)
