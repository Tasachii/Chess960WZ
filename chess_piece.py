import pygame
from constants import WHITE, BLACK, CREAM_WHITE, GOLD


class ChessPiece:
    """Base class for all chess pieces."""
    def __init__(self, piece_type, color, position, board):
        self.piece_type = piece_type
        self.color = color
        self.position = list(position)  # [col, row]
        self.board = board
        self.has_moved = False
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
        except:
            font = pygame.font.SysFont('Arial', 20)
        txt_color = (50, 50, 50) if self.color == WHITE else CREAM_WHITE
        txt = font.render(self.piece_type[0].upper(), True, txt_color)
        surf.blit(txt, txt.get_rect(center=(35, 35)))
        pygame.draw.rect(surf, GOLD, (0, 0, 70, 70), 2)
        return surf

    def get_pos(self):
        return tuple(self.position)

    def move(self, new_pos):
        self.position = list(new_pos)
        self.has_moved = True

    def get_valid_moves(self):
        # subclasses override
        return []

    def get_attack_squares(self):
        """
        Squares this piece attacks regardless of occupancy.
        Default = same as get_valid_moves(). Pawn overrides because its
        capture squares differ from its move squares.
        """
        return self.get_valid_moves()

    def _in_bounds(self, col, row):
        return 0 <= col <= 7 and 0 <= row <= 7

    def __repr__(self):
        return f"{self.color[0].upper()}{self.piece_type[:2]}@{tuple(self.position)}"


class Pawn(ChessPiece):
    def __init__(self, color, position, board):
        super().__init__('pawn', color, position, board)

    def get_valid_moves(self):
        moves = []
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
        for dc in [-1, 1]:
            if (col + dc, row + direction) == ep_sq:
                moves.append((col + dc, row + direction))

        return moves

    def get_attack_squares(self):
        """Pawn attacks both diagonals whether occupied or not."""
        col, row = self.position
        direction = 1 if self.color == WHITE else -1
        out = []
        for dc in [-1, 1]:
            sq = (col + dc, row + direction)
            if self._in_bounds(*sq):
                out.append(sq)
        return out


class Rook(ChessPiece):
    def __init__(self, color, position, board):
        super().__init__('rook', color, position, board)

    def get_valid_moves(self):
        return self._slide([(0, 1), (0, -1), (1, 0), (-1, 0)])

    def _slide(self, directions):
        moves = []
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


class Knight(ChessPiece):
    def __init__(self, color, position, board):
        super().__init__('knight', color, position, board)

    def get_valid_moves(self):
        col, row = self.position
        ally_pos = self.board.get_piece_positions(self.color)
        jumps = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                 (1, 2), (1, -2), (-1, 2), (-1, -2)]
        return [
            (col + dc, row + dr)
            for dc, dr in jumps
            if self._in_bounds(col + dc, row + dr) and (col + dc, row + dr) not in ally_pos
        ]


class Bishop(ChessPiece):
    def __init__(self, color, position, board):
        super().__init__('bishop', color, position, board)

    def get_valid_moves(self):
        return self._slide([(1, 1), (1, -1), (-1, 1), (-1, -1)])

    def _slide(self, directions):
        moves = []
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


class Queen(ChessPiece):
    def __init__(self, color, position, board):
        super().__init__('queen', color, position, board)

    def get_valid_moves(self):
        return self._slide([(0, 1), (0, -1), (1, 0), (-1, 0),
                            (1, 1), (1, -1), (-1, 1), (-1, -1)])

    def _slide(self, directions):
        moves = []
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


class King(ChessPiece):
    def __init__(self, color, position, board):
        super().__init__('king', color, position, board)

    def get_valid_moves(self):
        col, row = self.position
        ally_pos = self.board.get_piece_positions(self.color)
        moves = []
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                pos = (col + dc, row + dr)
                if self._in_bounds(*pos) and pos not in ally_pos:
                    moves.append(pos)
        return moves


def make_piece(piece_type, color, position, board):
    """Factory — returns the right subclass."""
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