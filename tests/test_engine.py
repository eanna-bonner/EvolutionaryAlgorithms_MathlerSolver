# tests/test_engine.py
import pytest

from engine import (
    MathlerGame,
    GuessResult,
    TileColor,
    safe_eval_expression,
)
from engine.mathler_engine import compute_feedback, ExpressionError


# ---------------------------------------------------------------------------
# safe_eval_expression tests
# ---------------------------------------------------------------------------

def test_safe_eval_simple_addition():
    assert safe_eval_expression("1+2") == 3


def test_safe_eval_precedence():
    # 2 + 3 * 4 = 14, not 20
    assert safe_eval_expression("2+3*4") == 14


def test_safe_eval_negative_numbers():
    # Unary minus
    assert safe_eval_expression("-3+5") == 2


def test_safe_eval_division_normalisation():
    # 8/4 = 2.0 -> normalised to 2
    val = safe_eval_expression("8/4")
    assert isinstance(val, int)
    assert val == 2


def test_safe_eval_division_float():
    # 3/2 = 1.5 -> stays float
    val = safe_eval_expression("3/2")
    assert isinstance(val, float)
    assert val == 1.5


def test_safe_eval_raises_on_bad_expr():
    with pytest.raises(ExpressionError):
        _ = safe_eval_expression("2+*3")  # invalid syntax


# ---------------------------------------------------------------------------
# compute_feedback tests (simplified GREY/YELLOW/GREEN logic)
# ---------------------------------------------------------------------------

def test_feedback_all_green():
    secret = "2+3*4"
    guess = "2+3*4"
    fb = compute_feedback(guess, secret)
    assert len(fb) == len(secret)
    assert all(c is TileColor.GREEN for c in fb)


def test_feedback_all_gray():
    secret = "2+3*4"
    guess = "9-9/9"  # no overlapping chars with secret
    fb = compute_feedback(guess, secret)
    assert all(c is TileColor.GRAY for c in fb)


def test_feedback_no_gray():
    secret = "2+3*4"
    guess = "4*3+2"  # same multiset of chars, all wrong positions
    fb = compute_feedback(guess, secret)
    # For our simplified logic, we at least require that
    # no position is marked GRAY since every char is in the secret.
    assert all(c is not TileColor.GRAY for c in fb)


def test_feedback_mixed_colors():
    secret = "2+3*4"
    guess = "2*3+4"  # correct first char, others present but shuffled
    fb = compute_feedback(guess, secret)
    # Position 0 should be GREEN (2)
    assert fb[0] is TileColor.GREEN
    # All others should be YELLOW in this simplified scheme
    assert all(c is not TileColor.GRAY for c in fb)


# ---------------------------------------------------------------------------
# MathlerGame tests
# ---------------------------------------------------------------------------

def test_game_from_secret_expr_sets_target_and_length():
    game = MathlerGame.from_secret_expr("2+3*4")  # 14
    assert game.target_value == 14
    assert game.expr_length == 5
    assert game.max_guesses == 6


def test_game_rejects_invalid_secret():
    # secret does not evaluate to the provided target_value (via from_secret_expr)
    with pytest.raises(ValueError):
        MathlerGame(secret_expr="2+3*", target_value=0)


def test_make_guess_invalid_length():
    game = MathlerGame.from_secret_expr("2+3*4")
    res: GuessResult = game.make_guess("2+3")  # too short
    assert res.is_valid is False
    assert res.feedback == []
    assert res.error is not None


def test_make_guess_invalid_chars():
    game = MathlerGame.from_secret_expr("2+3*4")
    res: GuessResult = game.make_guess("a+3*4")  # illegal char
    assert res.is_valid is False
    assert res.feedback == []
    assert res.error is not None


def test_make_guess_wrong_value_is_invalid():
    game = MathlerGame.from_secret_expr("2+3*4")  # target 14
    res: GuessResult = game.make_guess("2+2+2")   # 6, wrong
    assert res.is_valid is False
    assert res.is_correct is False
    assert res.feedback == []  # no feedback for invalid guesses
    assert res.value == 6
    assert "expected" in (res.error or "")


def test_make_guess_correct_value_wrong_expr():
    game = MathlerGame.from_secret_expr("2+3*4")  # target 14
    res: GuessResult = game.make_guess("3*4+2")   # also 14
    assert res.is_valid is True
    assert res.is_correct is False
    assert len(res.feedback) == game.expr_length
    # At least one position should be non-GREEN (since it's not the same string)
    assert any(c is not TileColor.GREEN for c in res.feedback)


def test_make_guess_exact_secret_wins():
    game = MathlerGame.from_secret_expr("2+3*4")
    res: GuessResult = game.make_guess("2+3*4")
    assert res.is_valid is True
    assert res.is_correct is True
    assert game.is_solved() is True
    assert game.guesses_remaining() == game.max_guesses - 1
