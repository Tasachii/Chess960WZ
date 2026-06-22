"""Pygame render layer for the chess board.

All rules/state logic lives in :class:`chess_core.board.CoreBoard`; ``ChessBoard``
subclasses it and adds only the Pygame ``screen``/font/drawing code. The board
state, move generation, check/checkmate/stalemate, Chess960 castling and en
passant are inherited from the (headless, tested) core. ``setup_board`` keeps the
auxiliary ``squares`` grid in sync via the core's ``_on_square_set`` hook.
"""
import math
from typing import List, Optional, Tuple

import pygame

from chess_core.board import CoreBoard
from chess_piece import make_piece
from constants import *
from square import Square

Coord = Tuple[int, int]


class ChessBoard(CoreBoard):
    def __init__(self, screen) -> None:
        # Build pure-core state, injecting the render-piece factory so pieces
        # carry images.
        super().__init__(piece_factory=make_piece)

        self.screen = screen
        self.squares = [[Square(col, row) for row in range(8)] for col in range(8)]
        self.playing_as_white = True

        self.square_size = 90
        self.start_pos = 20
        self.board_size = 800

        self.selected_piece = None
        self.highlight_promotion_option = -1

        self.color_light = (238, 238, 210)
        self.color_dark = (118, 150, 86)
        self.color_highlight = (246, 246, 130)

        self.menu_bg_top = (22, 22, 32)
        self.menu_bg_bottom = (32, 32, 48)
        self.menu_grid = (28, 28, 42)

        try:
            self.font = pygame.font.Font('freesansbold.ttf', 20)
            self.medium_font = pygame.font.Font('freesansbold.ttf', 40)
            self.big_font = pygame.font.Font('freesansbold.ttf', 50)
            self.small_font = pygame.font.Font('freesansbold.ttf', 14)
        except pygame.error:
            self.font = pygame.font.SysFont('Arial', 20)
            self.medium_font = pygame.font.SysFont('Arial', 40)
            self.big_font = pygame.font.SysFont('Arial', 50)
            self.small_font = pygame.font.SysFont('Arial', 14)

    def _on_square_set(self, col: int, row: int, piece) -> None:
        """Keep the auxiliary square grid mirror in sync with the core."""
        self.squares[col][row].piece = piece

    # --- Coordinate helpers (A17) ------------------------------------------
    # to_screen / from_screen are the single source of truth for the
    # board<->pixel mapping (and board flipping), replacing the per-method
    # ``7 - x if flipped else x`` duplication across every draw_* and the
    # mouse hit-test.

    def to_screen(self, col: int, row: int, flipped: bool = False) -> tuple[int, int]:
        """Top-left screen pixel of the cell holding board square ``(col, row)``."""
        sx = 7 - col if flipped else col
        sy = row if flipped else 7 - row
        return (BOARD_MARGIN + sx * self.square_size,
                BOARD_MARGIN + sy * self.square_size)

    def from_screen(self, x: int, y: int, flipped: bool = False) -> Optional[Coord]:
        """Board ``(col, row)`` under screen pixel ``(x, y)``, or ``None`` if off-board."""
        vx = (x - BOARD_MARGIN) // self.square_size
        vy = (y - BOARD_MARGIN) // self.square_size
        if vx < 0 or vx >= 8 or vy < 0 or vy >= 8:
            return None
        col = 7 - vx if flipped else vx
        row = vy if flipped else 7 - vy
        return (col, row)

    def setup_board(self, back_rank: Optional[List[str]] = None) -> None:
        # Reset square grid sync, then let the core rebuild the pieces (which
        # repopulates the grid via _on_square_set).
        for col in range(8):
            for row in range(8):
                self.squares[col][row].piece = None
        super().setup_board(back_rank)

    def draw_common_menu_elements(self):
        self.screen.fill(self.menu_bg_top)
        pygame.draw.rect(self.screen, self.menu_bg_bottom, pygame.Rect(0, HEIGHT // 2, WIDTH, HEIGHT // 2))
        sq = 60
        for row in range(HEIGHT // sq + 1):
            for col in range(WIDTH // sq + 1):
                if (row + col) % 2 == 0:
                    pygame.draw.rect(self.screen, self.menu_grid, pygame.Rect(col * sq, row * sq, sq, sq))

    def draw_board(self, flipped: bool = False) -> None:
        self.draw_common_menu_elements()
        start_x = BOARD_MARGIN
        start_y = BOARD_MARGIN

        pygame.draw.line(self.screen, GOLD, (BOARD_PX, 0), (BOARD_PX, HEIGHT), 2)
        pygame.draw.line(self.screen, GOLD, (0, BOARD_PX), (BOARD_PX, BOARD_PX), 2)

        for row in range(8):
            for col in range(8):
                px, py = self.to_screen(col, row, flipped)
                rect = [px, py, self.square_size, self.square_size]

                if (row + col) % 2 == 0:
                    pygame.draw.rect(self.screen, self.color_dark, rect)
                    pygame.draw.line(self.screen, self.color_highlight, (rect[0], rect[1]),
                                     (rect[0] + rect[2], rect[1]), 2)
                else:
                    pygame.draw.rect(self.screen, self.color_light, rect)

        # Highlight last move
        if self.last_move:
            highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            highlight_surface.fill((255, 255, 0, 70))
            for pos in self.last_move:
                if pos:
                    self.screen.blit(highlight_surface, self.to_screen(pos[0], pos[1], flipped))

        try:
            lf = pygame.font.Font('freesansbold.ttf', 16)
        except pygame.error:
            lf = pygame.font.SysFont('Arial', 16)

        for i in range(8):
            fl_idx = 7 - i if flipped else i
            fl = chr(65 + fl_idx)
            x = start_x + i * self.square_size + self.square_size // 2 - 5
            self.screen.blit(lf.render(fl, True, CREAM_WHITE), (x, 10))
            self.screen.blit(lf.render(fl, True, CREAM_WHITE), (x, BOARD_PX - 30))

            rk_val = i + 1 if flipped else 8 - i
            rk = str(rk_val)
            y = start_y + i * self.square_size + self.square_size // 2 - 5
            self.screen.blit(lf.render(rk, True, CREAM_WHITE), (10, y))
            self.screen.blit(lf.render(rk, True, CREAM_WHITE), (BOARD_PX - 30, y))

    def draw_menu(self):
        self.draw_common_menu_elements()
        try:
            title_font = pygame.font.Font('freesansbold.ttf', 72)
            sub_font = pygame.font.Font('freesansbold.ttf', 20)
            btn_font = pygame.font.Font('freesansbold.ttf', 36)
            info_font = pygame.font.Font('freesansbold.ttf', 15)
        except pygame.error:
            title_font = sub_font = btn_font = info_font = pygame.font.SysFont('Arial', 32)

        for dx, dy, alpha in [(6, 6, 60), (4, 4, 100), (2, 2, 150)]:
            sh = title_font.render("CHESS 960 WZ", True, WOOD_DARK)
            sh.set_alpha(alpha)
            self.screen.blit(sh, sh.get_rect(center=(WIDTH // 2 + dx, 148 + dy)))

        title = title_font.render("CHESS 960 WZ", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 148)))

        sub = sub_font.render("Fischer Random Chess  -  960 Unique Starting Positions", True, LIGHT_GRAY)
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 208)))
        pygame.draw.line(self.screen, GOLD, (WIDTH // 2 - 280, 228), (WIDTH // 2 + 280, 228), 1)

        mouse_pos = pygame.mouse.get_pos()
        white_btn = pygame.Rect(WIDTH // 2 - 190, 258, 380, 88)
        black_btn = pygame.Rect(WIDTH // 2 - 190, 372, 380, 88)

        for btn, label, fg, bg, accent in [
            (white_btn, "Play as White", (20, 20, 20), (235, 235, 215), CREAM_WHITE),
            (black_btn, "Play as Black", CREAM_WHITE, (22, 22, 32), (80, 80, 100)),
        ]:
            hover = btn.collidepoint(mouse_pos)
            if hover:
                glow = btn.inflate(12, 12)
                pygame.draw.rect(self.screen, LIGHT_BLUE, glow, border_radius=18)
            pygame.draw.rect(self.screen, bg, btn, border_radius=14)
            border_col = GOLD if hover else (100, 85, 50)
            pygame.draw.rect(self.screen, border_col, btn, 3, border_radius=14)
            icon_rect = pygame.Rect(btn.x + 20, btn.centery - 20, 40, 40)
            pygame.draw.rect(self.screen, accent, icon_rect, border_radius=6)
            txt = btn_font.render(label, True, fg)
            self.screen.blit(txt, txt.get_rect(midleft=(btn.x + 75, btn.centery)))

        quit_btn = pygame.Rect(WIDTH - 130, 24, 100, 40)
        hover_q = quit_btn.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, (80, 20, 20) if hover_q else (50, 20, 20), quit_btn, border_radius=8)
        pygame.draw.rect(self.screen, DARK_RED, quit_btn, 2, border_radius=8)
        qt = self.font.render("X  Quit", True, (220, 100, 100))
        self.screen.blit(qt, qt.get_rect(center=quit_btn.center))

        hint = info_font.render("F - Flip Board   |   R - Return to Menu during game", True, (80, 80, 100))
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 28)))

        return white_btn, black_btn, quit_btn

    def draw_status_area(self, turn_step: int, white_time: float = 0, black_time: float = 0) -> None:
        turn_text = "White's Turn" if turn_step < 2 else "Black's Turn"
        ind_color = WHITE if turn_step < 2 else BLACK
        txt_color = BLACK if turn_step < 2 else WHITE
        turn_rect = pygame.Rect(30, 820, 180, 60)
        pygame.draw.rect(self.screen, ind_color, turn_rect, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, turn_rect, 3, border_radius=10)
        try:
            tf = pygame.font.Font('freesansbold.ttf', 28)
            timef = pygame.font.Font('freesansbold.ttf', 32)
        except pygame.error:
            tf = pygame.font.SysFont('Arial', 28)
            timef = pygame.font.SysFont('Arial', 32)

        lbl = tf.render(turn_text, True, txt_color)
        self.screen.blit(lbl, lbl.get_rect(center=turn_rect.center))

        for time_val, rect_x, bg, fg in [
            (white_time, 240, WHITE, BLACK),
            (black_time, 380, BLACK, WHITE),
        ]:
            mins, secs = int(time_val) // 60, int(time_val) % 60
            tstr = f"{mins:02d}:{secs:02d}"
            trect = pygame.Rect(rect_x, 820, 120, 60)
            pygame.draw.rect(self.screen, bg, trect, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, trect, 3, border_radius=10)
            tl = timef.render(tstr, True, fg)
            self.screen.blit(tl, tl.get_rect(center=trect.center))

        # Material Advantage Bar implementation
        piece_values = {'pawn': 1, 'knight': 3, 'bishop': 3, 'rook': 5, 'queen': 9, 'king': 0}
        w_score = sum(piece_values.get(p.piece_type, 0) for p in self.white_pieces)
        b_score = sum(piece_values.get(p.piece_type, 0) for p in self.black_pieces)
        diff = w_score - b_score

        bar_x, bar_y, bar_w, bar_h = MATERIAL_BAR
        pygame.draw.rect(self.screen, (30, 30, 30), [bar_x, bar_y, bar_w, bar_h])
        max_adv = 15
        clamped_diff = max(min(diff, max_adv), -max_adv)
        fill_width = int(bar_w / 2 + (clamped_diff / max_adv) * (bar_w / 2))

        pygame.draw.rect(self.screen, CREAM_WHITE, [bar_x, bar_y, fill_width, bar_h])
        pygame.draw.rect(self.screen, GOLD, [bar_x, bar_y, bar_w, bar_h], 1)

        if diff > 0:
            txt = self.small_font.render(f"+{diff}", True, CREAM_WHITE)
            self.screen.blit(txt, (bar_x - 30, bar_y - 3))
        elif diff < 0:
            txt = self.small_font.render(f"+{-diff}", True, (50, 50, 50))
            self.screen.blit(txt, (bar_x + bar_w + 10, bar_y - 3))

        w_res = pygame.Rect(*RESIGN_WHITE_RECT)
        pygame.draw.rect(self.screen, LIGHT_GRAY, w_res, border_radius=8)
        pygame.draw.rect(self.screen, DARK_RED, w_res, 2, border_radius=8)
        w_txt = self.small_font.render("White Resign", True, DARK_RED)
        self.screen.blit(w_txt, w_txt.get_rect(center=w_res.center))

        b_res = pygame.Rect(*RESIGN_BLACK_RECT)
        pygame.draw.rect(self.screen, LIGHT_GRAY, b_res, border_radius=8)
        pygame.draw.rect(self.screen, DARK_RED, b_res, 2, border_radius=8)
        b_txt = self.small_font.render("Black Resign", True, DARK_RED)
        self.screen.blit(b_txt, b_txt.get_rect(center=b_res.center))

        quit_btn = pygame.Rect(*STATUS_QUIT_RECT)
        pygame.draw.rect(self.screen, (200, 50, 50), quit_btn, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, quit_btn, 2, border_radius=8)
        q_txt = self.font.render("Quit", True, CREAM_WHITE)
        self.screen.blit(q_txt, q_txt.get_rect(center=quit_btn.center))

    def draw_pieces(self, turn_step: int, selection: int, flipped: bool = False) -> None:
        for i, piece in enumerate(self.white_pieces):
            screen_x, screen_y = self.to_screen(piece.position[0], piece.position[1], flipped)
            ox = (self.square_size - piece.image.get_width()) // 2
            oy = (self.square_size - piece.image.get_height()) // 2
            self.screen.blit(piece.image, (screen_x + ox, screen_y + oy))
            if turn_step < 2 and selection == i:
                pygame.draw.rect(self.screen, RED,
                                 [screen_x + 2, screen_y + 2, self.square_size - 4, self.square_size - 4], 3,
                                 border_radius=5)

        for i, piece in enumerate(self.black_pieces):
            screen_x, screen_y = self.to_screen(piece.position[0], piece.position[1], flipped)
            ox = (self.square_size - piece.image.get_width()) // 2
            oy = (self.square_size - piece.image.get_height()) // 2
            self.screen.blit(piece.image, (screen_x + ox, screen_y + oy))
            if turn_step >= 2 and selection == i:
                pygame.draw.rect(self.screen, BLUE,
                                 [screen_x + 2, screen_y + 2, self.square_size - 4, self.square_size - 4], 3,
                                 border_radius=5)

    def draw_notation_panel(self):
        panel = pygame.Rect(810, 150, 375, 540)
        pygame.draw.rect(self.screen, LIGHT_GRAY, panel, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, panel, 2, border_radius=10)

        try:
            title_f = pygame.font.Font('freesansbold.ttf', 18)
            move_f = pygame.font.Font('freesansbold.ttf', 14)
        except pygame.error:
            title_f = pygame.font.SysFont('Arial', 18)
            move_f = pygame.font.SysFont('Arial', 14)

        title = title_f.render("Move Notation", True, BLACK)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 18)))
        pygame.draw.line(self.screen, GOLD, (panel.x + 10, panel.y + 35), (panel.right - 10, panel.y + 35), 1)

        y_off = panel.y + 45
        max_rows = 23
        log = self.notation_log
        pairs = []
        for i in range(0, len(log), 2):
            w_move = log[i] if i < len(log) else ''
            b_move = log[i + 1] if i + 1 < len(log) else ''
            pairs.append((i // 2 + 1, w_move, b_move))

        pairs = pairs[-max_rows:]
        for move_num, w, b in pairs:
            row_txt = f"{move_num:>3}. {w:<8} {b}"
            surf = move_f.render(row_txt, True, BLACK)
            self.screen.blit(surf, (panel.x + 12, y_off))
            y_off += 20

    def draw_captured(self):
        self.draw_notation_panel()

    def draw_valid_moves(self, valid_moves: List[Coord], turn_step: int, flipped: bool = False) -> None:
        color = RED if turn_step < 2 else BLUE
        for x, y in valid_moves:
            px, py = self.to_screen(x, y, flipped)
            cx = px + self.square_size // 2
            cy = py + self.square_size // 2
            surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            c = color if isinstance(color, tuple) else pygame.Color(color)
            pygame.draw.circle(surf, (*c[:3], 150), (10, 10), 10)
            self.screen.blit(surf, (cx - 10, cy - 10))

    def draw_check(self, counter: int, flipped: bool = False) -> bool:
        check = False
        pulse = 4 + abs(math.sin(counter * 0.2) * 3)

        for king, opponent, ring_color in [
            (next((p for p in self.white_pieces if p.piece_type == 'king'), None), self.black_pieces, DARK_RED),
            (next((p for p in self.black_pieces if p.piece_type == 'king'), None), self.white_pieces, DARK_BLUE),
        ]:
            if king:
                for op in opponent:
                    if king.get_pos() in op.get_attack_squares():
                        check = True
                        screen_x, screen_y = self.to_screen(king.position[0], king.position[1], flipped)
                        pygame.draw.rect(self.screen, ring_color,
                                         [screen_x - pulse, screen_y - pulse, self.square_size + pulse * 2,
                                          self.square_size + pulse * 2],
                                         int(pulse), border_radius=5)
        return check

    def draw_promotion(self, color, turn_step):
        panel = pygame.Rect(*PROMO_PANEL)
        pygame.draw.rect(self.screen, (45, 45, 60), panel, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, panel, 4, border_radius=15)
        title = self.medium_font.render("Promote", True, CREAM_WHITE)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 30)))
        pygame.draw.line(self.screen, GOLD, (panel.x + 20, panel.y + 60), (panel.right - 20, panel.y + 60), 2)

        for i, pt in enumerate(PROMOTION_PIECES):
            piece = make_piece(pt, color, (0, 0), self)
            opt = pygame.Rect(panel.x + 50, panel.y + PROMO_OPTION_TOP + i * PROMO_OPTION_H, 200, 70)
            bg = LIGHT_BLUE if i == self.highlight_promotion_option else CREAM_WHITE
            pygame.draw.rect(self.screen, bg, opt, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, opt, 2, border_radius=10)
            self.screen.blit(piece.image, (opt.x + 20, opt.y + (opt.height - piece.image.get_height()) // 2))
            nm = self.font.render(pt.capitalize(), True, BLACK)
            self.screen.blit(nm, nm.get_rect(midleft=(opt.x + 100, opt.centery)))

    def draw_castling(self, castling_moves, turn_step: int, flipped: bool = False) -> None:
        color = RED if turn_step < 2 else BLUE
        half = self.square_size // 2
        for king_pos, rook_pos in castling_moves:
            kpx, kpy = self.to_screen(king_pos[0], king_pos[1], flipped)
            rpx, rpy = self.to_screen(rook_pos[0], rook_pos[1], flipped)

            kcx = kpx + half
            kcy = kpy + half
            rcx = rpx + half
            rcy = rpy + half

            pygame.draw.line(self.screen, color, (kcx, kcy + 20), (rcx, rcy + 20), 3)
            pygame.draw.circle(self.screen, color, (kcx, kcy + 20), 10)
            pygame.draw.circle(self.screen, color, (rcx, rcy + 20), 10)

    def get_square_under_mouse(self, pos: Coord, flipped: bool = False) -> Optional[Coord]:
        return self.from_screen(pos[0], pos[1], flipped)

    def set_playing_side(self, as_white: bool) -> None:
        self.playing_as_white = as_white
