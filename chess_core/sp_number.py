"""Scharnagl SP-number <-> Chess960 back-rank mapping (no pygame).

A "Starting Position number" (SP-number, 0-959) uniquely identifies one of the
960 Chess960 / Fischer-random back-ranks via Reinhard Scharnagl's numbering
scheme. SP-518 is the orthodox ``RNBQKBNR`` arrangement.

The two functions here are exact inverses of each other and agree with
``python-chess`` (``chess.Board.from_chess960_pos`` / ``chess960_pos``) for every
``n`` in ``range(960)``; the test suite cross-checks this.

Back-ranks are represented the same way as :mod:`chess960_generator`: a list of
8 piece-type strings (``'rook'``, ``'knight'``, ``'bishop'``, ``'queen'``,
``'king'``) indexed by file/column 0-7.
"""
from typing import List

__all__ = ["STANDARD_SP_NUMBER", "sp_number_to_back_rank", "back_rank_to_sp_number"]

# The 10 ways to place the two knights among the 5 squares left after the
# bishops and queen are placed (Scharnagl's KN-table), as (lo, hi) index pairs
# into the remaining empty squares.
_KNIGHT_TABLE = [
    (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 2), (1, 3), (1, 4),
    (2, 3), (2, 4),
    (3, 4),
]

STANDARD_SP_NUMBER = 518  # RNBQKBNR


def sp_number_to_back_rank(n: int) -> List[str]:
    """Return the back-rank (list of 8 piece-type strings) for SP-number ``n``.

    ``n`` must be in ``range(960)``. The light-square bishop, dark-square bishop,
    queen, the two knights, and finally rook-king-rook (king strictly between the
    rooks) are placed per the Scharnagl algorithm.
    """
    if not 0 <= n <= 959:
        raise ValueError(f"SP-number out of range [0, 959]: {n}")

    back_rank: List[str] = [None] * 8  # type: ignore[list-item]

    n2, light_b = divmod(n, 4)   # light-square bishop -> files 1,3,5,7
    n3, dark_b = divmod(n2, 4)   # dark-square bishop  -> files 0,2,4,6
    n4, queen = divmod(n3, 6)    # queen among the 6 remaining empty squares

    back_rank[2 * light_b + 1] = 'bishop'
    back_rank[2 * dark_b] = 'bishop'

    empty = [i for i, p in enumerate(back_rank) if p is None]
    back_rank[empty[queen]] = 'queen'

    empty = [i for i, p in enumerate(back_rank) if p is None]
    lo, hi = _KNIGHT_TABLE[n4]
    back_rank[empty[lo]] = 'knight'
    back_rank[empty[hi]] = 'knight'

    empty = [i for i, p in enumerate(back_rank) if p is None]
    back_rank[empty[0]] = 'rook'
    back_rank[empty[1]] = 'king'
    back_rank[empty[2]] = 'rook'

    return back_rank


def back_rank_to_sp_number(back_rank: List[str]) -> int:
    """Inverse of :func:`sp_number_to_back_rank` (Scharnagl).

    Returns the SP-number (0-959) for a valid Chess960 ``back_rank``. Raises
    ``ValueError`` if the arrangement is not a legal Chess960 back-rank
    (wrong piece multiset, same-color bishops, or king not between the rooks).
    """
    if len(back_rank) != 8:
        raise ValueError(f"back_rank must have 8 entries, got {len(back_rank)}")

    bishops = [i for i, p in enumerate(back_rank) if p == 'bishop']
    queens = [i for i, p in enumerate(back_rank) if p == 'queen']
    knights = [i for i, p in enumerate(back_rank) if p == 'knight']
    rooks = [i for i, p in enumerate(back_rank) if p == 'rook']
    kings = [i for i, p in enumerate(back_rank) if p == 'king']

    if not (len(bishops) == 2 and len(queens) == 1 and len(knights) == 2
            and len(rooks) == 2 and len(kings) == 1):
        raise ValueError(f"not a valid Chess960 back-rank: {back_rank}")

    light = [i for i in bishops if i % 2 == 1]
    dark = [i for i in bishops if i % 2 == 0]
    if len(light) != 1 or len(dark) != 1:
        raise ValueError(f"bishops must be on opposite colors: {back_rank}")

    if not (rooks[0] < kings[0] < rooks[1]):
        raise ValueError(f"king must be strictly between the rooks: {back_rank}")

    light_b = (light[0] - 1) // 2
    dark_b = dark[0] // 2

    # Queen index among the squares left empty after both bishops are placed.
    after_bishops = [i for i in range(8) if i not in (light[0], dark[0])]
    queen = after_bishops.index(queens[0])

    # Knight pair index among the squares left after bishops + queen.
    after_queen = [i for i in after_bishops if i != queens[0]]
    knight_pair = (after_queen.index(knights[0]), after_queen.index(knights[1]))
    knight_pair = (min(knight_pair), max(knight_pair))
    n4 = _KNIGHT_TABLE.index(knight_pair)

    return ((n4 * 6 + queen) * 4 + dark_b) * 4 + light_b
