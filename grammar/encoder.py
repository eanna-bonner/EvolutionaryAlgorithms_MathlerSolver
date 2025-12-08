# grammar/encoder.py
from __future__ import annotations

from typing import List, Tuple

from engine import safe_eval_expression
from .grammar_defs import GRAMMAR, START_SYMBOL, is_nonterminal, TERMINALS


class EncodingError(ValueError):
    """Failed to encode expression into a genome."""

# Recursive descent parser to recover the leftmost derivation

def _parse_symbol(symbol: str, expr: str, pos: int) -> Tuple[bool, int, List[Tuple[str, int]]]:
    """
    Try to parse `expr` starting at `pos` according to `symbol`.

    Returns (success, new_pos, choices), where:
      - success: True / False
      - new_pos: index in expr after parsing this symbol
      - choices: list of (nonterminal, production_index) used in this subtree,
                 in the order they would be consumed by the decoder (leftmost).
    """
    # Terminal: single character like "1", "+", "-", etc.
    if not is_nonterminal(symbol):
        if pos >= len(expr) or expr[pos] != symbol:
            return False, pos, []
        return True, pos + 1, []

    # Nonterminal: try each production in order
    productions = GRAMMAR.get(symbol)
    if not productions:
        return False, pos, []

    for prod_idx, prod in enumerate(productions):
        cur_pos = pos
        choices: List[Tuple[str, int]] = [(symbol, prod_idx)]  # record this expansion first

        ok = True
        for child_sym in prod:
            child_ok, cur_pos, child_choices = _parse_symbol(child_sym, expr, cur_pos)
            if not child_ok:
                ok = False
                break
            choices.extend(child_choices)

        if ok:
            return True, cur_pos, choices

    # No production matched
    return False, pos, []



# Public encoder: expr -> genome


def encode_expr_to_genome(expr: str, genome_length: int = 20) -> List[int]:
    """
    Encode a 6-char expression into a genome such that:

        decode_genome_to_expr(genome) == expr

    assuming `expr` is in the language of the grammar.

    Steps:
      - Check length and characters.
      - Check it evaluates at all.
      - Parse via leftmost derivation from <expr6>.
      - For each (nonterminal, production_index), choose codon = production_index.
      - Pad or repeat codons to reach genome_length.
    """
    if len(expr) != 6:
        raise EncodingError(f"Expression {expr!r} is not 6 characters")

    if any(c not in TERMINALS for c in expr):
        raise EncodingError(f"Expression {expr!r} contains illegal characters")

    # Ensure it's at least syntactically/evaluationally sane
    _ = safe_eval_expression(expr)

    success, end_pos, choices = _parse_symbol(START_SYMBOL, expr, 0)
    if not success or end_pos != len(expr):
        raise EncodingError(
            f"Expression {expr!r} is not derivable from the grammar "
            f"(success={success}, end_pos={end_pos})"
        )

    # choices is a list of (nonterminal, prod_idx) in the order the decoder will consume them
    codons: List[int] = []
    for nonterm, prod_idx in choices:
        num_prods = len(GRAMMAR[nonterm])
        if not (0 <= prod_idx < num_prods):
            raise EncodingError(
                f"Internal error: production index {prod_idx} out of range for {nonterm}"
            )
        # Decoder uses codon % num_prods, so codon = prod_idx is enough
        codons.append(prod_idx)

    if not codons:
        raise EncodingError(f"No productions recorded while encoding {expr!r}")

    # Adjust length: repeat or truncate to get exactly genome_length codons
    if len(codons) >= genome_length:
        return codons[:genome_length]

    # Repeat pattern to fill
    full_codons: List[int] = []
    while len(full_codons) < genome_length:
        remaining = genome_length - len(full_codons)
        full_codons.extend(codons[:remaining])

    return full_codons
