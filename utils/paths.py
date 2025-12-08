# utils/paths.py
from datetime import datetime
from pathlib import Path


def create_run_dir(base: Path | str = "runs") -> Path:
    """
    Create and return a new run directory with a timestamped name.
    Example: runs/2025-12-08_20-41-03
    """
    base_path = Path(base)
    base_path.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = base_path / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
