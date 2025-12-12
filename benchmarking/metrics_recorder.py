# benchmarking/metrics_recorder.py
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _safe_json(obj: Any) -> Any:
    """
    Best-effort JSON serializer for config objects.
    - dict/list/str/int/float/bool/None: unchanged
    - dataclass: asdict
    - objects with __dict__: vars(obj)
    - fallback: str(obj)
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_safe_json(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _safe_json(v) for k, v in obj.items()}

    # dataclass support
    try:
        return asdict(obj)  # type: ignore[arg-type]
    except Exception:
        pass

    # object __dict__ support
    try:
        return {k: _safe_json(v) for k, v in vars(obj).items()}
    except Exception:
        return str(obj)


def _now_stamp() -> str:
    # Example: 20251212_142233
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@dataclass
class GameRow:
    run_id: str
    game_id: int
    seed: int
    secret_expr: str
    target_value: float
    success: int
    num_guesses: int
    total_runtime_s: float
    avg_runtime_per_guess_s: float
    invalid_guess_count: int


@dataclass
class GuessRow:
    run_id: str
    game_id: int
    guess_index: int
    guess_expr: str
    guess_valid: int
    guess_runtime_s: float
    guess_fitness: float
    # Optional: store feedback as a compact string if available
    feedback: str


@dataclass
class GenerationRow:
    run_id: str
    game_id: int
    guess_index: int
    generation_index: int
    gen_runtime_s: float
    fitness_mean: float
    fitness_max: float
    fitness_min: float
    fitness_std: float


class MetricsRecorder:
    """
    Collects metrics during solve runs and writes:
      - games.csv
      - guesses.csv
      - generations.csv
      - config.json
    into benchmarking/results/run_<timestamp>_<tag>/
    """

    def __init__(
        self,
        results_root: str | Path = "benchmarking/results",
        run_tag: str = "",
        save_secrets: bool = True,
    ) -> None:
        self.results_root = Path(results_root)
        self.run_id = f"run_{_now_stamp()}" + (f"_{run_tag}" if run_tag else "")
        self.run_dir = self.results_root / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.save_secrets = save_secrets

        self._games: List[GameRow] = []
        self._guesses: List[GuessRow] = []
        self._generations: List[GenerationRow] = []

        # per-game state
        self._game_id: Optional[int] = None
        self._seed: Optional[int] = None
        self._secret_expr: Optional[str] = None
        self._target_value: Optional[float] = None
        self._invalid_guess_count: int = 0

    # -----------------------------
    # Lifecycle hooks (called by solver/evolution)
    # -----------------------------

    def on_game_start(
        self,
        *,
        secret_expr: str,
        target_value: float,
        max_guesses: int,
        evo_cfg: Any,
        fit_cfg: Any,
    ) -> None:
        # This will be called once per game by solve_mathler_with_evolution()
        # game_id/seed are set by the benchmark runner before calling solve
        self._secret_expr = secret_expr
        self._target_value = float(target_value)
        self._invalid_guess_count = 0

        # Save config once (first game only) OR overwrite each time (fine too).
        # We'll write it every time but same path; last write wins, identical for run.
        cfg_payload = {
            "run_id": self.run_id,
            "max_guesses": max_guesses,
            "evolution_config": _safe_json(evo_cfg),
            "fitness_config": _safe_json(fit_cfg),
            "env": {
                "cwd": os.getcwd(),
            },
        }
        (self.run_dir / "config.json").write_text(json.dumps(cfg_payload, indent=2), encoding="utf-8")

    def on_guess_start(self, *, guess_idx: int, history: Any) -> None:
        # We don’t need to store anything at start right now, but hook exists.
        pass

    def on_generation_end(
        self,
        *,
        guess_idx: int | None,
        gen_idx: int | None,
        gen_runtime_s: float,
        population: Any,
        fitness_mean: float,
        fitness_max: float,
        fitness_min: float,
        fitness_std: float,
    ) -> None:
        if self._game_id is None:
            return
        if guess_idx is None or gen_idx is None:
            return

        self._generations.append(
            GenerationRow(
                run_id=self.run_id,
                game_id=self._game_id,
                guess_index=int(guess_idx),
                generation_index=int(gen_idx),
                gen_runtime_s=float(gen_runtime_s),
                fitness_mean=float(fitness_mean),
                fitness_max=float(fitness_max),
                fitness_min=float(fitness_min),
                fitness_std=float(fitness_std),
            )
        )

    def on_guess_end(
        self,
        *,
        guess_idx: int,
        guess_expr: str,
        guess_fitness: float,
        result: Any,
        guess_runtime_s: float,
        population: Any,
    ) -> None:
        if self._game_id is None:
            return

        # result is expected to look like GuessResult (has is_valid + feedback fields)
        guess_valid = int(getattr(result, "is_valid", False))
        if guess_valid == 0:
            self._invalid_guess_count += 1

        feedback = ""
        fb = getattr(result, "feedback", None)
        if fb:
            # feedback appears to be a list[str] like ["GREEN","GRAY",...]
            # store compactly as G/Y/X
            mapping = {"GREEN": "G", "YELLOW": "Y", "GRAY": "X"}
            try:
                feedback = "".join(mapping.get(x, "?") for x in fb)
            except Exception:
                feedback = str(fb)

        self._guesses.append(
            GuessRow(
                run_id=self.run_id,
                game_id=self._game_id,
                guess_index=int(guess_idx),
                guess_expr=str(guess_expr),
                guess_valid=guess_valid,
                guess_runtime_s=float(guess_runtime_s),
                guess_fitness=float(guess_fitness),
                feedback=feedback,
            )
        )

    def on_game_end(self, *, history: Any, total_runtime_s: float) -> None:
        """
        Called once per game at the end of solve_mathler_with_evolution().
        Creates a games.csv row for the current game_id.
        """
        if self._game_id is None or self._seed is None:
            return
        secret_expr = self._secret_expr if self.save_secrets else ""
        num_guesses = len(history) if history is not None else 0
        success = 0
        if history:
                for r in history:
                    g = getattr(r, "guess", None) or getattr(r, "guess_expr", None)
                    if g == secret_expr:
                        success = 1
                        break

        avg_runtime_per_guess = (float(total_runtime_s) / num_guesses) if num_guesses > 0 else float(total_runtime_s)

        
        target_val = float(self._target_value) if self._target_value is not None else 0.0

        self._games.append(
            GameRow(
                run_id=self.run_id,
                game_id=self._game_id,
                seed=int(self._seed),
                secret_expr=secret_expr,
                target_value=target_val,
                success=success,
                num_guesses=int(num_guesses),
                total_runtime_s=float(total_runtime_s),
                avg_runtime_per_guess_s=float(avg_runtime_per_guess),
                invalid_guess_count=int(self._invalid_guess_count),
            )
        )

    # -----------------------------
    # Benchmark runner helpers
    # -----------------------------

    def set_game_context(self, *, game_id: int, seed: int) -> None:
        """
        Called by the benchmark runner before each solve.
        """
        self._game_id = int(game_id)
        self._seed = int(seed)

    def write_all(self) -> None:
        """
        Writes games.csv, guesses.csv, generations.csv into run directory.
        """
        self._write_csv(self.run_dir / "games.csv", self._games)
        self._write_csv(self.run_dir / "guesses.csv", self._guesses)
        self._write_csv(self.run_dir / "generations.csv", self._generations)

    @staticmethod
    def _write_csv(path: Path, rows: List[Any]) -> None:
        if not rows:
            # still create an empty file with header if possible
            path.write_text("", encoding="utf-8")
            return

        dict_rows = [asdict(r) for r in rows]
        fieldnames = list(dict_rows[0].keys())

        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(dict_rows)
