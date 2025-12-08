# grammar/decoder.py
from __future__ import annotations

from typing import List

from .grammar_defs import GRAMMAR, START_SYMBOL, is_nonterminal


class MappingError(ValueError):
    """Genome could not be fully mapped to a valid expression."""


def decode_genome_to_expr(genome: List[int],
                          max_expansions: int = 100) -> str:
    """
    Map a list of codons to a 6-char expression using the grammar.

    - Uses classic GE mapping: for each nonterminal, pick production
      via codon % num_productions.
    - Wraps around the genome if needed.
    - Fails if nonterminals remain after max_expansions.
    """
    if not genome:
        raise MappingError("Empty genome")

    symbols: List[str] = [START_SYMBOL]
    codon_idx = 0
    expansions = 0
    genome_len = len(genome)

    while any(is_nonterminal(s) for s in symbols):
        if expansions >= max_expansions:
            raise MappingError(
                f"Exceeded max_expansions={max_expansions} while mapping genome"
            )

        # Expand first nonterminal from left
        for i, sym in enumerate(symbols):
            if is_nonterminal(sym):
                productions = GRAMMAR.get(sym)
                if not productions:
                    raise MappingError(f"No productions for nonterminal {sym!r}")

                codon = genome[codon_idx % genome_len]
                codon_idx += 1

                choice = codon % len(productions)
                expansion = productions[choice]

                # Replace symbol at i with the chosen expansion
                symbols = symbols[:i] + expansion + symbols[i + 1 :]
                expansions += 1
                break

    expr = "".join(symbols)

    if len(expr) != 6:
        # Should not happen if grammar is correct
        raise MappingError(f"Mapped expression {expr!r} has length {len(expr)}, not 6")

    return expr
