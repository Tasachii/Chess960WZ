"""Property, completeness, uniformity, and FEN-validity tests for the
Chess960 back-rank generator (``chess960_generator.Chess960Generator``).

These tests lock the generator's current (correct) behavior. They are pure and
require no display, so they run today without the Section B core extraction.
"""
import random
from collections import Counter

import chess
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from chess960_generator import Chess960Generator

PIECE_CHARS = {
    'king': 'k', 'queen': 'q', 'rook': 'r',
    'bishop': 'b', 'knight': 'n', 'pawn': 'p',
}
EXPECTED_MULTISET = {'rook': 2, 'knight': 2, 'bishop': 2, 'queen': 1, 'king': 1}
STANDARD_BACK_RANK = ['rook', 'knight', 'bishop', 'queen',
                      'king', 'bishop', 'knight', 'rook']


def _all_back_ranks():
    """Deterministically enumerate every valid Chess960 back-rank.

    Independent of the generator: brute-force all 8-square arrangements of
    {2 rook, 2 knight, 2 bishop, 1 queen, 1 king} satisfying the Chess960
    constraints (bishops on opposite colors, king strictly between the rooks).
    """
    from itertools import permutations

    seen = set()
    out = []
    base = ('rook', 'rook', 'knight', 'knight',
            'bishop', 'bishop', 'queen', 'king')
    for perm in set(permutations(base)):
        bishops = [i for i, p in enumerate(perm) if p == 'bishop']
        if (bishops[0] % 2) == (bishops[1] % 2):
            continue  # bishops must be opposite colors
        rooks = [i for i, p in enumerate(perm) if p == 'rook']
        king = perm.index('king')
        if not (rooks[0] < king < rooks[1]):
            continue  # king strictly between the rooks
        if perm not in seen:
            seen.add(perm)
            out.append(list(perm))
    return out


# ---------------------------------------------------------------------------
# 1-4. Structural invariants (hypothesis property tests)
# ---------------------------------------------------------------------------

@given(st.integers(min_value=0, max_value=2**32 - 1))
@settings(max_examples=300)
def test_multiset(seed):
    random.seed(seed)
    br = Chess960Generator.generate()
    assert Counter(br) == EXPECTED_MULTISET


@given(st.integers(min_value=0, max_value=2**32 - 1))
@settings(max_examples=300)
def test_bishops_opposite_color(seed):
    random.seed(seed)
    br = Chess960Generator.generate()
    bishops = [i for i, p in enumerate(br) if p == 'bishop']
    assert len(bishops) == 2
    assert bishops[0] % 2 != bishops[1] % 2


@given(st.integers(min_value=0, max_value=2**32 - 1))
@settings(max_examples=300)
def test_king_strictly_between_rooks(seed):
    random.seed(seed)
    br = Chess960Generator.generate()
    rooks = [i for i, p in enumerate(br) if p == 'rook']
    king = br.index('king')
    assert len(rooks) == 2
    assert rooks[0] < king < rooks[1]


@given(st.integers(min_value=0, max_value=2**32 - 1))
@settings(max_examples=300)
def test_length_and_no_none(seed):
    random.seed(seed)
    br = Chess960Generator.generate()
    assert len(br) == 8
    assert None not in br


# ---------------------------------------------------------------------------
# 5. Completeness — exactly 960 distinct valid back-ranks
# ---------------------------------------------------------------------------

def test_enumeration_is_960_distinct():
    all_br = _all_back_ranks()
    distinct = {tuple(b) for b in all_br}
    assert len(distinct) == 960


def test_generator_only_produces_enumerated_positions():
    valid = {tuple(b) for b in _all_back_ranks()}
    random.seed(12345)
    for _ in range(2000):
        assert tuple(Chess960Generator.generate()) in valid


# ---------------------------------------------------------------------------
# 6. Near-uniform distribution (no scipy: per-bucket +-4 sigma envelope)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_near_uniform_distribution():
    n_buckets = 960
    per = 100
    n = n_buckets * per  # 96,000 samples
    random.seed(2024)
    counts = Counter()
    for _ in range(n):
        counts[tuple(Chess960Generator.generate())] += 1

    assert len(counts) == n_buckets, "not all 960 positions were produced"

    # Binomial sigma for each bucket under the uniform null.
    p = 1.0 / n_buckets
    mean = n * p
    sigma = (n * p * (1 - p)) ** 0.5
    lo, hi = mean - 4 * sigma, mean + 4 * sigma
    outliers = [c for c in counts.values() if not (lo <= c <= hi)]
    # Allow a tiny number of >4 sigma buckets across 960 (expected ~0 but noisy).
    assert len(outliers) <= 5, (
        f"{len(outliers)} buckets outside +-4 sigma "
        f"[{lo:.1f}, {hi:.1f}] (mean={mean:.1f})"
    )


# ---------------------------------------------------------------------------
# 7. Standard arrangement -> RNBQKBNR
# ---------------------------------------------------------------------------

def test_standard_arrangement_fen():
    fen = Chess960Generator.starting_fen(STANDARD_BACK_RANK)
    assert fen.startswith("rnbqkbnr/")
    parts = fen.split()
    assert parts[0].split('/')[-1] == "RNBQKBNR"
    assert parts[2] == "HAha"  # Shredder castling for corner rooks


# ---------------------------------------------------------------------------
# 8. Every generated FEN is valid under python-chess (chess960)
# ---------------------------------------------------------------------------

def test_generated_fens_valid_under_python_chess():
    random.seed(777)
    for _ in range(1000):
        br = Chess960Generator.generate()
        fen = Chess960Generator.starting_fen(br)
        board = chess.Board(fen, chess960=True)
        assert board.is_valid()


# ---------------------------------------------------------------------------
# A1 regression: Shredder castling field correctness (the proven FEN bug)
# ---------------------------------------------------------------------------

def test_shredder_castling_field_inner_rooks():
    # nrkrbqbn -> DBdb (the exact value python-chess produced in the audit).
    br = ['knight', 'rook', 'king', 'rook', 'bishop', 'queen', 'bishop', 'knight']
    fen = Chess960Generator.starting_fen(br)
    assert fen.split()[2] == "DBdb"
    board = chess.Board(fen, chess960=True)
    assert board.is_valid()
    # Round-trip: python-chess Shredder rendering matches our castling field.
    assert board.shredder_fen().split()[2] == "DBdb"


def test_shredder_castling_field_matches_python_chess_for_samples():
    random.seed(99)
    for _ in range(500):
        br = Chess960Generator.generate()
        fen = Chess960Generator.starting_fen(br)
        board = chess.Board(fen, chess960=True)
        assert board.shredder_fen().split()[2] == fen.split()[2]
