import random

from chess_core.sp_number import back_rank_to_sp_number, sp_number_to_back_rank


class Chess960Generator:
    """
    Generates a valid Chess960 back-rank using the 5-step combinatorial algorithm.
    Total: 4 × 4 × 6 × 10 × 1 = 960 unique positions.
    """

    @staticmethod
    def generate():
        """Return list of 8 piece names for the back rank (col 0-7)."""
        back_rank = [None] * 8

        # step 1 — dark bishop on dark squares (cols 1,3,5,7 for row 0)
        # a square is dark if (col + row) % 2 == 1, row=0 so col must be odd
        dark_squares = [1, 3, 5, 7]
        back_rank[random.choice(dark_squares)] = 'bishop'

        # step 2 — light bishop on light squares (cols 0,2,4,6)
        light_squares = [0, 2, 4, 6]
        back_rank[random.choice(light_squares)] = 'bishop'

        # step 3 — queen on one of 6 remaining empty squares
        empty = [i for i, p in enumerate(back_rank) if p is None]
        back_rank[random.choice(empty)] = 'queen'

        # step 4 — 2 knights on 2 of 5 remaining squares
        empty = [i for i, p in enumerate(back_rank) if p is None]
        knight_squares = random.sample(empty, 2)
        for sq in knight_squares:
            back_rank[sq] = 'knight'

        # step 5 — remaining 3 squares get rook, king, rook (in that order)
        # king must be between the rooks — the only valid arrangement is R K R
        empty = [i for i, p in enumerate(back_rank) if p is None]
        # empty is exactly 3 squares; left→right = rook, king, rook
        back_rank[empty[0]] = 'rook'
        back_rank[empty[1]] = 'king'
        back_rank[empty[2]] = 'rook'

        return back_rank

    @staticmethod
    def sp_number(back_rank):
        """Return the Scharnagl SP-number (0-959) for ``back_rank``."""
        return back_rank_to_sp_number(back_rank)

    @staticmethod
    def from_sp_number(n):
        """Return the back-rank for SP-number ``n`` (0-959)."""
        return sp_number_to_back_rank(n)

    @staticmethod
    def generate_with_sp_number():
        """Like :meth:`generate` but also return the position's SP-number.

        Returns ``(back_rank, sp_number)``.
        """
        back_rank = Chess960Generator.generate()
        return back_rank, back_rank_to_sp_number(back_rank)

    @staticmethod
    def starting_fen(back_rank):
        """Build the Shredder-FEN string for the generated position.

        The castling field uses the file letters of the rooks (Shredder-FEN),
        not the X-FEN ``KQkq`` shorthand, which is only unambiguous when the
        rooks are the outermost back-rank pieces. White rooks are rendered as
        uppercase file letters and black rooks as lowercase, ordered by file
        descending to match python-chess (e.g. back-rank ``nrkrbqbn`` -> ``DBdb``).
        """
        piece_chars = {
            'king': 'k', 'queen': 'q', 'rook': 'r',
            'bishop': 'b', 'knight': 'n', 'pawn': 'p'
        }
        black_back = ''.join(piece_chars[p] for p in back_rank)
        white_back = black_back.upper()

        rook_cols = [c for c, p in enumerate(back_rank) if p == 'rook']
        white_castle = ''.join(chr(ord('A') + c) for c in sorted(rook_cols, reverse=True))
        black_castle = white_castle.lower()
        castling = white_castle + black_castle if rook_cols else '-'

        fen = f"{black_back}/pppppppp/8/8/8/8/PPPPPPPP/{white_back} w {castling} - 0 1"
        return fen