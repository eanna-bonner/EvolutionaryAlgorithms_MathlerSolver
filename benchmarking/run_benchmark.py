# benchmarking/run_benchmark.py
from __future__ import annotations

import argparse
import random
from typing import Tuple
import time
from benchmarking.metrics_recorder import MetricsRecorder
from grammar import decode_genome_to_expr, MappingError
from engine.mathler_engine import safe_eval_expression
from solver import solve_mathler_with_evolution

def generate_secret(
    *,
    rng: random.Random,
    codon_len: int = 32,
    max_tries: int = 2000,
) -> Tuple[str, float]:
    """
    Generate a secret by sampling a random genome, decoding it to an expression,
    and evaluating it to get a target value.

    This deliberately uses the project's GE decoder so benchmarking stays modular
    across grammars.
    """
    for _ in range(max_tries):
        genome = [rng.randint(0, 255) for _ in range(codon_len)]
        try:
            expr = decode_genome_to_expr(genome)
        except MappingError:
            continue

        # Filter out expressions that don't evaluate cleanly (div0, etc.)
        try:
            value = float(safe_eval_expression(expr))
        except Exception:
            continue

        return expr, value

    raise RuntimeError(
        f"Failed to generate a valid secret after {max_tries} attempts "
        f"(codon_len={codon_len}). Try increasing codon_len or max_tries."
    )



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=100, help="Number of games to run")
    ap.add_argument("--seed", type=int, default=12345, help="Base RNG seed for reproducibility")
    ap.add_argument("--tag", type=str, default="", help="Optional tag appended to run directory name")
    ap.add_argument("--save-secrets", action="store_true", help="Include secret expressions in games.csv")
    ap.add_argument("--print-every", type=int, default=1, help="Print a summary every N games")
    args = ap.parse_args()

    recorder = MetricsRecorder(run_tag=args.tag, save_secrets=args.save_secrets)

    base_seed = int(args.seed)
    n_games = int(args.games)

    print(f"Benchmark run_id: {recorder.run_id}")
    print(f"Output dir: {recorder.run_dir}")
    print(f"Games: {n_games}, base_seed: {base_seed}, print_every: {args.print_every}")
    print("-" * 60)

    t_run0 = time.perf_counter()
    solved_count = 0
    crashed_count = 0

    for game_id in range(n_games):
        t_game0 = time.perf_counter()

        game_seed = base_seed + game_id
        game_rng = random.Random(game_seed)

        recorder.set_game_context(game_id=game_id, seed=game_seed)

        # Generate secret (show progress if this ever becomes the bottleneck)
        secret_expr, target_value = generate_secret(rng=game_rng, codon_len=32, max_tries=2000)

        if args.save_secrets:
            print(f"[Game {game_id+1:>3}/{n_games}] seed={game_seed} secret={secret_expr} target={target_value}")
        else:
            print(f"[Game {game_id+1:>3}/{n_games}] seed={game_seed} target={target_value}")

        try:
            history = solve_mathler_with_evolution(secret_expr, metrics=recorder)

            # Determine solved + guesses
            num_guesses = len(history) if history else 0
            solved = 0
            if history:
                for r in history:
                    g = getattr(r, "guess", None) or getattr(r, "guess_expr", None)
                    if g == secret_expr:
                        solved = 1
                        break


            solved_count += solved
            game_time = time.perf_counter() - t_game0

            # Print summary every N games (default 1 = every game)
            if (game_id + 1) % args.print_every == 0:
                run_time = time.perf_counter() - t_run0
                rate = solved_count / (game_id + 1)
                print(
                    f"  -> solved={bool(solved)} guesses={num_guesses} "
                    f"game_time={game_time:.2f}s | "
                    f"running_solve_rate={rate:.2%} total_time={run_time:.1f}s"
                )
                print("-" * 60)

        except Exception as e:
            crashed_count += 1
            game_time = time.perf_counter() - t_game0
            print(f"  -> ERROR after {game_time:.2f}s: {e!r}")
            print("-" * 60)
            continue

    recorder.write_all()
    total_time = time.perf_counter() - t_run0
    print(f"Finished {n_games} games in {total_time:.1f}s")
    print(f"Solved: {solved_count}/{n_games} ({(solved_count/n_games if n_games else 0):.2%})")
    print(f"Crashed: {crashed_count}/{n_games} ({(crashed_count/n_games if n_games else 0):.2%})")
    print(f"Wrote benchmark results to: {recorder.run_dir}")


if __name__ == "__main__":
    main()
