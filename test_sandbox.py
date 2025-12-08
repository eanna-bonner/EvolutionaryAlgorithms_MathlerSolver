# test_sandbox.py
from config import GLOBAL_CONFIG
from engine import MathlerGame
from evolution.genome import init_population
from evolution.evolution_loop import run_generation
from fitness import make_eval_population_mathler
from logging_config import setup_logging, get_logger
from utils.rng import seed_everything


def main() -> None:
    # Console-only logging for this sandbox
    setup_logging(run_dir=None)
    logger = get_logger(__name__)

    # Seed for reproducibility
    seed_everything(GLOBAL_CONFIG.solver.random_seed)

    # Simple test game: secret "2+3*4" => target 14
    game = MathlerGame.from_secret_expr("2+3*4")
    target_value = game.target_value
    history = []  # no guesses yet

    evo_cfg = GLOBAL_CONFIG.evolution
    fit_cfg = GLOBAL_CONFIG.fitness

    # Loosen fitness a bit so not everything is -inf in this sandbox
    fit_cfg.error_tolerance = 100.0
    fit_cfg.low_gray_bonus = 0.0
    fit_cfg.green_bonus = 0.0

    eval_fn = make_eval_population_mathler(
        target_value=target_value,
        history=history,
        cfg=fit_cfg,
    )

    genome_length = 20
    population = init_population(
        size=evo_cfg.pop_size,
        genome_length=genome_length,
    )

    logger.info("Starting sandbox evolution run")
    logger.info("Pop size=%d, genome_length=%d", len(population), genome_length)

    num_generations = 5
    for gen in range(num_generations):
        population = run_generation(population, evo_cfg, eval_fn)

        # run_generation already called eval_fn, so fitness is up to date
        best = max(population, key=lambda ind: ind.fitness)
        logger.info(
            "Gen %d: best fitness=%.3f, expr=%s",
            gen,
            best.fitness,
            best.expr,
        )


if __name__ == "__main__":
    main()
