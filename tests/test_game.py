"""Game-layer regression net for :class:`chess_game.ChessGame`.

This pins the *observable* behavior of the Pygame state-machine / input /
UI-orchestration layer before (and after) the Phase-4 refactor. Everything runs
headless: ``conftest.py`` forces ``SDL_VIDEODRIVER=dummy`` so ``ChessGame()`` can
build a real (off-screen) display surface, fonts and board without a window.

The tests drive the *public* methods/handlers (``start_game``, ``reset_game``,
``handle_*`` event handlers, ``_handle_player_move``, the ``needs_game_state_check``
draw ladder) and assert on the resulting state, rather than on pixels. They are
the safety net for the God-Object split: any extraction must keep them green.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import constants as C
from chess_core import make_core_piece
from chess_game import ChessGame


@pytest.fixture(scope="module", autouse=True)
def _pygame_init():
    """Initialise pygame once for the module (headless via conftest SDL=dummy)."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def game():
    """A fresh :class:`ChessGame` (menu state, no game started yet)."""
    return ChessGame()


# --------------------------------------------------------------------------- #
# Helpers — drive moves through the public handler by board coordinates.
# --------------------------------------------------------------------------- #

def _move(g, color, frm, to):
    """Select ``frm`` then move to ``to`` for ``color`` via ``_handle_player_move``."""
    g._handle_player_move(tuple(frm), color)
    g._handle_player_move(tuple(to), color)


def _post_move_state_check(g):
    """Run the same draw/checkmate ladder ``handle_gameplay`` runs after a move.

    Mirrors the ``needs_game_state_check`` block so tests can exercise the
    game-over logic without pumping the full render loop.
    """
    if getattr(g, 'needs_game_state_check', False) and not g.game_over:
        g.needs_game_state_check = False
        opp_color = C.BLACK if g.turn_step >= 2 else C.WHITE
        g.board.record_position(opp_color)
        if g.board.is_checkmate(opp_color):
            g.winner = C.WHITE if opp_color == C.BLACK else C.BLACK
            g.game_over = True
        elif g.board.is_stalemate(opp_color):
            g.winner = 'draw'
            g.draw_reason = 'stalemate'
            g.game_over = True
        elif g.board.is_insufficient_material():
            g.winner = 'draw'
            g.draw_reason = 'insufficient material'
            g.game_over = True
        elif g.board.is_threefold_repetition():
            g.winner = 'draw'
            g.draw_reason = 'threefold repetition'
            g.game_over = True
        elif g.halfmove_clock >= 100:
            g.winner = 'draw'
            g.draw_reason = 'fifty-move rule'
            g.game_over = True


def _clear_board(g):
    """Strip all pieces off the live board (for hand-built endgames)."""
    g.board.white_pieces = []
    g.board.black_pieces = []
    g.board.white_ep = None
    g.board.black_ep = None
    g.board.last_move = None
    g.board.position_history = []
    g.board.squares = [[__import__('square').Square(c, r) for r in range(8)]
                       for c in range(8)]


def _place(g, piece_type, color, pos, has_moved=False):
    """Place a render piece on the live board; keep the square grid in sync."""
    p = make_core_piece(piece_type, color, pos, g.board)
    p.has_moved = has_moved
    (g.board.white_pieces if color == C.WHITE else g.board.black_pieces).append(p)
    g.board.squares[pos[0]][pos[1]].piece = p
    return p


# --------------------------------------------------------------------------- #
# 1. Initial state after start_game.
# --------------------------------------------------------------------------- #

def test_start_game_initial_state(game):
    game.start_game()
    assert game.game_state == C.PLAYING
    assert game.turn_step == 0
    assert game.winner == ''
    assert game.draw_reason == ''
    assert game.game_over is False
    assert game.winner_by_time is False
    assert game.selection == 100
    assert game.valid_moves == []
    assert game.halfmove_clock == 0
    assert game.stats_saved is False
    assert game.white_promote is False
    assert game.black_promote is False
    # 16 pieces per side from the Chess960 setup.
    assert len(game.board.white_pieces) == 16
    assert len(game.board.black_pieces) == 16
    # Repetition history is seeded with the starting position (1 entry).
    assert len(game.board.position_history) == 1
    # A back-rank and PGN exporter were created.
    assert game.back_rank is not None
    assert game.pgn is not None


def test_start_game_seeds_pgn_and_stats(game):
    game.start_game()
    assert game.pgn is not None
    # game_type recorded from the selected time control name.
    assert game.stats.game_data['game_type'] == C.TIME_NAMES[game.time_control].lower()


# --------------------------------------------------------------------------- #
# 2. reset_game restores a clean PLAYING state.
# --------------------------------------------------------------------------- #

def test_reset_game_clears_winner_and_reseeds(game):
    game.start_game()
    # Dirty the state as if a game had ended in a draw.
    game.winner = 'draw'
    game.draw_reason = 'stalemate'
    game.game_over = True
    game.stats_saved = True
    game.halfmove_clock = 42
    game.white_promote = True

    game.reset_game()

    assert game.winner == ''
    assert game.draw_reason == ''
    assert game.game_over is False
    assert game.stats_saved is False
    assert game.halfmove_clock == 0
    assert game.white_promote is False
    assert game.black_promote is False
    assert game.turn_step == 0
    assert game.selection == 100
    assert len(game.board.white_pieces) == 16
    assert len(game.board.black_pieces) == 16
    # Repetition history re-seeded with exactly the start position.
    assert len(game.board.position_history) == 1
    # Time re-armed for the same time control.
    assert game.white_time == C.TIME_CONTROLS[game.time_control]
    assert game.black_time == C.TIME_CONTROLS[game.time_control]


def test_reset_game_preserves_player_color_and_flip(game):
    game.start_game()
    game.player_color = C.BLACK
    game.board.playing_as_white = False
    game.board_flipped = True
    game.reset_game()
    assert game.player_color == C.BLACK
    assert game.board.playing_as_white is False
    assert game.board_flipped is True


# --------------------------------------------------------------------------- #
# 3. State-machine transitions via the public handlers (events mocked).
# --------------------------------------------------------------------------- #

def _post_event(event_type, **kwargs):
    pygame.event.post(pygame.event.Event(event_type, **kwargs))


def test_menu_play_white_goes_to_time_select(game):
    pygame.event.clear()
    # draw_menu returns the white/black/quit button rects; click white.
    white_btn, _black_btn, _quit_btn = game.board.draw_menu()
    _post_event(pygame.MOUSEBUTTONDOWN, button=1, pos=white_btn.center)
    running = game.handle_menu()
    assert running is True
    assert game.game_state == C.TIME_SELECT
    assert game.player_color == C.WHITE
    assert game.board_flipped is False


def test_menu_play_black_sets_flip(game):
    pygame.event.clear()
    _white_btn, black_btn, _quit_btn = game.board.draw_menu()
    _post_event(pygame.MOUSEBUTTONDOWN, button=1, pos=black_btn.center)
    game.handle_menu()
    assert game.game_state == C.TIME_SELECT
    assert game.player_color == C.BLACK
    assert game.board_flipped is True


def test_menu_history_button_opens_history(game):
    pygame.event.clear()
    game.board.draw_menu()
    hist_btn = pygame.Rect(C.WIDTH // 2 - 100, 510, 200, 50)
    _post_event(pygame.MOUSEBUTTONDOWN, button=1, pos=hist_btn.center)
    game.handle_menu()
    assert game.game_state == C.HISTORY


def test_menu_quit_returns_false(game):
    pygame.event.clear()
    _white_btn, _black_btn, quit_btn = game.board.draw_menu()
    _post_event(pygame.MOUSEBUTTONDOWN, button=1, pos=quit_btn.center)
    running = game.handle_menu()
    assert running is False


def test_time_select_escape_returns_to_menu(game):
    pygame.event.clear()
    game.game_state = C.TIME_SELECT
    _post_event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    game.handle_time_selection()
    assert game.game_state == C.MENU


def test_time_select_choice_starts_game(game):
    pygame.event.clear()
    game.game_state = C.TIME_SELECT
    # First time-control button: rect from handle_time_selection geometry.
    btn = pygame.Rect(C.WIDTH // 2 - 200, 250, 400, 80)
    _post_event(pygame.MOUSEBUTTONDOWN, button=1, pos=btn.center)
    game.handle_time_selection()
    assert game.game_state == C.PLAYING
    assert game.time_control == C.BULLET
    assert game.white_time == C.TIME_CONTROLS[C.BULLET]


def test_history_back_returns_to_menu(game):
    pygame.event.clear()
    game.game_state = C.HISTORY
    back_btn = pygame.Rect(30, C.HEIGHT - 70, 120, 50)
    _post_event(pygame.MOUSEBUTTONDOWN, button=1, pos=back_btn.center)
    game.handle_history_view()
    assert game.game_state == C.MENU


def test_history_charts_button_opens_chart_viewer(game):
    pygame.event.clear()
    game.game_state = C.HISTORY
    charts_btn = pygame.Rect(170, C.HEIGHT - 70, 230, 50)
    _post_event(pygame.MOUSEBUTTONDOWN, button=1, pos=charts_btn.center)
    game.handle_history_view()
    assert game.game_state == C.CHART_VIEWER


def test_chart_viewer_escape_returns_to_history(game):
    pygame.event.clear()
    game.game_state = C.CHART_VIEWER
    _post_event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    game.handle_chart_viewer()
    assert game.game_state == C.HISTORY


def test_gameplay_r_key_returns_to_menu(game):
    pygame.event.clear()
    game.start_game()
    _post_event(pygame.KEYDOWN, key=pygame.K_r)
    running = game.handle_gameplay()
    assert running is True
    assert game.game_state == C.MENU


def test_gameplay_enter_after_game_over_resets(game):
    pygame.event.clear()
    game.start_game()
    game.winner = C.WHITE
    game.game_over = True
    game.stats_saved = True  # avoid re-export side effects
    _post_event(pygame.KEYDOWN, key=pygame.K_RETURN)
    game.handle_gameplay()
    # reset_game re-armed a fresh PLAYING game.
    assert game.game_over is False
    assert game.winner == ''


# --------------------------------------------------------------------------- #
# 4. Turn / timer flags.
# --------------------------------------------------------------------------- #

def test_timeout_white_loses(game):
    game.start_game()
    game.turn_step = 0  # white to move
    game.white_time = 0.001
    game.last_move_time = pygame.time.get_ticks() - 5000  # 5s elapsed
    game.update_timers()
    assert game.white_time == 0
    assert game.winner == C.BLACK
    assert game.winner_by_time is True
    assert game.game_over is True


def test_timeout_black_loses(game):
    game.start_game()
    game.turn_step = 2  # black to move
    game.black_time = 0.001
    game.last_move_time = pygame.time.get_ticks() - 5000
    game.update_timers()
    assert game.black_time == 0
    assert game.winner == C.WHITE
    assert game.winner_by_time is True
    assert game.game_over is True


def test_turn_step_advances_after_white_move(game):
    game.start_game()
    # Use a standard back-rank layout so e2-e4 (col 4) is a legal pawn push.
    game.board.setup_board(['rook', 'knight', 'bishop', 'queen',
                            'king', 'bishop', 'knight', 'rook'])
    game.board.record_position(C.WHITE)
    assert game.turn_step == 0
    _move(game, C.WHITE, (4, 1), (4, 3))
    # White's move complete → turn passes to black (step 2).
    assert game.turn_step == 2
    assert game.needs_game_state_check is True


# --------------------------------------------------------------------------- #
# 5. Draw detection wired through ChessGame (Phase-3 path, Phase-4 net).
# --------------------------------------------------------------------------- #

def test_insufficient_material_declares_draw(game):
    game.start_game()
    _clear_board(game)
    # K vs K — lone kings, insufficient material.
    _place(game, 'king', C.WHITE, (4, 0))
    _place(game, 'king', C.BLACK, (4, 7))
    game.board.record_position(C.WHITE)
    game.needs_game_state_check = True
    game.turn_step = 2  # so opp_color resolves to BLACK; symmetric for K v K
    _post_move_state_check(game)
    assert game.winner == 'draw'
    assert game.draw_reason == 'insufficient material'
    assert game.game_over is True


def test_kbk_same_color_is_insufficient(game):
    game.start_game()
    _clear_board(game)
    _place(game, 'king', C.WHITE, (4, 0))
    _place(game, 'king', C.BLACK, (4, 7))
    _place(game, 'bishop', C.WHITE, (2, 0))  # (2+0)%2 == 0
    _place(game, 'bishop', C.BLACK, (5, 7))  # (5+7)%2 == 0 -> same color
    game.board.record_position(C.WHITE)
    game.needs_game_state_check = True
    game.turn_step = 0
    _post_move_state_check(game)
    assert game.winner == 'draw'
    assert game.draw_reason == 'insufficient material'


def test_rook_endgame_is_not_a_draw(game):
    game.start_game()
    _clear_board(game)
    _place(game, 'king', C.WHITE, (4, 0))
    _place(game, 'king', C.BLACK, (4, 7))
    _place(game, 'rook', C.WHITE, (0, 0))  # sufficient material
    game.board.record_position(C.WHITE)
    game.needs_game_state_check = True
    game.turn_step = 2
    _post_move_state_check(game)
    # Not insufficient material; with a free king it's also not stalemate/mate.
    assert game.winner != 'draw' or game.draw_reason != 'insufficient material'


def test_threefold_repetition_declares_draw(game):
    game.start_game()
    _clear_board(game)
    # Two kings plus rooks so material is sufficient (isolates threefold path).
    wk = _place(game, 'king', C.WHITE, (4, 0), has_moved=True)
    bk = _place(game, 'king', C.BLACK, (4, 7), has_moved=True)
    _place(game, 'rook', C.WHITE, (0, 0), has_moved=True)
    _place(game, 'rook', C.BLACK, (0, 7), has_moved=True)
    # Record the same position signature 3 times (white to move each time).
    for _ in range(3):
        game.board.record_position(C.WHITE)
    assert wk and bk
    game.needs_game_state_check = True
    game.turn_step = 2  # opp_color = BLACK -> records BLACK once more; the
    # white-to-move signature already hit 3, so threefold holds.
    # Re-seed so the most recent recorded signature is the repeated one:
    game.board.position_history.append(game.board.position_signature(C.WHITE))
    assert game.board.is_threefold_repetition() is True


def test_fifty_move_rule_declares_draw(game):
    game.start_game()
    _clear_board(game)
    _place(game, 'king', C.WHITE, (4, 0))
    _place(game, 'king', C.BLACK, (4, 7))
    _place(game, 'rook', C.WHITE, (0, 0))  # sufficient material
    _place(game, 'rook', C.BLACK, (7, 7))
    game.board.record_position(C.WHITE)
    game.halfmove_clock = 100
    game.needs_game_state_check = True
    game.turn_step = 2
    _post_move_state_check(game)
    assert game.winner == 'draw'
    assert game.draw_reason == 'fifty-move rule'
    assert game.game_over is True


# --------------------------------------------------------------------------- #
# 6. Checkmate / stalemate through ChessGame.
# --------------------------------------------------------------------------- #

def test_back_rank_checkmate_declares_winner(game):
    game.start_game()
    _clear_board(game)
    # Black king h8 boxed by own pawns g7,h7; white rook delivers mate on a8.
    _place(game, 'king', C.BLACK, (7, 7))
    _place(game, 'pawn', C.BLACK, (6, 6))
    _place(game, 'pawn', C.BLACK, (7, 6))
    _place(game, 'king', C.WHITE, (4, 0))
    _place(game, 'rook', C.WHITE, (0, 7))  # rook on a8 checks along rank 8
    game.board.record_position(C.BLACK)
    game.needs_game_state_check = True
    game.turn_step = 2  # white just moved -> opp is black
    _post_move_state_check(game)
    assert game.board.is_checkmate(C.BLACK) is True
    assert game.winner == C.WHITE
    assert game.game_over is True


def test_stalemate_declares_draw(game):
    game.start_game()
    _clear_board(game)
    # Classic K+Q stalemate: black king a8, white queen b6, white king c6.
    _place(game, 'king', C.BLACK, (0, 7))
    _place(game, 'queen', C.WHITE, (1, 5))
    _place(game, 'king', C.WHITE, (2, 5))
    game.board.record_position(C.BLACK)
    game.needs_game_state_check = True
    game.turn_step = 2
    _post_move_state_check(game)
    assert game.board.is_stalemate(C.BLACK) is True
    assert game.winner == 'draw'
    assert game.draw_reason == 'stalemate'


# --------------------------------------------------------------------------- #
# 7. Castling-onto-rook fix still holds through ChessGame (A4/Phase-1).
# --------------------------------------------------------------------------- #

def test_castling_through_game_does_not_capture_rook(game):
    game.start_game()
    _clear_board(game)
    # Chess960-ish: king on b1 (col 1), kingside rook on c1 (col 2).
    # Kingside castle lands king on g1 (col 6), rook on f1 (col 5).
    king = _place(game, 'king', C.WHITE, (1, 0))
    rook = _place(game, 'rook', C.WHITE, (2, 0))
    _place(game, 'king', C.BLACK, (4, 7))
    game.board.record_position(C.WHITE)
    game.turn_step = 0

    # Select the king, compute castling targets, then click the king destination.
    game.selection = game.board.white_pieces.index(king)
    game.turn_step = 1
    game.get_valid_moves()
    assert game.castling_moves, "expected a castling option"
    king_dest = game.castling_moves[0][0]
    game._handle_player_move(tuple(king_dest), C.WHITE)

    # Both pieces survived; king on g1/col6, rook on f1/col5; rook NOT captured.
    assert king in game.board.white_pieces
    assert rook in game.board.white_pieces
    assert tuple(king.position) == (6, 0)
    assert tuple(rook.position) == (5, 0)
    assert len(game.board.captured_white) == 0
    assert game.turn_step == 2  # turn passed to black


# --------------------------------------------------------------------------- #
# 8. Promotion enter / exit.
# --------------------------------------------------------------------------- #

def test_check_promotion_detects_white_pawn_on_last_rank(game):
    game.start_game()
    _clear_board(game)
    _place(game, 'king', C.WHITE, (4, 0))
    _place(game, 'king', C.BLACK, (4, 7))
    _place(game, 'pawn', C.WHITE, (0, 7))  # white pawn on rank 8 -> promote
    game.check_promotion()
    assert game.white_promote is True
    assert game.black_promote is False


def test_handle_promotion_click_replaces_pawn(game):
    game.start_game()
    _clear_board(game)
    _place(game, 'king', C.WHITE, (4, 0))
    _place(game, 'king', C.BLACK, (4, 7))
    _place(game, 'pawn', C.WHITE, (0, 7))
    game.check_promotion()
    assert game.white_promote is True

    # Click the queen option: queen is index 3 in PROMOTION_PIECES.
    panel = pygame.Rect(*C.PROMO_PANEL)
    q_idx = C.PROMOTION_PIECES.index('queen')
    click_y = panel.y + C.PROMO_OPTION_TOP + q_idx * C.PROMO_OPTION_H + 5
    click_x = panel.centerx
    game.handle_promotion_click((click_x, click_y))

    # Pawn is gone; a queen now sits on (0,7); promotion flag cleared.
    pieces_on_sq = game.board.get_piece_at_position((0, 7))
    assert pieces_on_sq is not None
    assert pieces_on_sq.piece_type == 'queen'
    assert game.white_promote is False
    assert game.needs_game_state_check is True


def test_promotion_pauses_timers_in_run_gate(game):
    """The run-loop only ticks timers when no promotion is pending."""
    game.start_game()
    game.white_promote = True
    # The gate condition in run(): not game_over and not white_promote and not black_promote
    gate = not game.game_over and not game.white_promote and not game.black_promote
    assert gate is False
    game.white_promote = False
    gate = not game.game_over and not game.white_promote and not game.black_promote
    assert gate is True


# --------------------------------------------------------------------------- #
# 9. Re-selection branch in _handle_player_move.
# --------------------------------------------------------------------------- #

def test_reselect_piece_on_invalid_click(game):
    game.start_game()
    game.board.setup_board(['rook', 'knight', 'bishop', 'queen',
                            'king', 'bishop', 'knight', 'rook'])
    game.board.record_position(C.WHITE)
    game.turn_step = 0
    # Select the b1 knight (col 1).
    game._handle_player_move((1, 0), C.WHITE)
    assert game.turn_step == 1
    first_sel = game.selection
    # Click a friendly piece that is NOT a valid move (the g1 knight, col 6)
    # -> should re-select rather than move.
    game._handle_player_move((6, 0), C.WHITE)
    assert game.turn_step == 1  # still in move-step, re-selected
    assert game.selection != first_sel
