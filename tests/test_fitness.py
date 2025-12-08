# tests/test_fitness.py
import pytest

from config import FitnessConfig
from engine import GuessResult, TileColor
from engine.mathler_engine import compute_feedback
from fitness import score_expression
from fitness.constraints import get_forbidden_symbols, is_expr_compatible_with_history


def make_guess_result(guess: str, feedback, is_valid: bool = True) -> GuessResult:
    """Helper to build a GuessResult quickly."""
    return GuessResult(
        guess=guess,
        feedback=list(feedback),
        value=None,
        is_valid=is_valid,
        is_correct=False,
        error=None,
    )


def base_cfg(**overrides) -> FitnessConfig:
    """Create a FitnessConfig with sensible defaults for tests."""
    cfg = FitnessConfig(
        error_tolerance=100.0,
        value_weight=1.0,
        green_bonus=0.0,
        yellow_bonus=0.0,
        diversity_bonus_per_symbol=0.0,
        diversity_min_symbols=10,
        hard_consistency=False,    # not used in current scoring
        low_gray_bonus=0.0,        # default; tests override when needed
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


# score_expression tests

def test_score_expression_closeness_empty_history():
    cfg = base_cfg()
    target = 14

    expr_good = "2+3*4"   # 14
    expr_bad = "2+2+2"    # 6

    score_good = score_expression(expr_good, target, [], cfg)
    score_bad = score_expression(expr_bad, target, [], cfg)

    assert score_good > score_bad


def test_low_gray_bonus_prefers_fewer_forbidden_symbols():
    # History: one valid guess where everything is gray
    feedback = [TileColor.GRAY] * 6
    history = [make_guess_result("1+2345", feedback)]

    # low_gray_bonus is positive so exprs that use fewer forbidden symbols get a boost
    cfg = base_cfg(low_gray_bonus=5.0)

    # Both expressions evaluate to 6, so base closeness score is equal.
    target = 6

    # Uses 3 forbidden symbols: '1', '+', '5'
    expr_more_forbidden = "1+5"     # value 6
    # Uses 1 forbidden symbol: '1'
    expr_fewer_forbidden = "6*1"    # value 6

    score_more = score_expression(expr_more_forbidden, target, history, cfg)
    score_fewer = score_expression(expr_fewer_forbidden, target, history, cfg)

    # The one with fewer forbidden symbols should score higher
    assert score_fewer > score_more


# get_forbidden_symbols tests

def test_forbidden_symbols_from_greys():
    feedback = [TileColor.GRAY] * 6
    history = [make_guess_result("1+2345", feedback)]

    forbidden = get_forbidden_symbols(history)
    # All chars in this guess should be forbidden
    assert forbidden == set("1+2345")


# is_expr_compatible_with_history tests (helper only, not used in scoring)

def test_is_expr_compatible_with_history_simple():
    secret = "2+3*4"
    guess = "3*4+2"
    feedback = compute_feedback(guess, secret)

    history = [make_guess_result(guess, feedback)]

    assert is_expr_compatible_with_history(secret, history)
    assert not is_expr_compatible_with_history("2+2+2", history)
