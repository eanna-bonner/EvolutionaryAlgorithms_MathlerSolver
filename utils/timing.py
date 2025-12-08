# utils/timing.py
import time
from contextlib import contextmanager
from logging_config import get_logger

logger = get_logger(__name__)


@contextmanager
def time_block(name: str):
    """
    Context manager to log how long a block of code takes.
    Usage:
        with time_block("evolution step"):
            ... do stuff ...
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        logger.info("%s took %.4f seconds", name, end - start)
