"""SP-number <-> back-rank (Scharnagl) tests (FIXLIST A21 / C3).

Cross-checked against python-chess (``chess.Board.from_chess960_pos``) as the
reference for every n in range(960).
"""
import chess
import pytest

from chess960_generator import Chess960Generator
from chess_core import (
    STANDARD_SP_NUMBER,
    back_rank_to_sp_number,
    sp_number_to_back_rank,
)

STANDARD = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']

_PC_NAME = {
    chess.ROOK: 'rook', chess.KNIGHT: 'knight', chess.BISHOP: 'bishop',
    chess.QUEEN: 'queen', chess.KING: 'king',
}


def _python_chess_back_rank(n):
    """White back-rank (col 0-7) for SP-number n from python-chess."""
    b = chess.Board.from_chess960_pos(n)
    return [_PC_NAME[b.piece_at(chess.square(f, 0)).piece_type] for f in range(8)]


def test_round_trip_all_960():
    for n in range(960):
        assert back_rank_to_sp_number(sp_number_to_back_rank(n)) == n


def test_bijection_960_distinct():
    distinct = {tuple(sp_number_to_back_rank(n)) for n in range(960)}
    assert len(distinct) == 960


def test_sp_518_is_standard():
    assert STANDARD_SP_NUMBER == 518
    assert sp_number_to_back_rank(518) == STANDARD
    assert back_rank_to_sp_number(STANDARD) == 518


@pytest.mark.parametrize("n", list(range(960)))
def test_cross_check_python_chess(n):
    assert sp_number_to_back_rank(n) == _python_chess_back_rank(n)


def test_out_of_range_rejected():
    for bad in (-1, 960, 1000):
        with pytest.raises(ValueError):
            sp_number_to_back_rank(bad)


def test_invalid_back_rank_rejected():
    # Wrong length.
    with pytest.raises(ValueError):
        back_rank_to_sp_number(['rook', 'king', 'rook'])
    # Wrong piece multiset (two queens, no king).
    with pytest.raises(ValueError):
        back_rank_to_sp_number(
            ['rook', 'queen', 'bishop', 'queen', 'bishop', 'knight', 'knight', 'rook'])
    # Two bishops on the same color square (cols 0 and 2, both even).
    with pytest.raises(ValueError):
        back_rank_to_sp_number(
            ['bishop', 'rook', 'bishop', 'queen', 'king', 'knight', 'knight', 'rook'])
    # Valid multiset and opposite-color bishops, but king not between the rooks
    # (king at col 0, both rooks to its right).
    with pytest.raises(ValueError):
        back_rank_to_sp_number(
            ['king', 'bishop', 'rook', 'knight', 'bishop', 'knight', 'queen', 'rook'])


def test_generator_helpers_expose_sp_number():
    # generate_with_sp_number round-trips through the mapping.
    back_rank, sp = Chess960Generator.generate_with_sp_number()
    assert 0 <= sp <= 959
    assert Chess960Generator.from_sp_number(sp) == back_rank
    assert Chess960Generator.sp_number(back_rank) == sp
