# solver/solver.py
from __future__ import annotations

from typing import List

from config import GLOBAL_CONFIG
from logging_config import get_logger
from engine import MathlerGame, GuessResult
from evolution import init_population, run_generation, Individual, sort_by_fitness
from fitness import make_eval_population_mathler
import time

logger = get_logger(__name__)


def solve_mathler_with_evolution(
    secret_expr: str,
    global_config = GLOBAL_CONFIG,
    metrics = None,
) -> List[GuessResult]:
    """
    Solve a single Mathler game using evolutionary search.

    Steps:
      - Create a MathlerGame from the secret expression.
      - Initialise a random population of genomes.
      - For each guess:
          * build an eval_fn using current target_value and history
          * run evolution for evolution.generations_per_guess
          * pick best expr as next guess
          * submit guess to the game and update history
      - Return the full list of GuessResult objects.
    """
    # Set up game
    game = MathlerGame.from_secret_expr(secret_expr, max_guesses=global_config.solver.max_guesses)
    history: List[GuessResult] = []

    evo_cfg = global_config.evolution
    fit_cfg = global_config.fitness

    # Initial random population
    population: List[Individual] = init_population(
        size=evo_cfg.pop_size,
        genome_length=evo_cfg.genome_length,
    )

    logger.info(
        "Starting evolutionary solve for secret=%s (target=%s)",
        secret_expr,
        game.target_value,
    )

    if metrics is not None:
        metrics.on_game_start(
            secret_expr=secret_expr,
            target_value=game.target_value,
            max_guesses=game.max_guesses,
            evo_cfg=evo_cfg,
            fit_cfg=fit_cfg,
        )

    t_game0 = time.perf_counter()


    # Game loop: up to max_guesses
    for guess_idx in range(game.max_guesses):
        logger.info("Guess %d / %d", guess_idx + 1, game.max_guesses)

        t_guess0 = time.perf_counter()
        if metrics is not None:
            metrics.on_guess_start(guess_idx=guess_idx, history=history)

        # Build evaluation function with current history
        eval_fn = make_eval_population_mathler(
            target_value=game.target_value,
            history=history,
            cfg=fit_cfg,
        )

        # Run several evolutionary generations before making a guess
        for gen in range(evo_cfg.generations_per_guess):
            population = run_generation(
                population,
                evo_cfg,
                eval_fn,
                guess_idx=guess_idx,
                gen_idx=gen,
                metrics=metrics,
            )


        # Ensure final population for this guess is evaluated
        eval_fn(population)

        # Find last valid guess (if any)
        last_valid_guess = None
        for res in reversed(history):
            if res.is_valid:
                last_valid_guess = res.guess
                break

        # Sort population by fitness (best first)
        ranked = sort_by_fitness(population)

        # Try the top 5, skipping any that repeat the last valid guess
        candidate = None
        for ind in ranked[:5]:
            if ind.expr is None:
                continue
            if last_valid_guess is not None and ind.expr == last_valid_guess:
                continue
            candidate = ind
            break

        # Fallback: if no suitable candidate found, use the best anyway
        if candidate is None:
            candidate = ranked[0]

        best = candidate
        guess_expr = best.expr if best.expr is not None else "0+0+0"

        logger.info(
            "Chosen guess %r with fitness=%.3f (last_valid_guess=%r)",
            guess_expr,
            best.fitness,
            last_valid_guess,
        )

        # Submit guess to the game
        result = game.make_guess(guess_expr)
        history.append(result)

        guess_runtime_s = time.perf_counter() - t_guess0
        if metrics is not None:
            metrics.on_guess_end(
                guess_idx=guess_idx,
                guess_expr=guess_expr,
                guess_fitness=best.fitness,
                result=result,
                guess_runtime_s=guess_runtime_s,
                population=population,
            )


        logger.info(
            "Guess result: valid=%s, correct=%s, feedback=%s",
            result.is_valid,
            result.is_correct,
            [c.name for c in result.feedback] if result.feedback else [],
        )

        if result.is_correct:
            logger.info("Solved in %d guesses", len(history))
            break

    if not game.is_solved():
        logger.info("Failed to solve within %d guesses", game.max_guesses)

    total_runtime_s = time.perf_counter() - t_game0
    if metrics is not None:
        metrics.on_game_end(history=history, total_runtime_s=total_runtime_s)


    return history
