# grammar/grammar_defs.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set

from .bnf_loader import load_bnf, is_nonterminal  # re-export helper

# Locate the BNF file in the same directory
_THIS_DIR = Path(__file__).resolve().parent
_BNF_FILE = _THIS_DIR / "mathler_expr6.bnf"

# Load at import time
START_SYMBOL, GRAMMAR, TERMINALS = load_bnf(_BNF_FILE)

__all__ = [
    "START_SYMBOL",
    "GRAMMAR",
    "TERMINALS",
    "is_nonterminal",
]
