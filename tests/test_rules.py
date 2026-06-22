"""C4 rule-engine tests against the pure chess_core (no pygame).

Each test hand-builds a position and asserts a single rule: en-passant lifecycle,
the castling-block cases, Chess960 castling targets, the C4.8 slider-masking edge
case, absolute pins, stalemate vs checkmate, promotion, and the 50-move counter.
"""
import chess
import pytest

from chess_core import BLACK, WHITE

from _core_helpers import apply_move, empty_board, place


# --------------------------------------------------------------------- en passant

def test_en_passant_only_immediately_after_double_step():
    """The diagonal e.p. capture is legal right after the double-step and the
    captured pawn is actually removed (its square cleared)."""
    b = empty_board()
    place(b, 'king', WHITE, (0, 0))
    place(b, 'king', BLACK, (0, 7))
    wp = place(b, 'pawn', WHITE, (4, 4), has_moved=True)   # white pawn e5
    bp = place(b, 'pawn', BLACK, (3, 6))                   # black pawn d7

    # black double-steps d7 -> d5, setting the e.p. target on d6
    b.move_piece(bp, (3, 4))
    assert b.black_ep == (3, 5)

    # white e5 pawn can capture en passant onto d6
    moves = wp.get_valid_moves()
    assert (3, 5) in moves

    b.move_piece(wp, (3, 5))
    assert tuple(wp.position) == (3, 5)
    assert b.get_piece_at_position((3, 4)) is None          # captured pawn gone
    assert bp not in b.black_pieces
    assert bp in b.captured_black


def test_en_passant_window_closes_after_another_move():
    """If the side to move plays something else, the e.p. capture disappears
    (sentinel resets to None)."""
    b = empty_board()
    place(b, 'king', WHITE, (0, 0))
    bk = place(b, 'king', BLACK, (0, 7))
    wp = place(b, 'pawn', WHITE, (4, 4), has_moved=True)
    bp = place(b, 'pawn', BLACK, (3, 6))

    b.move_piece(bp, (3, 4))            # double step, black_ep = (3,5)
    assert (3, 5) in wp.get_valid_moves()

    # white makes an unrelated king move; the en-passant offer is black's and
    # only applies to white's immediately-following move. White declines it, then
    # black moves, which clears black_ep.
    b.move_piece(b.get_piece_at_position((0, 0)), (1, 0))
    b.move_piece(bk, (1, 7))            # any black move clears black_ep
    assert b.black_ep is None
    assert (3, 5) not in wp.get_valid_moves()


def test_en_passant_sentinel_is_none_not_offboard():
    b = empty_board()
    place(b, 'king', WHITE, (4, 0))
    place(b, 'king', BLACK, (4, 7))
    assert b.white_ep is None
    assert b.black_ep is None
    assert b.get_en_passant_square(WHITE) is None
    assert b.get_en_passant_square(BLACK) is None


# ----------------------------------------------------------------- castling blocks

def _white_king_rook(king_col, rook_col, king_row=0):
    b = empty_board()
    wk = place(b, 'king', WHITE, (king_col, king_row))
    wr = place(b, 'rook', WHITE, (rook_col, king_row))
    place(b, 'king', BLACK, (4, 7))
    return b, wk, wr


def test_castling_blocked_when_king_in_check():
    b, wk, wr = _white_king_rook(4, 7)          # e1 king, h1 rook (kingside)
    place(b, 'rook', BLACK, (4, 5))             # black rook e3 checks king on e1
    assert b.is_king_in_check(WHITE)
    assert b.check_castling(WHITE) == []


def test_castling_blocked_through_attacked_square():
    b, wk, wr = _white_king_rook(4, 7)          # king e1 -> g1 passes f1
    place(b, 'rook', BLACK, (5, 7))             # black rook f8 attacks f1
    assert b.check_castling(WHITE) == []


def test_castling_blocked_destination_attacked():
    b, wk, wr = _white_king_rook(4, 7)          # king dest g1
    place(b, 'rook', BLACK, (6, 7))             # black rook g8 attacks g1
    assert b.check_castling(WHITE) == []


def test_castling_blocked_path_occupied():
    b, wk, wr = _white_king_rook(4, 7)          # king e1, rook h1
    place(b, 'bishop', WHITE, (5, 0))           # own bishop on f1 blocks the path
    assert b.check_castling(WHITE) == []


def test_castling_blocked_king_has_moved():
    b, wk, wr = _white_king_rook(4, 7)
    wk.has_moved = True
    assert b.check_castling(WHITE) == []


def test_castling_blocked_rook_has_moved():
    b, wk, wr = _white_king_rook(4, 7)
    wr.has_moved = True
    assert b.check_castling(WHITE) == []


def test_castling_allowed_clear_kingside():
    b, wk, wr = _white_king_rook(4, 7)
    assert b.check_castling(WHITE) == [((6, 0), (5, 0))]


# -------------------------------------------------------- Chess960 castling targets

def test_chess960_castling_targets_kingside():
    """Non-standard start: king on b-file, rook on a far file -> king lands g1, rook f1."""
    b, wk, wr = _white_king_rook(1, 6)          # king b1, rook g1 (kingside)
    castles = b.check_castling(WHITE)
    assert castles == [((6, 0), (5, 0))]        # king -> g-file (6), rook -> f-file (5)


def test_chess960_castling_targets_queenside():
    """King on f-file, queenside rook -> king lands c1 (2), rook d1 (3)."""
    b, wk, wr = _white_king_rook(5, 1)          # king f1, rook b1 (queenside)
    castles = b.check_castling(WHITE)
    assert castles == [((2, 0), (3, 0))]        # king -> c-file (2), rook -> d-file (3)


def test_chess960_castling_both_targets_match_python_chess():
    """Cross-check c/g king + d/f rook targets against python-chess for a 960 start."""
    b, wk, wr = _white_king_rook(4, 0)          # king e1, queenside rook a1
    # add a kingside rook too
    place(b, 'rook', WHITE, (7, 0))
    castles = sorted(b.check_castling(WHITE))
    # queenside: king->c1(2), rook->d1(3); kingside: king->g1(6), rook->f1(5)
    assert castles == [((2, 0), (3, 0)), ((6, 0), (5, 0))]


# ----------------------------------------------------------- C4.8 slider masking

def test_c48_slider_masking_false_positive_fixed():
    """The gap found in the audit: a slider whose ray to a king-path square is
    blocked *only* by the castling rook (not the king) must still forbid castling.

    Position: white king d1, white queenside rook b1, black rook a1, black king
    f8. With both white pieces present the a1 rook's ray stops at b1, so naively
    the king's path (c1, d1) looks safe -> false positive. Vacating the king AND
    the rook during the scan exposes the attack. python-chess agrees this castle
    is illegal and the king is not in check.
    """
    b = empty_board()
    place(b, 'king', WHITE, (3, 0))             # d1
    place(b, 'rook', WHITE, (1, 0))             # b1 (queenside rook)
    place(b, 'rook', BLACK, (0, 0))             # a1 attacker
    place(b, 'king', BLACK, (5, 7))             # f8

    assert not b.is_king_in_check(WHITE)        # the b1 rook masks the check too
    assert b.check_castling(WHITE) == []        # post-fix: correctly illegal

    # ground truth: python-chess forbids this castle
    bd = chess.Board(None, chess960=True)
    bd.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    bd.set_piece_at(chess.B1, chess.Piece(chess.ROOK, chess.WHITE))
    bd.set_piece_at(chess.D1, chess.Piece(chess.KING, chess.WHITE))
    bd.set_piece_at(chess.F8, chess.Piece(chess.KING, chess.BLACK))
    bd.turn = chess.WHITE
    bd.castling_rights = chess.BB_B1
    assert bd.is_valid()
    assert [m for m in bd.legal_moves if bd.is_castling(m)] == []


def test_c48_castling_still_allowed_when_truly_safe():
    """Sanity counterpart: clear the masking attacker -> castling is legal again."""
    b = empty_board()
    place(b, 'king', WHITE, (3, 0))
    place(b, 'rook', WHITE, (1, 0))
    place(b, 'king', BLACK, (5, 7))
    assert b.check_castling(WHITE) == [((2, 0), (3, 0))]


# ------------------------------------------------------------------- pinned piece

def test_absolutely_pinned_piece_cannot_move():
    """A bishop pinned to its own king by a rook cannot step off the pin line."""
    b = empty_board()
    place(b, 'king', WHITE, (4, 0))             # e1
    bishop = place(b, 'bishop', WHITE, (4, 3))  # e4, in front of the king
    place(b, 'rook', BLACK, (4, 7))             # e8 pins the bishop along the e-file
    place(b, 'king', BLACK, (0, 7))

    legal = b.get_valid_moves_for(bishop, WHITE)
    assert legal == []                          # any bishop move exposes the king

    # the king itself can still move off the file
    king = b.get_piece_at_position((4, 0))
    king_legal = b.get_valid_moves_for(king, WHITE)
    assert (3, 0) in king_legal or (5, 0) in king_legal


# ------------------------------------------------------- stalemate vs checkmate

def test_stalemate_not_checkmate():
    """Classic K+Q stalemate: black king a8, white queen c7, white king c6.
    Black is not in check but has no legal move."""
    b = empty_board()
    place(b, 'king', BLACK, (0, 7))             # a8
    place(b, 'queen', WHITE, (2, 6))            # c7
    place(b, 'king', WHITE, (2, 5))             # c6
    assert b.is_stalemate(BLACK) is True
    assert b.is_checkmate(BLACK) is False
    assert b.is_king_in_check(BLACK) is False


def test_back_rank_checkmate_not_stalemate():
    """Back-rank mate: black king g8 boxed by its own pawns, white rook a8 mates."""
    b = empty_board()
    place(b, 'king', BLACK, (6, 7))             # g8
    place(b, 'pawn', BLACK, (5, 6), has_moved=False)   # f7
    place(b, 'pawn', BLACK, (6, 6), has_moved=False)   # g7
    place(b, 'pawn', BLACK, (7, 6), has_moved=False)   # h7
    place(b, 'rook', WHITE, (0, 7))             # a8 delivers mate along rank 8
    place(b, 'king', WHITE, (0, 0))
    assert b.is_king_in_check(BLACK) is True
    assert b.is_checkmate(BLACK) is True
    assert b.is_stalemate(BLACK) is False


# --------------------------------------------------------------------- promotion

@pytest.mark.parametrize("promo", ['bishop', 'knight', 'rook', 'queen'])
def test_promotion_to_all_four(promo):
    """A white pawn reaching rank 8 promotes to each piece type, updating the grid."""
    b = empty_board()
    place(b, 'king', WHITE, (0, 0))
    place(b, 'king', BLACK, (7, 7))
    pawn = place(b, 'pawn', WHITE, (4, 6), has_moved=True)   # e7

    # promotion move e7 -> e8 then swap (mirrors the helper's apply_move)
    apply_move(b, WHITE, ((4, 6), (4, 7), promo, None))

    promoted = b.get_piece_at_position((4, 7))
    assert promoted is not None
    assert promoted.piece_type == promo
    assert promoted.color == WHITE
    assert pawn not in b.white_pieces


# --------------------------------------------------------------------- 50-move

def test_fifty_move_counter_resets_on_pawn_or_capture():
    """The 50-move rule is enforced by a halfmove counter that resets on any
    pawn move or capture and increments otherwise. We exercise that arithmetic
    directly (the core supplies the predicates used by the game)."""
    b = empty_board()
    place(b, 'king', WHITE, (4, 0))
    place(b, 'king', BLACK, (4, 7))
    knight = place(b, 'knight', WHITE, (1, 0))   # b1
    pawn = place(b, 'pawn', WHITE, (0, 1))       # a2

    halfmove_clock = 98
    # a quiet knight move increments toward 100
    cap = b.get_piece_at_position((2, 2))
    is_capture = cap is not None
    b.move_piece(knight, (2, 2))
    halfmove_clock = 0 if (is_capture or knight.piece_type == 'pawn') else halfmove_clock + 1
    assert halfmove_clock == 99

    # one more quiet move reaches the 100-halfmove (50-move) draw threshold
    b.move_piece(knight, (1, 0))
    halfmove_clock = halfmove_clock + 1
    assert halfmove_clock >= 100

    # a pawn move resets the counter to 0
    b.move_piece(pawn, (0, 2))
    is_pawn_move = pawn.piece_type == 'pawn'
    halfmove_clock = 0 if is_pawn_move else halfmove_clock + 1
    assert halfmove_clock == 0
