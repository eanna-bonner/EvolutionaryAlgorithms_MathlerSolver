# engine/mathler_engine.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from logging_config import get_logger

logger = get_logger(__name__)

# Feedback types

class TileColor(Enum):
    GRAY = auto()
    YELLOW = auto()
    GREEN = auto()

# Fast evaluation

_ALLOWED_CHARS = set("0123456789+-*/")


class ExpressionError(ValueError):
    """Expression is invalid or failed to evaluate."""


def _validate_chars(expr: str) -> None:
    if any(c not in _ALLOWED_CHARS for c in expr):
        raise ExpressionError(f"Illegal character in expression: {expr!r}")


def _validate_length(expr: str, expected_len: int) -> None:
    if len(expr) != expected_len:
        raise ExpressionError(
            f"Expression length {len(expr)} != expected {expected_len}"
        )


def safe_eval_expression(expr: str):
    """
    Fast eval for Mathler expressions.

    Assumes expr comes from our grammar and only uses digits and + - * /.
    Returns int or float. 14.0 -> 14, 14.7 stays 14.7.
    """
    try:
        value = eval(expr, {"__builtins__": None}, {})
    except ZeroDivisionError as e:
        raise ExpressionError(f"Division by zero in {expr!r}") from e
    except Exception as e:
        raise ExpressionError(f"Failed to evaluate {expr!r}: {e}") from e

    if isinstance(value, float) and value.is_integer():
        value = int(value)

    if not isinstance(value, (int, float)):
        raise ExpressionError(f"Non-numeric result {value!r} for {expr!r}")

    return value

# Feedback

def compute_feedback(guess: str, secret: str) -> List[TileColor]:
    if len(guess) != len(secret):
        raise ValueError(
            f"Guess length {len(guess)} != secret length {len(secret)}"
        )

    n = len(secret)
    feedback: List[TileColor] = [TileColor.GRAY] * n

    for i in range(n):
        g = guess[i]
        s = secret[i]
        if g == s:
            feedback[i] = TileColor.GREEN
        elif g in secret:
            feedback[i] = TileColor.YELLOW
        else:
            feedback[i] = TileColor.GRAY

    return feedback

# Game state / engine

@dataclass
class GuessResult:
    guess: str
    feedback: List[TileColor]
    value: Optional[float] = None
    is_valid: bool = False
    is_correct: bool = False
    error: Optional[str] = None


@dataclass
class MathlerGame:
    """
    Core Mathler engine:
      - fixed-length exprs (same length as secret)
      - only digits and + - * /
      - guess must evaluate to target_value to be valid
      - feedback is Wordle-style on the raw string
    """
    secret_expr: str
    target_value: float
    max_guesses: int = 6
    history: List[GuessResult] = field(default_factory=list)

    def __post_init__(self) -> None:
        try:
            _validate_chars(self.secret_expr)
            value = safe_eval_expression(self.secret_expr)
        except ExpressionError as e:
            raise ValueError(f"Invalid secret {self.secret_expr!r}: {e}") from e

        if value != self.target_value:
            raise ValueError(
                f"Secret {self.secret_expr!r} evaluates to {value}, "
                f"not target {self.target_value}"
            )

    @classmethod
    def from_secret_expr(cls, secret_expr: str, max_guesses: int = 6) -> "MathlerGame":
        value = safe_eval_expression(secret_expr)
        logger.info(
            "Creating MathlerGame from secret %s (target=%s)",
            secret_expr,
            value,
        )
        return cls(secret_expr=secret_expr, target_value=value, max_guesses=max_guesses)

    @property
    def expr_length(self) -> int:
        return len(self.secret_expr)

    def make_guess(self, guess_expr: str) -> GuessResult:
        logger.debug("Received guess: %s", guess_expr)

        # Basic checks
        try:
            _validate_length(guess_expr, self.expr_length)
            _validate_chars(guess_expr)
            value = safe_eval_expression(guess_expr)
        except ExpressionError as e:
            logger.info("Invalid guess %r: %s", guess_expr, e)
            result = GuessResult(
                guess=guess_expr,
                feedback=[],
                value=None,
                is_valid=False,
                is_correct=False,
                error=str(e),
            )
            self.history.append(result)
            return result

        # Must hit target value to be a valid Mathler guess
        if value != self.target_value:
            msg = (
                f"Guess {guess_expr!r} evaluates to {value}, "
                f"expected {self.target_value}"
            )
            logger.info(msg)
            result = GuessResult(
                guess=guess_expr,
                feedback=[],
                value=value,
                is_valid=False,
                is_correct=False,
                error=msg,
            )
            self.history.append(result)
            return result

        # Valid guess: compute feedback
        feedback = compute_feedback(guess_expr, self.secret_expr)
        is_correct = guess_expr == self.secret_expr

        result = GuessResult(
            guess=guess_expr,
            feedback=feedback,
            value=value,
            is_valid=True,
            is_correct=is_correct,
            error=None,
        )
        self.history.append(result)

        logger.info(
            "Valid guess %r (value=%s) -> feedback=%s, correct=%s",
            guess_expr,
            value,
            [c.name for c in feedback],
            is_correct,
        )

        return result

    def is_solved(self) -> bool:
        return any(r.is_correct for r in self.history)

    def guesses_remaining(self) -> int:
        return self.max_guesses - len(self.history)
