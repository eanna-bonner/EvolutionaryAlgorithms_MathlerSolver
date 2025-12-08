# main.py
from pathlib import Path
import json

from config import GLOBAL_CONFIG, config_to_dict
from logging_config import setup_logging, get_logger
from utils.paths import create_run_dir
from utils.rng import seed_everything


def main() -> None:
    # 1. Create a new run directory
    run_dir: Path = create_run_dir()

    # 2. Setup logging (console + file)
    setup_logging(run_dir=run_dir)
    logger = get_logger(__name__)
    logger.info("Starting new run in %s", run_dir)

    # 3. Seed RNG
    seed_everything(GLOBAL_CONFIG.solver.random_seed)
    logger.info("Random seed set to %s",
                GLOBAL_CONFIG.solver.random_seed)

    # 4. Save current config to run directory
    config_path = run_dir / "config.json"
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config_to_dict(), f, indent=2)
    logger.info("Saved config to %s", config_path)

    # 5. Placeholder: later we will call solver/autotuner here
    logger.info("Stage 1 skeleton complete. No solver/evolution yet.")


if __name__ == "__main__":
    main()
