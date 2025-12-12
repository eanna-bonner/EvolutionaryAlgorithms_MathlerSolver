# grammar/bnf_loader.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple


def is_nonterminal(symbol: str) -> bool:
    return symbol.startswith("<") and symbol.endswith(">")


def _parse_alt(
    alt: str,
    terminals: Set[str],
) -> List[str]:
    """
    Parse a single alternative string like:
        '<int1> <addmul_op> <int2>'
        '"+"'
    into a list of symbols, updating `terminals` set for literals.
    """
    alt = alt.strip()
    if alt == "" or alt.lower() == "epsilon":
        # epsilon / empty production
        return []

    tokens = alt.split()
    symbols: List[str] = []
    for tok in tokens:
        tok = tok.strip()
        if tok.startswith('"') and tok.endswith('"'):
            # terminal literal
            sym = tok[1:-1]
            symbols.append(sym)
            terminals.add(sym)
        else:
            # assume nonterminal
            symbols.append(tok)
    return symbols


def load_bnf(path: str | Path) -> Tuple[str, Dict[str, List[List[str]]], Set[str]]:
    """
    Load a simple BNF file and return (START_SYMBOL, GRAMMAR, TERMINALS).

    Supported syntax:
      - %start <symbol>
      - <lhs> ::= rhs1 | rhs2 | ...
      - continuation lines:
            | rhs3
            | rhs4 | rhs5
      - terminals: "x"
      - nonterminals: <name>
      - comments: lines starting with '#'
      - epsilon (empty) productions: 'epsilon' or a blank alternative
    """
    path = Path(path)
    grammar: Dict[str, List[List[str]]] = {}
    terminals: Set[str] = set()
    start_symbol: str | None = None

    current_lhs: str | None = None  # last LHS we saw with '::='

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            stripped = raw_line.strip()

            # Skip empty lines / comments
            if not stripped or stripped.startswith("#"):
                continue

            # %start directive
            if stripped.startswith("%start"):
                parts = stripped.split(None, 1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid %start line: {raw_line!r}")
                start_symbol = parts[1].strip()
                continue

            # Continuation line for the previous LHS:
            #   | <alt1> | <alt2>
            if stripped.startswith("|"):
                if current_lhs is None:
                    raise ValueError(
                        f"Continuation line without previous LHS: {raw_line!r}"
                    )

                rhs_part = stripped[1:].strip()  # drop leading '|'
                alt_strings = [alt.strip() for alt in rhs_part.split("|")]

                for alt in alt_strings:
                    symbols = _parse_alt(alt, terminals)
                    grammar[current_lhs].append(symbols)
                continue

            # New production line with '::='
            if "::=" in stripped:
                lhs_part, rhs_part = stripped.split("::=", 1)
                lhs = lhs_part.strip()
                if not is_nonterminal(lhs):
                    raise ValueError(f"LHS is not a nonterminal: {lhs!r}")

                current_lhs = lhs  # remember for continuation lines

                alt_strings = [alt.strip() for alt in rhs_part.split("|")]
                prods: List[List[str]] = []
                for alt in alt_strings:
                    symbols = _parse_alt(alt, terminals)
                    prods.append(symbols)

                if lhs in grammar:
                    grammar[lhs].extend(prods)
                else:
                    grammar[lhs] = prods
                continue

            # Anything else is invalid
            raise ValueError(f"Invalid BNF line (no '::=' or leading '|'): {raw_line!r}")

    if start_symbol is None:
        # Fallback if %start is omitted
        if "<expr6>" in grammar:
            start_symbol = "<expr6>"
        else:
            raise ValueError("No %start directive and no <expr6> nonterminal in grammar.")

    return start_symbol, grammar, terminals
