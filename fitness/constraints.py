# fitness/constraints.py
from __future__ import annotations

from typing import List, Set

from engine import GuessResult, TileColor
from engine.mathler_engine import compute_feedback


def get_forbidden_symbols(history: List[GuessResult]) -> Set[str]:
    """
    From history, collect all symbols that have ever been marked GRAY.
    With your simplified feedback, GRAY means 'not in secret at all'.
    """
    forbidden: Set[str] = set()
    for res in history:
        if not res.is_valid:
            continue
        guess = res.guess
        for i, color in enumerate(res.feedback):
            if color is TileColor.GRAY:
                forbidden.add(guess[i])
    return forbidden


def is_expr_compatible_with_history(expr: str,
                                    history: List[GuessResult]) -> bool:
    """
    Check if a candidate expression could be the secret, given past feedback.
    We simulate feedback as if 'expr' were the secret and ensure it matches
    the recorded feedback for each valid guess.
    """
    for res in history:
        if not res.is_valid:
            continue

        simulated = compute_feedback(res.guess, expr)

        if len(simulated) != len(res.feedback):
            return False

        for c1, c2 in zip(simulated, res.feedback):
            if c1 is not c2:
                return False

    return True
