# fitness/fitness_functions.py
from __future__ import annotations

from typing import List

from config import FitnessConfig
from engine import GuessResult, safe_eval_expression
from .constraints import get_forbidden_symbols, get_known_green_positions  # still useful


def score_expression(expr: str,
                     target_value: float,
                     history: List[GuessResult],
                     cfg: FitnessConfig) -> float:
    """
    Score a single expression.

    Hard constraints:
      - must eval successfully
      - |value - target| <= error_tolerance

    Soft terms:
      - closer to target is better
      - bonus for using fewer 'gray' symbols from history
      - diversity bonus for many unique symbols
    """
    # 1) Evaluate
    try:
        value = safe_eval_expression(expr)
    except Exception:
        return float("-inf")

    # 2) Value constraint
    diff = abs(value - target_value)
    if diff > cfg.error_tolerance:
        return float("-inf")

    # 3) Base score: closer is better
    score = -diff * cfg.value_weight

    # 4) gray-based bonus (soft)
    #    Forbidden = symbols we've seen as GRAY in valid guesses.
    forbidden = get_forbidden_symbols(history)
    num_gray_used = sum(1 for s in expr if s in forbidden)
    if num_gray_used < 3:
        score += cfg.low_gray_bonus
    
    # 5) green bonus
    greens = get_known_green_positions(history)
    if greens:
        for idx, ch in greens.items():
            if idx < len(expr) and expr[idx] == ch:
                score += cfg.green_bonus

    # 6) Diversity bonus
    unique_symbols = len(set(expr))
    if unique_symbols >= cfg.diversity_min_symbols:
        extra = unique_symbols - cfg.diversity_min_symbols + 1
        score += extra * cfg.diversity_bonus_per_symbol

    return score
