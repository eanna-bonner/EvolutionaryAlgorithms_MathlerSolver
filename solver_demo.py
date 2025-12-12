# solver_demo.py
from config import GLOBAL_CONFIG
from engine import TileColor
from logging_config import setup_logging, get_logger
from solver import solve_mathler_with_evolution
from utils.rng import seed_everything


ALLOWED_CHARS = set("0123456789+-*/")
GENOME_LENGTH = 20 


def format_feedback(feedback):
    # G = green, Y = yellow, . = gray
    return "".join(
        "G" if c is TileColor.GREEN else
        "Y" if c is TileColor.YELLOW else
        "."
        for c in feedback
    )


def prompt_secret():
    while True:
        secret = input("Enter a 6-char secret expression (digits and + - * /): ").strip()
        if len(secret) != 6:
            print("Secret must be exactly 6 characters.")
            continue
        if any(ch not in ALLOWED_CHARS for ch in secret):
            print("Secret contains invalid characters. Use only digits and + - * /.")
            continue
        return secret


def main():
    setup_logging(run_dir=None)
    logger = get_logger(__name__)

    seed_everything(GLOBAL_CONFIG.solver.random_seed)

    print("=== Mathler Evolution Demo ===")
    secret_expr = prompt_secret()

    logger.info("Running solver for secret %s", secret_expr)

    history = solve_mathler_with_evolution(
        secret_expr=secret_expr,
        global_config=GLOBAL_CONFIG,
    )

    print("\n=== Result ===")
    for i, res in enumerate(history, start=1):
        if not res.is_valid:
            print(f"{i}: {res.guess}  INVALID  ({res.error})")
        else:
            fb_str = format_feedback(res.feedback)
            print(f"{i}: {res.guess}  [{fb_str}]  valid={res.is_valid}, correct={res.is_correct}")

    if history and history[-1].is_correct:
        print(f"\nSolved in {len(history)} guesses 🎉")
    else:
        print(f"\nFailed to solve in {len(history)} guesses.")


if __name__ == "__main__":
    main()
