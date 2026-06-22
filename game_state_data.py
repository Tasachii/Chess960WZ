"""Plain mutable game-state holder for :class:`chess_game.ChessGame` (A4 seam).

This is the state half of the former God Object: the ~28 scalar attributes that
make up the running game's state machine, selection, clocks, draw/winner flags
and chart-view selection. Pulling them into one dataclass groups what used to be
a flat wall of ``self.x = ...`` lines in ``ChessGame.__init__`` and gives the
state machine a single, inspectable home.

``ChessGame`` owns one ``GameState`` (``self.state``) and exposes each field via
a property so all existing ``self.turn_step`` / ``self.winner`` / ... access keeps
working unchanged — the extraction is behavior-preserving, which is what the
game-layer test net verifies.

Infrastructure objects (the pygame ``screen``, ``board``, ``clock``, fonts,
``stats``, ``pgn``) deliberately stay on ``ChessGame``: they are collaborators,
not state, and live for the lifetime of the app rather than a single game.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from constants import BLITZ, MENU, WHITE

Coord = Tuple[int, int]


@dataclass
class GameState:
    """Mutable state of one running (or pending) Chess960WZ game."""

    # --- state machine / turn ---------------------------------------------
    game_state: int = MENU
    turn_step: int = 0

    # --- current selection / move hints -----------------------------------
    selection: int = 100
    valid_moves: List[Coord] = field(default_factory=list)
    castling_moves: List[Tuple[Coord, Coord]] = field(default_factory=list)

    # --- frame / animation counters ---------------------------------------
    counter: int = 0
    check: bool = False

    # --- result / game-over flags -----------------------------------------
    winner: str = ''
    winner_by_time: bool = False
    draw_reason: str = ''
    game_over: bool = False
    needs_game_state_check: bool = False
    stats_saved: bool = False

    # --- promotion --------------------------------------------------------
    white_promote: bool = False
    black_promote: bool = False
    promo_index: int = 100

    # --- board orientation ------------------------------------------------
    board_flipped: bool = False
    last_flip_time: int = 0

    # --- 50-move clock ----------------------------------------------------
    halfmove_clock: int = 0

    # --- player / time control --------------------------------------------
    player_color: str = WHITE
    time_control: int = BLITZ
    white_time: float = 0
    black_time: float = 0
    last_move_time: int = 0
    last_move_start: int = 0

    # --- current Chess960 back-rank ---------------------------------------
    back_rank: Optional[List[str]] = None

    # --- analytics chart view selection -----------------------------------
    chart_metric: str = 'dependency'
    chart_color: str = 'all'
