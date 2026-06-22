"""Shared headless helpers for driving :mod:`chess_core` in tests.

Provides full *legal* move enumeration (including Chess960 castling and the four
promotion choices) plus a push/pop-by-copy move applier, used by the perft and
PGN round-trip suites. None of this imports pygame.
"""
import copy
from typing import List, Optional, Tuple

from chess_core import BLACK, WHITE, CoreBoard, make_core_piece

Coord = Tuple[int, int]
OTHER = {WHITE: BLACK, BLACK: WHITE}

# A move is (from_sq, to_sq, promotion_or_None, rook_dest_or_None).
# rook_dest is set only for castling; promotion is set only for promoting pawn moves.
Move = Tuple[Coord, Coord, Optional[str], Optional[Coord]]


def piece_at(board: CoreBoard, color: str):
    return board.white_pieces if color == WHITE else board.black_pieces


def legal_moves(board: CoreBoard, color: str) -> List[Move]:
    """Enumerate every legal move for ``color``, promotions expanded to 4."""
    out: List[Move] = []
    pieces = piece_at(board, color)
    for p in list(pieces):
        for m in board.get_valid_moves_for(p, color):
            if p.piece_type == 'pawn' and m[1] in (0, 7):
                for promo in ('queen', 'rook', 'bishop', 'knight'):
                    out.append((tuple(p.position), tuple(m), promo, None))
            else:
                out.append((tuple(p.position), tuple(m), None, None))
    king = next((p for p in pieces if p.piece_type == 'king'), None)
    if king:
        for king_dest, rook_dest in board.check_castling(color):
            out.append((tuple(king.position), tuple(king_dest), None, tuple(rook_dest)))
    return out


def apply_move(board: CoreBoard, color: str, move: Move) -> None:
    """Apply ``move`` in place (handles castling, promotion, en passant)."""
    frm, to, promo, rook_dest = move
    piece = board.get_piece_at_position(frm)
    if rook_dest is not None:
        kx = frm[0]
        kingside = to[0] > kx
        pieces = piece_at(board, color)
        rook = next(
            r for r in pieces
            if r.piece_type == 'rook'
            and ((kingside and r.position[0] > kx) or (not kingside and r.position[0] < kx))
        )
        board.castle(piece, rook, to, rook_dest)
        return

    board.move_piece(piece, to)
    if promo:
        pieces = piece_at(board, color)
        pieces.remove(piece)
        new_piece = make_core_piece(promo, color, to, board)
        new_piece.has_moved = True
        pieces.append(new_piece)
        board._on_square_set(to[0], to[1], new_piece)


def perft(board: CoreBoard, color: str, depth: int) -> int:
    """Count leaf nodes ``depth`` plies deep from ``board`` (push/pop by copy)."""
    if depth == 0:
        return 1
    total = 0
    for move in legal_moves(board, color):
        child = copy.deepcopy(board)
        apply_move(child, color, move)
        total += perft(child, OTHER[color], depth - 1)
    return total


def empty_board() -> CoreBoard:
    """A CoreBoard with no pieces (for hand-built rule positions)."""
    b = CoreBoard()
    b.white_pieces = []
    b.black_pieces = []
    b.white_ep = None
    b.black_ep = None
    b.last_move = None
    return b


def place(board: CoreBoard, piece_type: str, color: str, pos: Coord, has_moved: bool = False):
    """Create and place a piece on ``board``; returns it."""
    p = make_core_piece(piece_type, color, pos, board)
    p.has_moved = has_moved
    (board.white_pieces if color == WHITE else board.black_pieces).append(p)
    return p
