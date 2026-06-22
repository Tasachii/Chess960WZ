"""Draw-rule tests (FIXLIST A10 / C4.13): threefold repetition and
insufficient material, cross-checked against python-chess where applicable.

These exercise the pure :mod:`chess_core` board with no pygame.
"""
import chess
import pytest

from chess_core import BLACK, WHITE

from _core_helpers import apply_move, empty_board, place

# (col, row) -> python-chess square index (col == file, row == rank).
PC_PIECE = {
    'pawn': chess.PAWN, 'knight': chess.KNIGHT, 'bishop': chess.BISHOP,
    'rook': chess.ROOK, 'queen': chess.QUEEN, 'king': chess.KING,
}
PC_COLOR = {WHITE: chess.WHITE, BLACK: chess.BLACK}


def _pc_board(pieces):
    """Build a python-chess board from (piece_type, color, (col, row)) tuples."""
    b = chess.Board(None)
    for pt, color, (col, row) in pieces:
        b.set_piece_at(chess.square(col, row),
                       chess.Piece(PC_PIECE[pt], PC_COLOR[color]))
    return b


def _core_board(pieces):
    """Build a CoreBoard from (piece_type, color, (col, row)) tuples."""
    b = empty_board()
    for pt, color, pos in pieces:
        place(b, pt, color, pos)
    return b


# --------------------------------------------------------------- threefold

def test_threefold_repetition_draw():
    """Shuffling two knights back and forth repeats the start position 3x."""
    b = empty_board()
    place(b, 'king', WHITE, (4, 0))
    place(b, 'king', BLACK, (4, 7))
    wn = place(b, 'knight', WHITE, (1, 0))
    bn = place(b, 'knight', BLACK, (1, 7))

    # Record the initial position (White to move).
    b.record_position(WHITE)
    assert not b.is_threefold_repetition()

    # Two full cycles return to the exact start position twice more.
    cycle = [
        (wn, (2, 2), WHITE), (bn, (2, 5), BLACK),
        (wn, (1, 0), WHITE), (bn, (1, 7), BLACK),
    ]
    side_after = {WHITE: BLACK, BLACK: WHITE}
    occurrences = 1
    for _ in range(2):
        for piece, dest, mover in cycle:
            apply_move(b, mover, (tuple(piece.position), dest, None, None))
            b.record_position(side_after[mover])
        occurrences += 1  # start position reached once more per cycle
    assert occurrences == 3
    assert b.is_threefold_repetition()


def test_non_repeated_position_not_draw():
    """A position seen only once (and twice) is not a threefold draw."""
    b = empty_board()
    place(b, 'king', WHITE, (4, 0))
    place(b, 'king', BLACK, (4, 7))
    wn = place(b, 'knight', WHITE, (1, 0))
    bn = place(b, 'knight', BLACK, (1, 7))

    b.record_position(WHITE)               # start, 1st time
    apply_move(b, WHITE, ((1, 0), (2, 2), None, None))
    b.record_position(BLACK)
    apply_move(b, BLACK, ((1, 7), (2, 5), None, None))
    b.record_position(WHITE)
    apply_move(b, WHITE, ((2, 2), (1, 0), None, None))
    b.record_position(BLACK)
    apply_move(b, BLACK, ((2, 5), (1, 7), None, None))
    b.record_position(WHITE)               # start, 2nd time
    assert not b.is_threefold_repetition()
    _ = (wn, bn)


def test_repetition_signature_distinguishes_side_to_move():
    """Same placement but different side-to-move are different positions."""
    b = empty_board()
    place(b, 'king', WHITE, (4, 0))
    place(b, 'king', BLACK, (4, 7))
    sig_white = b.position_signature(WHITE)
    sig_black = b.position_signature(BLACK)
    assert sig_white != sig_black


def test_repetition_signature_distinguishes_castling_rights():
    """Losing castling rights changes the signature (not a repetition)."""
    b = empty_board()
    k = place(b, 'king', WHITE, (4, 0))
    place(b, 'king', BLACK, (4, 7))
    place(b, 'rook', WHITE, (7, 0))
    sig_before = b.position_signature(WHITE)
    k.has_moved = True
    sig_after = b.position_signature(WHITE)
    assert sig_before != sig_after


# ----------------------------------------------------- insufficient material

INSUFFICIENT_CASES = [
    ("K vs K", [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7))]),
    ("K+B vs K", [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
                  ('bishop', WHITE, (2, 0))]),
    ("K+N vs K", [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
                  ('knight', WHITE, (1, 0))]),
    # K+B vs K+B, both bishops on the same color square (c1 and f8 are both dark).
    ("K+B vs K+B same color",
     [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
      ('bishop', WHITE, (2, 0)), ('bishop', BLACK, (5, 7))]),
]

SUFFICIENT_CASES = [
    # K+B vs K+B on opposite colors (c1 dark, c8 light) -> NOT a draw.
    ("K+B vs K+B opposite color",
     [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
      ('bishop', WHITE, (2, 0)), ('bishop', BLACK, (2, 7))]),
    ("K+R vs K", [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
                  ('rook', WHITE, (0, 0))]),
    ("K+Q vs K", [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
                  ('queen', WHITE, (3, 0))]),
    # Two knights vs lone king is NOT insufficient per python-chess semantics.
    ("K+N+N vs K", [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
                    ('knight', WHITE, (1, 0)), ('knight', WHITE, (6, 0))]),
    ("K+P vs K", [('king', WHITE, (4, 0)), ('king', BLACK, (4, 7)),
                  ('pawn', WHITE, (0, 1))]),
]


@pytest.mark.parametrize("label,pieces", INSUFFICIENT_CASES)
def test_insufficient_material_draw(label, pieces):
    core = _core_board(pieces)
    assert core.is_insufficient_material() is True, label
    # Cross-check against python-chess as the reference.
    assert _pc_board(pieces).is_insufficient_material() is True, label


@pytest.mark.parametrize("label,pieces", SUFFICIENT_CASES)
def test_sufficient_material_not_draw(label, pieces):
    core = _core_board(pieces)
    assert core.is_insufficient_material() is False, label
    assert _pc_board(pieces).is_insufficient_material() is False, label


def test_insufficient_material_matches_python_chess_random():
    """Bulk differential check: random material configs agree with python-chess."""
    import random
    random.seed(20240622)
    types = ['knight', 'bishop', 'rook', 'queen', 'pawn']
    colors = [WHITE, BLACK]
    mism = 0
    for _ in range(2000):
        used = set()

        def rand_sq():
            while True:
                c, r = random.randint(0, 7), random.randint(0, 7)
                if (c, r) not in used:
                    used.add((c, r))
                    return (c, r)

        pieces = [('king', WHITE, rand_sq()), ('king', BLACK, rand_sq())]
        for _ in range(random.randint(0, 4)):
            pt = random.choice(types)
            pos = rand_sq()
            if pt == 'pawn' and pos[1] in (0, 7):
                continue
            pieces.append((pt, random.choice(colors), pos))
        if _core_board(pieces).is_insufficient_material() != \
                _pc_board(pieces).is_insufficient_material():
            mism += 1
    assert mism == 0
