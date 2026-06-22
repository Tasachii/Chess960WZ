"""Pure, UI-free chess core for Chess960WZ.

This package contains the rules engine with **no** ``import pygame``: the board
and position state, move generation, legality filtering, check/checkmate/
stalemate detection, Chess960 castling, en passant, and the move-application
logic. It is import-safe with no display and is what the test suite exercises.

The Pygame ``ChessBoard``/``ChessPiece`` render classes (in ``chess_board.py`` /
``chess_piece.py``) subclass and import from here, adding only drawing.

Layering:  chess_core (no pygame)  <-  chess_board/chess_piece (render)  <-  chess_game
"""
from constants import BLACK, WHITE

from .board import CoreBoard, simulated_move
from .pieces import (
    Bishop,
    King,
    Knight,
    Pawn,
    PieceCore,
    Queen,
    Rook,
    make_core_piece,
)
from .sp_number import (
    STANDARD_SP_NUMBER,
    back_rank_to_sp_number,
    sp_number_to_back_rank,
)

__all__ = [
    "WHITE",
    "BLACK",
    "CoreBoard",
    "simulated_move",
    "PieceCore",
    "Pawn",
    "Rook",
    "Knight",
    "Bishop",
    "Queen",
    "King",
    "make_core_piece",
    "STANDARD_SP_NUMBER",
    "sp_number_to_back_rank",
    "back_rank_to_sp_number",
]
