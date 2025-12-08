# tests/test_grammar.py
import pytest

from grammar import (
    encode_expr_to_genome,
    decode_genome_to_expr,
    EncodingError,
    MappingError,
)


# A few valid 6-char expressions that should be in the grammar language:
# - 1+2345 : int1 op int4
# - 12+3*4 : tri_expr6_211 pattern (2,1,1)
# - 1+2*34 : tri_expr6_112 pattern (1,1,2)
# - 1*23+4 : tri_expr6_121 pattern (1,2,1)
VALID_EXPR6 = [
    "1+2345",
    "12+3*4",
    "1+2*34",
    "1*23+4",
]


@pytest.mark.parametrize("expr", VALID_EXPR6)
def test_encode_decode_round_trip_default_length(expr: str):
    genome = encode_expr_to_genome(expr, genome_length=20)
    decoded = decode_genome_to_expr(genome)
    assert decoded == expr


@pytest.mark.parametrize("expr", VALID_EXPR6)
def test_encode_decode_round_trip_short_genome(expr: str):
    # Shorter genome than number of choices -> decoder wraps around, but
    # first few codons still drive the same derivation.
    genome = encode_expr_to_genome(expr, genome_length=8)
    decoded = decode_genome_to_expr(genome)
    assert decoded == expr


@pytest.mark.parametrize("expr", VALID_EXPR6)
def test_encode_decode_round_trip_long_genome(expr: str):
    # Longer genome -> extra codons are unused and should not affect decoding.
    genome = encode_expr_to_genome(expr, genome_length=40)
    decoded = decode_genome_to_expr(genome)
    assert decoded == expr


def test_encode_invalid_length_raises():
    # Not 6 characters
    with pytest.raises(EncodingError):
        encode_expr_to_genome("1+23")  # length 4


def test_encode_invalid_chars_raises():
    # Contains illegal character 'a'
    with pytest.raises(EncodingError):
        encode_expr_to_genome("1a2+3")  # length 5 plus illegal char


def test_decode_empty_genome_raises():
    with pytest.raises(MappingError):
        decode_genome_to_expr([])
        

def test_decode_all_zero_genome_produces_6_char_expr():
    # Basic sanity: mapping should produce a 6-character expression
    expr = decode_genome_to_expr([0, 0, 0, 0, 0, 0, 0, 0])
    assert isinstance(expr, str)
    assert len(expr) == 6
