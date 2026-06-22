"""Pure chess-piece move generation (no pygame).

Each piece exposes ``get_valid_moves()`` (pseudo-legal moves, ignoring whether
the move leaves one's own king in check) and ``get_attack_squares()`` (the
squares the piece attacks for check/threat detection). Legality (king safety) is
applied by the board, not here.

Positions are ``(col, row)`` with ``0 <= col,row <= 7`` and white starting on
rows 0-1, black on rows 6-7.
"""
from typing import TYPE_CHECKING, List, Tuple

from constants import BLACK, WHITE

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .board import CoreBoard

Coord = Tuple[int, int]


class PieceCore:
    """Base class for all pure (UI-free) chess pieces."""

    def __init__(self, piece_type: str, color: str, position, board: "CoreBoard") -> None:
        self.piece_type = piece_type
        self.color = color
        self.position = list(position)  # [col, row]
        self.board = board
        self.has_moved = False

    def get_pos(self) -> Coord:
        return tuple(self.position)

    def move(self, new_pos) -> None:
        self.position = list(new_pos)
        self.has_moved = True

    def get_valid_moves(self) -> List[Coord]:
        # subclasses override
        return []

    def _slide(self, directions) -> List[Coord]:
        """Slide along each (dc, dr) direction until blocked.

        Stops before an ally, includes (and stops on) the first enemy.
        Shared by Rook, Bishop, and Queen.
        """
        moves: List[Coord] = []
        col, row = self.position
        ally_pos = self.board.get_piece_positions(self.color)
        opp_pos = self.board.get_opponent_positions(self.color)
        for dc, dr in directions:
            for d in range(1, 8):
                nc, nr = col + dc * d, row + dr * d
                if not self._in_bounds(nc, nr):
                    break
                pos = (nc, nr)
                if pos in ally_pos:
                    break
                moves.append(pos)
                if pos in opp_pos:
                    break
        return moves

    def get_attack_squares(self) -> List[Coord]:
        """Squares this piece attacks regardless of occupancy.

        Default = same as ``get_valid_moves()``. Pawn overrides because its
        capture squares differ from its move squares.
        """
        return self.get_valid_moves()

    def _in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col <= 7 and 0 <= row <= 7

    def __repr__(self) -> str:
        return f"{self.color[0].upper()}{self.piece_type[:2]}@{tuple(self.position)}"


class Pawn(PieceCore):
    def __init__(self, color: str, position, board: "CoreBoard") -> None:
        super().__init__('pawn', color, position, board)

    def get_valid_moves(self) -> List[Coord]:
        moves: List[Coord] = []
        col, row = self.position
        direction = 1 if self.color == WHITE else -1
        all_pos = self.board.get_all_piece_positions()
        opp_pos = self.board.get_opponent_positions(self.color)

        # forward 1
        if self._in_bounds(col, row + direction) and (col, row + direction) not in all_pos:
            moves.append((col, row + direction))
            # forward 2 from start
            if not self.has_moved and (col, row + 2 * direction) not in all_pos:
                moves.append((col, row + 2 * direction))

        # diagonal captures
        for dc in [-1, 1]:
            cap = (col + dc, row + direction)
            if cap in opp_pos:
                moves.append(cap)

        # en passant
        ep_color = BLACK if self.color == WHITE else WHITE
        ep_sq = self.board.get_en_passant_square(ep_color)
        if ep_sq is not None:
            for dc in [-1, 1]:
                if (col + dc, row + direction) == ep_sq:
                    moves.append((col + dc, row + direction))

        return moves

    def get_attack_squares(self) -> List[Coord]:
        """Pawn attacks both diagonals whether occupied or not."""
        col, row = self.position
        direction = 1 if self.color == WHITE else -1
        out: List[Coord] = []
        for dc in [-1, 1]:
            sq = (col + dc, row + direction)
            if self._in_bounds(*sq):
                out.append(sq)
        return out


class Rook(PieceCore):
    def __init__(self, color: str, position, board: "CoreBoard") -> None:
        super().__init__('rook', color, position, board)

    def get_valid_moves(self) -> List[Coord]:
        return self._slide([(0, 1), (0, -1), (1, 0), (-1, 0)])


class Knight(PieceCore):
    def __init__(self, color: str, position, board: "CoreBoard") -> None:
        super().__init__('knight', color, position, board)

    def get_valid_moves(self) -> List[Coord]:
        col, row = self.position
        ally_pos = self.board.get_piece_positions(self.color)
        jumps = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                 (1, 2), (1, -2), (-1, 2), (-1, -2)]
        return [
            (col + dc, row + dr)
            for dc, dr in jumps
            if self._in_bounds(col + dc, row + dr) and (col + dc, row + dr) not in ally_pos
        ]


class Bishop(PieceCore):
    def __init__(self, color: str, position, board: "CoreBoard") -> None:
        super().__init__('bishop', color, position, board)

    def get_valid_moves(self) -> List[Coord]:
        return self._slide([(1, 1), (1, -1), (-1, 1), (-1, -1)])


class Queen(PieceCore):
    def __init__(self, color: str, position, board: "CoreBoard") -> None:
        super().__init__('queen', color, position, board)

    def get_valid_moves(self) -> List[Coord]:
        return self._slide([(0, 1), (0, -1), (1, 0), (-1, 0),
                            (1, 1), (1, -1), (-1, 1), (-1, -1)])


class King(PieceCore):
    def __init__(self, color: str, position, board: "CoreBoard") -> None:
        super().__init__('king', color, position, board)

    def get_valid_moves(self) -> List[Coord]:
        col, row = self.position
        ally_pos = self.board.get_piece_positions(self.color)
        moves: List[Coord] = []
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                pos = (col + dc, row + dr)
                if self._in_bounds(*pos) and pos not in ally_pos:
                    moves.append(pos)
        return moves


CORE_PIECE_CLASSES = {
    'pawn': Pawn,
    'rook': Rook,
    'knight': Knight,
    'bishop': Bishop,
    'queen': Queen,
    'king': King,
}


def make_core_piece(piece_type: str, color: str, position, board: "CoreBoard") -> PieceCore:
    """Factory — returns the right pure-piece subclass."""
    cls = CORE_PIECE_CLASSES.get(piece_type)
    if cls:
        return cls(color, position, board)
    raise ValueError(f"Unknown piece type: {piece_type}")
