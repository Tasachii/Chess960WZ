"""Pure board / position model and rules engine (no pygame).

``CoreBoard`` owns the piece lists, the en-passant target squares, captured/
notation bookkeeping and ``last_move``, plus every rule query (check, checkmate,
stalemate, Chess960 castling, en passant) and the move-application logic
(``move_piece``, ``is_move_safe_for_king``, ``get_valid_moves`` legality filter).

It has **no** display dependency; the Pygame ``ChessBoard`` subclasses it and
adds rendering. A ``piece_factory`` hook lets the render layer inject pieces that
carry images while the headless core uses plain :class:`~chess_core.pieces.PieceCore`.
"""
from contextlib import contextmanager
from typing import Callable, Hashable, List, Optional, Tuple

from constants import BLACK, WHITE

from .pieces import PieceCore, make_core_piece

Coord = Tuple[int, int]

STANDARD_BACK_RANK = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']


@contextmanager
def simulated_move(board: "CoreBoard", piece: PieceCore, new_pos, cap_pos=None):
    """Temporarily apply a move (and remove any captured piece), then restore.

    This unifies the two formerly-duplicated "simulate move / test king safety /
    restore" routines (FIXLIST A19). It removes the captured piece (defaulting to
    whatever sits on ``new_pos``; pass ``cap_pos`` explicitly for en-passant where
    the captured pawn is not on the destination square), moves ``piece``, yields,
    then restores the original position and re-inserts the captured piece in its
    original list slot so iteration order is preserved.

    ``piece=None`` is allowed: then no piece is moved (used to vacate a captured
    piece, or to scan with a piece removed via ``cap_pos``).
    """
    cap = board.get_piece_at_position(cap_pos) if cap_pos is not None else None
    cap_list = None
    cap_index = None
    if cap is not None and cap is not piece:
        cap_list = board.white_pieces if cap.color == WHITE else board.black_pieces
        cap_index = cap_list.index(cap)
        cap_list.pop(cap_index)

    orig = None
    if piece is not None:
        orig = list(piece.position)
        piece.position = list(new_pos)

    try:
        yield
    finally:
        if piece is not None and orig is not None:
            piece.position = orig
        if cap is not None and cap_list is not None and cap_index is not None:
            cap_list.insert(cap_index, cap)


class CoreBoard:
    """Pure board state + rules engine (no pygame)."""

    def __init__(self, piece_factory: Optional[Callable] = None) -> None:
        # Factory used to construct pieces (render layer injects image-bearing
        # pieces; default builds pure cores).
        self._piece_factory = piece_factory or make_core_piece

        self.white_pieces: List[PieceCore] = []
        self.black_pieces: List[PieceCore] = []
        self.captured_white: List[PieceCore] = []
        self.captured_black: List[PieceCore] = []
        self.notation_log: List[str] = []
        self.last_move = None

        # En-passant target squares; None means "no en-passant available".
        self.white_ep: Optional[Coord] = None
        self.black_ep: Optional[Coord] = None

        # Repetition history: list of position signatures (see
        # ``position_signature``). The game records one after each ply for
        # threefold-repetition detection (FIXLIST A10).
        self.position_history: List[Hashable] = []

    # ------------------------------------------------------------------ setup

    def _make_piece(self, piece_type, color, position):
        return self._piece_factory(piece_type, color, position, self)

    def _on_square_set(self, col, row, piece):
        """Hook for subclasses to keep an auxiliary square grid in sync.

        The pure core does not track a square grid; the render layer overrides
        this so its ``squares[col][row].piece`` mirror stays correct.
        """

    def setup_board(self, back_rank=None) -> None:
        self.white_pieces = []
        self.black_pieces = []
        self.captured_white = []
        self.captured_black = []
        self.notation_log = []
        self.white_ep = None
        self.black_ep = None
        self.last_move = None
        self.position_history = []

        if back_rank is None:
            back_rank = list(STANDARD_BACK_RANK)

        for col, pt in enumerate(back_rank):
            wp = self._make_piece(pt, WHITE, (col, 0))
            bp = self._make_piece(pt, BLACK, (col, 7))
            self.white_pieces.append(wp)
            self.black_pieces.append(bp)
            self._on_square_set(col, 0, wp)
            self._on_square_set(col, 7, bp)

        for col in range(8):
            wp = self._make_piece('pawn', WHITE, (col, 1))
            bp = self._make_piece('pawn', BLACK, (col, 6))
            self.white_pieces.append(wp)
            self.black_pieces.append(bp)
            self._on_square_set(col, 1, wp)
            self._on_square_set(col, 6, bp)

    def add_notation(self, text: str) -> None:
        self.notation_log.append(text)

    # ---------------------------------------------------------------- lookups

    def get_piece_at_position(self, position) -> Optional[PieceCore]:
        for p in self.white_pieces + self.black_pieces:
            if tuple(p.position) == tuple(position):
                return p
        return None

    def get_all_piece_positions(self) -> List[Coord]:
        return [tuple(p.position) for p in self.white_pieces + self.black_pieces]

    def get_piece_positions(self, color) -> List[Coord]:
        pieces = self.white_pieces if color == WHITE else self.black_pieces
        return [tuple(p.position) for p in pieces]

    def get_opponent_positions(self, color) -> List[Coord]:
        pieces = self.black_pieces if color == WHITE else self.white_pieces
        return [tuple(p.position) for p in pieces]

    def get_en_passant_square(self, color) -> Optional[Coord]:
        return self.white_ep if color == WHITE else self.black_ep

    # ------------------------------------------------------------ rule checks

    def is_king_in_check(self, color) -> bool:
        king = next(
            (p for p in (self.white_pieces if color == WHITE else self.black_pieces)
             if p.piece_type == 'king'),
            None,
        )
        if not king:
            return False
        opp = self.black_pieces if color == WHITE else self.white_pieces
        # use get_attack_squares so pawn diagonals are counted even on empty squares
        return any(king.get_pos() in p.get_attack_squares() for p in opp)

    def is_square_under_attack(self, position, attacking_color) -> bool:
        pieces = self.white_pieces if attacking_color == WHITE else self.black_pieces
        # use get_attack_squares for the same reason as is_king_in_check
        return any(position in p.get_attack_squares() for p in pieces)

    def _ep_capture_square(self, piece, move) -> Optional[Coord]:
        """Square of the pawn captured if ``move`` is an en-passant capture, else None."""
        if piece.piece_type != 'pawn':
            return None
        if piece.color == WHITE and self.black_ep is not None and tuple(move) == self.black_ep:
            return (move[0], move[1] - 1)
        if piece.color == BLACK and self.white_ep is not None and tuple(move) == self.white_ep:
            return (move[0], move[1] + 1)
        return None

    def is_move_safe_for_king(self, piece, new_pos, color) -> bool:
        """True if moving ``piece`` to ``new_pos`` leaves ``color``'s king safe.

        Handles the en-passant ghost pawn (the captured pawn is not on the
        destination square). Uses :func:`simulated_move` so the simulate/restore
        logic lives in exactly one place (A19).
        """
        ep_sq = self._ep_capture_square(piece, new_pos)
        cap_pos = ep_sq if ep_sq is not None else new_pos
        with simulated_move(self, piece, new_pos, cap_pos=cap_pos):
            return not self.is_king_in_check(color)

    def _has_legal_moves(self, color) -> bool:
        pieces = self.white_pieces if color == WHITE else self.black_pieces
        for p in pieces:
            for m in p.get_valid_moves():
                if self.is_move_safe_for_king(p, m, color):
                    return True
        return False

    def is_checkmate(self, color) -> bool:
        return self.is_king_in_check(color) and not self._has_legal_moves(color)

    def is_stalemate(self, color) -> bool:
        return not self.is_king_in_check(color) and not self._has_legal_moves(color)

    def get_valid_moves_for(self, piece, color) -> List[Coord]:
        """Legal (king-safe) moves for a single piece — the legality filter."""
        return [m for m in piece.get_valid_moves() if self.is_move_safe_for_king(piece, m, color)]

    def check_castling(self, color):
        """Chess960 castling targets for ``color`` (list of (king_dest, rook_dest)).

        King lands on the c-file (queenside, col 2) or g-file (kingside, col 6);
        the rook lands on the d-file (col 3) or f-file (col 5). Blocked if the
        king is in check, the king/rook has moved, the path is occupied, or any
        square the king travels through (incl. origin and destination) is
        attacked.
        """
        moves = []
        if self.is_king_in_check(color):
            return moves

        pieces = self.white_pieces if color == WHITE else self.black_pieces
        opp_color = BLACK if color == WHITE else WHITE
        king = next((p for p in pieces if p.piece_type == 'king'), None)
        rooks = [p for p in pieces if p.piece_type == 'rook']

        if not king or king.has_moved:
            return moves

        kx, ky = king.position

        for rook in rooks:
            if rook.has_moved:
                continue

            rx, ry = rook.position
            is_kingside = rx > kx

            # Chess960 castling target rule
            king_dest_x = 6 if is_kingside else 2
            rook_dest_x = 5 if is_kingside else 3

            king_dest = (king_dest_x, ky)
            rook_dest = (rook_dest_x, ky)

            min_x = min(kx, rx, king_dest_x, rook_dest_x)
            max_x = max(kx, rx, king_dest_x, rook_dest_x)
            path_clear = True

            all_pieces = self.white_pieces + self.black_pieces
            for x in range(min_x, max_x + 1):
                if x == kx or x == rx:
                    continue
                if any(p.position == [x, ky] for p in all_pieces):
                    path_clear = False
                    break

            if not path_clear:
                continue

            king_min_x = min(kx, king_dest_x)
            king_max_x = max(kx, king_dest_x)
            safe_path = True

            # C4.8 slider-masking fix: vacate the king (and the rook, which also
            # moves) while scanning the king's path so a slider behind the king's
            # origin is not masked by the king/rook still standing there.
            with simulated_move(self, None, None, cap_pos=king.get_pos()), \
                    simulated_move(self, None, None, cap_pos=rook.get_pos()):
                for x in range(king_min_x, king_max_x + 1):
                    if self.is_square_under_attack((x, ky), opp_color):
                        safe_path = False
                        break

            if not safe_path:
                continue
            moves.append((king_dest, rook_dest))

        return moves

    # ----------------------------------------------------------- apply a move

    def move_piece(self, piece, new_pos) -> bool:
        """Apply a (already-legal) move to the board, with all bookkeeping.

        Handles en-passant capture, the double-step en-passant target, normal
        captures, captured-piece bookkeeping and ``last_move``. Returns ``False``
        without mutating if the destination holds a king (defensive — kings are
        never legally capturable), else ``True``.

        Note: no timing side effects live here (those belong to the game/render
        layer); the headless core is deterministic and display-free.
        """
        old_col, old_row = piece.position

        # En-passant capture: remove the pawn that double-stepped past us.
        ep_sq = self._ep_capture_square(piece, new_pos)
        if ep_sq is not None:
            cap = self.get_piece_at_position(ep_sq)
            if cap:
                if cap.color == WHITE:
                    self.white_pieces.remove(cap)
                    self.captured_white.append(cap)
                else:
                    self.black_pieces.remove(cap)
                    self.captured_black.append(cap)
                self._on_square_set(cap.position[0], cap.position[1], None)

        # Set / clear the en-passant target for this side.
        if piece.piece_type == 'pawn' and abs(old_row - new_pos[1]) == 2:
            mid_y = (old_row + new_pos[1]) // 2
            if piece.color == WHITE:
                self.white_ep = (new_pos[0], mid_y)
            else:
                self.black_ep = (new_pos[0], mid_y)
        else:
            if piece.color == WHITE:
                self.white_ep = None
            else:
                self.black_ep = None

        # Normal capture on the destination square.
        cap = self.get_piece_at_position(new_pos)
        if cap:
            if cap.piece_type == 'king':
                return False
            if cap.color == WHITE:
                self.white_pieces.remove(cap)
                self.captured_white.append(cap)
            else:
                self.black_pieces.remove(cap)
                self.captured_black.append(cap)

        self._on_square_set(old_col, old_row, None)
        self.last_move = ((old_col, old_row), tuple(new_pos))
        piece.move(new_pos)
        self._on_square_set(new_pos[0], new_pos[1], piece)
        return True

    def castle(self, king, rook, king_dest, rook_dest) -> None:
        """Apply a (legal) Chess960 castling move: king -> ``king_dest``, rook ->
        ``rook_dest``.

        Unlike two separate ``move_piece`` calls, this clears both origin squares
        *before* placing either piece, so the king moving onto the rook's square
        (common in Chess960) does not spuriously "capture" the rook. Castling is
        never a capture and resets the en-passant target.
        """
        king_from = tuple(king.position)
        rook_from = tuple(rook.position)

        # Lift both pieces off the board first.
        self._on_square_set(king_from[0], king_from[1], None)
        self._on_square_set(rook_from[0], rook_from[1], None)

        # Castling clears any en-passant target for the moving side.
        if king.color == WHITE:
            self.white_ep = None
        else:
            self.black_ep = None

        king.move(king_dest)
        rook.move(rook_dest)
        self._on_square_set(king_dest[0], king_dest[1], king)
        self._on_square_set(rook_dest[0], rook_dest[1], rook)
        self.last_move = (king_from, tuple(king_dest))

    # --------------------------------------------------------------- draw rules

    def _castling_signature(self) -> Tuple:
        """Hashable castling-rights component: the squares of every king and
        rook that has **not** moved (so retains castling potential).

        Using ``has_moved`` rather than tracking an explicit rights mask keeps
        this consistent with how :meth:`check_castling` decides legality.
        """
        squares = []
        for p in self.white_pieces + self.black_pieces:
            if p.piece_type in ('king', 'rook') and not p.has_moved:
                squares.append((p.color, p.piece_type, tuple(p.position)))
        return tuple(sorted(squares))

    def position_signature(self, side_to_move: str) -> Hashable:
        """A hashable key identifying a position for repetition detection.

        Per FIXLIST A10 the signature = piece placement + side-to-move +
        castling rights (king/rook ``has_moved``) + en-passant target square.
        Two positions with the same signature are "the same position" for the
        threefold-repetition rule.
        """
        placement = tuple(sorted(
            (tuple(p.position), p.color, p.piece_type)
            for p in self.white_pieces + self.black_pieces
        ))
        return (
            placement,
            side_to_move,
            self._castling_signature(),
            self.white_ep,
            self.black_ep,
        )

    def record_position(self, side_to_move: str) -> None:
        """Append the current position's signature to the repetition history.

        Call this once after each ply, passing the side that is now to move.
        """
        self.position_history.append(self.position_signature(side_to_move))

    def is_threefold_repetition(self) -> bool:
        """True if the most recent recorded position has occurred >= 3 times."""
        if not self.position_history:
            return False
        last = self.position_history[-1]
        return self.position_history.count(last) >= 3

    def is_insufficient_material(self) -> bool:
        """True if neither side has sufficient material to checkmate.

        Mirrors python-chess ``is_insufficient_material()``: K vs K, K + a
        single minor (bishop or knight) vs K, and any number of bishops all on
        the same color square (with no knights/pawns) on each side. This is the
        per-color check applied to both sides.
        """
        return self._has_insufficient_material(WHITE) and \
            self._has_insufficient_material(BLACK)

    def _has_insufficient_material(self, color: str) -> bool:
        """Faithful port of python-chess ``has_insufficient_material(color)``."""
        own = self.white_pieces if color == WHITE else self.black_pieces
        opp = self.black_pieces if color == WHITE else self.white_pieces

        # Pawns, rooks or queens are always (potentially) winning material.
        if any(p.piece_type in ('pawn', 'rook', 'queen') for p in own):
            return False

        own_knights = [p for p in own if p.piece_type == 'knight']
        own_bishops = [p for p in own if p.piece_type == 'bishop']

        if own_knights:
            # Knights: insufficient only if this side has nothing but the king
            # and a single knight, and the opponent has only king/queen.
            own_non_king = [p for p in own if p.piece_type != 'king']
            opp_threat = any(
                p.piece_type not in ('king', 'queen') for p in opp
            )
            return len(own_non_king) <= 1 and not opp_threat

        if own_bishops:
            # All bishops on the board (both sides) must share one square color,
            # and there must be no knights or pawns anywhere.
            all_bishops = [
                p for p in self.white_pieces + self.black_pieces
                if p.piece_type == 'bishop'
            ]
            colors = {(p.position[0] + p.position[1]) % 2 for p in all_bishops}
            same_color = len(colors) <= 1
            any_knight = any(
                p.piece_type == 'knight'
                for p in self.white_pieces + self.black_pieces
            )
            any_pawn = any(
                p.piece_type == 'pawn'
                for p in self.white_pieces + self.black_pieces
            )
            return same_color and not any_knight and not any_pawn

        # King alone.
        return True
