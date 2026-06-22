"""Pygame render layer for chess pieces.

The pure move-generation logic lives in :mod:`chess_core.pieces`; this module
only adds image loading on top of those classes. Each render piece subclasses
its pure core counterpart and the :class:`PieceRenderMixin`, so ``get_valid_moves``
/ ``get_attack_squares`` come straight from the (tested, headless) core while the
``image`` / ``small_image`` surfaces are built here.
"""
import pygame

from chess_core.pieces import Bishop as CoreBishop
from chess_core.pieces import King as CoreKing
from chess_core.pieces import Knight as CoreKnight
from chess_core.pieces import Pawn as CorePawn
from chess_core.pieces import PieceCore
from chess_core.pieces import Queen as CoreQueen
from chess_core.pieces import Rook as CoreRook
from constants import CREAM_WHITE, GOLD, WHITE

# Re-export the pure base so existing ``from chess_piece import ChessPiece`` and
# isinstance checks keep working.
ChessPiece = PieceCore


class PieceRenderMixin:
    """Adds pygame image loading to a pure core piece."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_image()

    def load_image(self):
        color_name = "white" if self.color == WHITE else "black"
        try:
            img = pygame.image.load(f"images/{color_name} {self.piece_type}.png")
            size = 65 if self.piece_type == 'pawn' else 70
            self.image = pygame.transform.scale(img, (size, size))
            self.small_image = pygame.transform.scale(self.image, (40, 40))
        except (pygame.error, FileNotFoundError):
            # fallback when piece images are missing
            self.image = self._placeholder()
            self.small_image = pygame.transform.scale(self.image, (40, 40))

    def _placeholder(self):
        surf = pygame.Surface((70, 70), pygame.SRCALPHA)
        bg = CREAM_WHITE if self.color == WHITE else (50, 50, 50)
        pygame.draw.rect(surf, bg, (0, 0, 70, 70))
        try:
            font = pygame.font.Font('freesansbold.ttf', 20)
        except pygame.error:
            font = pygame.font.SysFont('Arial', 20)
        txt_color = (50, 50, 50) if self.color == WHITE else CREAM_WHITE
        txt = font.render(self.piece_type[0].upper(), True, txt_color)
        surf.blit(txt, txt.get_rect(center=(35, 35)))
        pygame.draw.rect(surf, GOLD, (0, 0, 70, 70), 2)
        return surf


class Pawn(PieceRenderMixin, CorePawn):
    pass


class Rook(PieceRenderMixin, CoreRook):
    pass


class Knight(PieceRenderMixin, CoreKnight):
    pass


class Bishop(PieceRenderMixin, CoreBishop):
    pass


class Queen(PieceRenderMixin, CoreQueen):
    pass


class King(PieceRenderMixin, CoreKing):
    pass


def make_piece(piece_type, color, position, board):
    """Factory — returns the right render subclass (with images)."""
    mapping = {
        'pawn': Pawn,
        'rook': Rook,
        'knight': Knight,
        'bishop': Bishop,
        'queen': Queen,
        'king': King,
    }
    cls = mapping.get(piece_type)
    if cls:
        return cls(color, position, board)
    raise ValueError(f"Unknown piece type: {piece_type}")
