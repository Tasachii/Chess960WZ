from constants import WHITE, BLACK

class Square:
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.piece = None
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