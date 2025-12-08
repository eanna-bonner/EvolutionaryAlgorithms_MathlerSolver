# solver/solver.py
from __future__ import annotations

from typing import List

from config import GLOBAL_CONFIG
from logging_config import get_logger
from engine import MathlerGame, GuessResult
from evolution import init_population, run_generation, Individual
from fitness import make_eval_population_mathler


logger = get_logger(__name__)


def solve_mathler_with_evolution(
    secret_expr: str,
    global_config = GLOBAL_CONFIG,
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

    # Game loop: up to max_guesses
    for guess_idx in range(game.max_guesses):
        logger.info("Guess %d / %d", guess_idx + 1, game.max_guesses)

        # Build evaluation function with current history
        eval_fn = make_eval_population_mathler(
            target_value=game.target_value,
            history=history,
            cfg=fit_cfg,
        )

        # Run several evolutionary generations before making a guess
        for gen in range(evo_cfg.generations_per_guess):
            population = run_generation(population, evo_cfg, eval_fn)

        # Ensure final population for this guess is evaluated
        eval_fn(population)

        # Pick best individual
        best = max(population, key=lambda ind: ind.fitness)
        if best.expr is None:
            # Should be rare; fall back to a no-op guess that will be invalid
            logger.warning("Best individual has no expr; using '0+0+0' as fallback")
            guess_expr = "0+0+0"  # not necessarily 6 chars, just a placeholder
        else:
            guess_expr = best.expr

        logger.info(
            "Chosen guess %r with fitness=%.3f",
            guess_expr,
            best.fitness,
        )

        # Submit guess to the game
        result = game.make_guess(guess_expr)
        history.append(result)

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

    return history
