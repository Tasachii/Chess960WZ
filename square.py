from constants import WHITE, BLACK


class Square:
    """One cell on the board."""
    def __init__(self, col, row):
        self.col = col   # 0-7 (x)
        self.row = row   # 0-7 (y)
        self.piece = None
        # light square if (col+row) % 2 == 0
        self.color = WHITE if (col + row) % 2 == 0 else BLACK

    @property
    def position(self):
        return (self.col, self.row)

    def is_empty(self):
        return self.piece is None

    def has_enemy(self, color):
        return self.piece is not None and self.piece.color != color

    def has_ally(self, color):
        return self.piece is not None and self.piece.color == color

    def __repr__(self):
        return f"Square({self.col},{self.row} piece={self.piece})"
