# utils/rng.py
import random
from typing import Optional


def seed_everything(seed: Optional[int]) -> None:
    """
    Seed Python's random module (and anything else later if we add it).
    If seed is None, do nothing.
    """
    if seed is None:
        return
    random.seed(seed)
