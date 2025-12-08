# logging_config.py
import logging
from pathlib import Path
from typing import Optional

DEFAULT_LOG_LEVEL = logging.INFO


def setup_logging(run_dir: Optional[Path] = None,
                  level: int = DEFAULT_LOG_LEVEL) -> None:
    """
    Configure the root logger with a console handler and,
    if run_dir is provided, a file handler writing to train.log.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers (useful if re-running in a REPL / notebook)
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if run_dir is not None:
        run_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(run_dir / "train.log",
                                           mode="w",
                                           encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Convenience helper to get a module-specific logger."""
    return logging.getLogger(name)
