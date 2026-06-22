"""C5 perft tests — the bulk correctness gate.

Enumerate leaf nodes at depth 1-3 from the chess_core legal-move generator and
assert equality with python-chess (chess960=True) perft on the *same* position:
the standard start (20 / 400 / 8902) and 3 fixed Chess960 starts. Depth-3 is
marked ``slow``. A mismatch here means a real move-generation bug.
"""
import random

import chess
import pytest

from chess_core import WHITE, CoreBoard
from chess960_generator import Chess960Generator

from _core_helpers import perft

# Fixed Chess960 back-ranks (seeded so the suite is deterministic) plus the
# standard arrangement.
STANDARD = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']


def _fixed_chess960_back_ranks(n=3):
    rng = random.Random(20260622)
    out = []
    saved_state = random.getstate()
    try:
        for _ in range(n):
            random.seed(rng.randint(0, 10_000_000))
            out.append(Chess960Generator.generate())
    finally:
        random.setstate(saved_state)
    return out


CHESS960_BACK_RANKS = _fixed_chess960_back_ranks(3)
ALL_BACK_RANKS = [STANDARD] + CHESS960_BACK_RANKS


def _python_chess_perft(board: chess.Board, depth: int) -> int:
    if depth == 0:
        return 1
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += _python_chess_perft(board, depth - 1)
        board.pop()
    return total


def _core_board(back_rank) -> CoreBoard:
    b = CoreBoard()
    b.setup_board(back_rank)
    return b


def _reference_board(back_rank) -> chess.Board:
    fen = Chess960Generator.starting_fen(back_rank)
    return chess.Board(fen, chess960=True)


# ------------------------------------------------------------- standard sanity

def test_standard_start_perft_known_values():
    b = _core_board(STANDARD)
    assert perft(b, WHITE, 1) == 20
    assert perft(b, WHITE, 2) == 400


@pytest.mark.slow
def test_standard_start_perft_depth3():
    b = _core_board(STANDARD)
    assert perft(b, WHITE, 3) == 8902


# ------------------------------------------------ core vs python-chess (1..2)

@pytest.mark.parametrize("back_rank", ALL_BACK_RANKS, ids=lambda br: ''.join(p[0] for p in br))
def test_perft_matches_python_chess_depth1_2(back_rank):
    core = _core_board(back_rank)
    ref = _reference_board(back_rank)
    for depth in (1, 2):
        assert perft(core, WHITE, depth) == _python_chess_perft(ref, depth), (
            f"perft({depth}) mismatch for back-rank {back_rank}"
        )


# ------------------------------------------------ core vs python-chess (depth 3)

@pytest.mark.slow
@pytest.mark.parametrize("back_rank", ALL_BACK_RANKS, ids=lambda br: ''.join(p[0] for p in br))
def test_perft_matches_python_chess_depth3(back_rank):
    core = _core_board(back_rank)
    ref = _reference_board(back_rank)
    assert perft(core, WHITE, 3) == _python_chess_perft(ref, 3), (
        f"perft(3) mismatch for back-rank {back_rank}"
    )
