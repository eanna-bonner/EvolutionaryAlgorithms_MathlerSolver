# grammar/grammar_defs.py
from __future__ import annotations

from typing import Dict, List

# Nonterminals are written as "<name>"
START_SYMBOL = "<expr6>"

# Terminals are literal characters "0".."9", "+", "-", "*", "/"
TERMINALS = set("0123456789+-*/")


def is_nonterminal(symbol: str) -> bool:
    return symbol.startswith("<") and symbol.endswith(">")


# Grammar as: nonterminal -> list of productions,
# each production is a list of symbols (terminals or nonterminals).

GRAMMAR: Dict[str, List[List[str]]] = {
    # Top-level
    "<expr6>": [
        ["<int6>"],
        ["<bin_expr6>"],
        ["<tri_expr6>"],
    ],

    # Operators
    "<op>": [["<addmul_op>"], ["<div_op>"]],
    "<addmul_op>": [["+"] , ["-"], ["*"]],
    "<div_op>": [["/"]],

    # 1-operator expressions (total length 6)
    # Patterns (len(A), len(B)) = (1,4), (2,3), (3,2), (4,1)
    "<bin_expr6>": [
        ["<int1>", "<op>",        "<int4>"],
        ["<int2>", "<op>",        "<int3>"],
        ["<int3>", "<op>",        "<int2>"],
        ["<int4>", "<addmul_op>", "<int1>"],
        ["<int4>", "<div_op>",    "<nz_int1>"],
    ],

    # 2-operator expressions (total length 6)
    "<tri_expr6>": [
        ["<tri_expr6_112>"],
        ["<tri_expr6_121>"],
        ["<tri_expr6_211>"],
    ],

    # Pattern (1,1,2): A=int1, B=int1, C=int2
    "<tri_expr6_112>": [
        ["<int1>", "<addmul_op>", "<int1>",    "<op>", "<int2>"],
        ["<int1>", "<div_op>",    "<nz_int1>", "<op>", "<int2>"],
    ],

    # Pattern (1,2,1): A=int1, B=int2, C=int1
    "<tri_expr6_121>": [
        ["<int1>", "<op>", "<int2>", "<addmul_op>", "<int1>"],
        ["<int1>", "<op>", "<int2>", "<div_op>",    "<nz_int1>"],
    ],

    # Pattern (2,1,1): A=int2, B=int1, C=int1
    "<tri_expr6_211>": [
        ["<int2>", "<addmul_op>", "<int1>",    "<addmul_op>", "<int1>"],
        ["<int2>", "<div_op>",    "<nz_int1>", "<addmul_op>", "<int1>"],
        ["<int2>", "<addmul_op>", "<int1>",    "<div_op>",    "<nz_int1>"],
        ["<int2>", "<div_op>",    "<nz_int1>", "<div_op>",    "<nz_int1>"],
    ],

    # Digits
    "<digit>": [["0"], ["<nonzero_digit>"]],
    "<nonzero_digit>": [
        ["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"], ["8"], ["9"],
    ],

    # Integers by length
    # Length 1
    "<int1>": [["0"], ["<nonzero_digit>"]],
    "<nz_int1>": [["<nonzero_digit>"]],

    # Length 2: 10–99 or -1..-9
    "<int2>": [
        ["<nonzero_digit>", "<digit>"],
        ["-", "<nonzero_digit>"],
    ],

    # Length 3: 100–999 or -10..-99
    "<int3>": [
        ["<nonzero_digit>", "<digit>", "<digit>"],
        ["-", "<nonzero_digit>", "<digit>"],
    ],

    # Length 4: 1000–9999 or -100..-999
    "<int4>": [
        ["<nonzero_digit>", "<digit>", "<digit>", "<digit>"],
        ["-", "<nonzero_digit>", "<digit>", "<digit>"],
    ],

    # Length 6: full expression may just be an integer
    "<int6>": [
        ["<nonzero_digit>", "<digit>", "<digit>", "<digit>", "<digit>", "<digit>"],
        ["-", "<nonzero_digit>", "<digit>", "<digit>", "<digit>", "<digit>"],
    ],
}

