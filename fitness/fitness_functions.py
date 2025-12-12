# fitness/fitness_functions.py
from __future__ import annotations

from typing import List

from config import FitnessConfig
from engine import GuessResult, safe_eval_expression
from .constraints import get_forbidden_symbols, get_known_green_positions, is_expr_compatible_with_history  # still useful


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
    
    score = 0.0  # base score (shouldnt go below 0 with penalties, handy for graphing)
    # 2) Value constraint
    diff = abs(value - target_value)
    if diff > 0.0:
        score -= cfg.wrong_value_penalty
        if diff > cfg.error_tolerance:
            return float("-inf")

    # 3) Base score: closer is better
    # score -= diff * cfg.value_weight
    
    # 4) gray-based bonus (soft)
    #    Forbidden = symbols we've seen as GRAY in valid guesses.
    forbidden = get_forbidden_symbols(history)
    num_gray_used = sum(1 for s in expr if s in forbidden)
    if num_gray_used < 3:
        score += cfg.low_gray_bonus
    else:
        score -= num_gray_used * (cfg.low_gray_bonus / 2)
    
    # 5) green bonus
    greens = get_known_green_positions(history)
    if greens:
        for idx, ch in greens.items():
            if idx < len(expr) and expr[idx] == ch:
                score += cfg.green_bonus

    # 6) Diversity bonus
    unique_symbols = len(set(expr))
    for symbol in set(expr):
        if symbol in forbidden:
            unique_symbols -= 1
    score += unique_symbols * cfg.diversity_bonus_per_symbol

    # 7) Check history compatibility (hard)
    if not is_expr_compatible_with_history(expr, history):
        score -= cfg.history_incopatibility_penalty

    # 8) Check if expr was already guessed (hard)
    for res in history:
        if expr == res.guess:
            score -= cfg.repeat_guess_penalty  # heavy penalty
    return score
