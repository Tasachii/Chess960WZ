import pygame
import math
from constants import *
from square import Square
from chess_piece import make_piece


class ChessBoard:
    def __init__(self, screen):
        self.screen = screen
        self.squares = [[Square(col, row) for row in range(8)] for col in range(8)]
        self.white_pieces = []
        self.black_pieces = []
        self.captured_white = []
        self.captured_black = []
        self.notation_log = []
        self.last_move = None

        self.white_ep = (100, 100)
        self.black_ep = (100, 100)
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
        except:
            self.font = pygame.font.SysFont('Arial', 20)
            self.medium_font = pygame.font.SysFont('Arial', 40)
            self.big_font = pygame.font.SysFont('Arial', 50)
            self.small_font = pygame.font.SysFont('Arial', 14)

    def setup_board(self, back_rank=None):
        self.white_pieces = []
        self.black_pieces = []
        self.captured_white = []
        self.captured_black = []
        self.notation_log = []
        self.white_ep = (100, 100)
        self.black_ep = (100, 100)
        self.last_move = None

        # Reset square grid sync
        for col in range(8):
            for row in range(8):
                self.squares[col][row].piece = None

        if back_rank is None:
            back_rank = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']

        # Setup pieces and sync with square grid
        for col, pt in enumerate(back_rank):
            wp = make_piece(pt, WHITE, (col, 0), self)
            bp = make_piece(pt, BLACK, (col, 7), self)
            self.white_pieces.append(wp)
            self.black_pieces.append(bp)
            self.squares[col][0].piece = wp
            self.squares[col][7].piece = bp

        for col in range(8):
            wp = make_piece('pawn', WHITE, (col, 1), self)
            bp = make_piece('pawn', BLACK, (col, 6), self)
            self.white_pieces.append(wp)
            self.black_pieces.append(bp)
            self.squares[col][1].piece = wp
            self.squares[col][6].piece = bp

    def add_notation(self, text):
        self.notation_log.append(text)

    def draw_common_menu_elements(self):
        self.screen.fill(self.menu_bg_top)
        pygame.draw.rect(self.screen, self.menu_bg_bottom, pygame.Rect(0, HEIGHT // 2, WIDTH, HEIGHT // 2))
        sq = 60
        for row in range(HEIGHT // sq + 1):
            for col in range(WIDTH // sq + 1):
                if (row + col) % 2 == 0:
                    pygame.draw.rect(self.screen, self.menu_grid, pygame.Rect(col * sq, row * sq, sq, sq))

    def draw_board(self, flipped=False):
        self.draw_common_menu_elements()
        margin = (800 - (8 * self.square_size)) // 2
        start_x = margin
        start_y = margin

        pygame.draw.line(self.screen, GOLD, (800, 0), (800, 900), 2)
        pygame.draw.line(self.screen, GOLD, (0, 800), (800, 800), 2)

        for row in range(8):
            for col in range(8):
                screen_row = row if flipped else 7 - row
                screen_col = 7 - col if flipped else col
                rect = [start_x + screen_col * self.square_size, start_y + screen_row * self.square_size,
                        self.square_size, self.square_size]

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
                    sx = 7 - pos[0] if flipped else pos[0]
                    sy = pos[1] if flipped else 7 - pos[1]
                    self.screen.blit(highlight_surface,
                                     (start_x + sx * self.square_size, start_y + sy * self.square_size))

        try:
            lf = pygame.font.Font('freesansbold.ttf', 16)
        except:
            lf = pygame.font.SysFont('Arial', 16)

        for i in range(8):
            fl_idx = 7 - i if flipped else i
            fl = chr(65 + fl_idx)
            x = start_x + i * self.square_size + self.square_size // 2 - 5
            self.screen.blit(lf.render(fl, True, CREAM_WHITE), (x, 10))
            self.screen.blit(lf.render(fl, True, CREAM_WHITE), (x, 770))

            rk_val = i + 1 if flipped else 8 - i
            rk = str(rk_val)
            y = start_y + i * self.square_size + self.square_size // 2 - 5
            self.screen.blit(lf.render(rk, True, CREAM_WHITE), (10, y))
            self.screen.blit(lf.render(rk, True, CREAM_WHITE), (770, y))

    def draw_menu(self):
        self.draw_common_menu_elements()
        try:
            title_font = pygame.font.Font('freesansbold.ttf', 72)
            sub_font = pygame.font.Font('freesansbold.ttf', 20)
            btn_font = pygame.font.Font('freesansbold.ttf', 36)
            info_font = pygame.font.Font('freesansbold.ttf', 15)
        except:
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

    def draw_status_area(self, turn_step, white_time=0, black_time=0):
        status_panel_x = 800

        turn_text = "White's Turn" if turn_step < 2 else "Black's Turn"
        ind_color = WHITE if turn_step < 2 else BLACK
        txt_color = BLACK if turn_step < 2 else WHITE
        turn_rect = pygame.Rect(30, 820, 180, 60)
        pygame.draw.rect(self.screen, ind_color, turn_rect, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, turn_rect, 3, border_radius=10)
        try:
            tf = pygame.font.Font('freesansbold.ttf', 28)
            timef = pygame.font.Font('freesansbold.ttf', 32)
        except:
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

        bar_x, bar_y, bar_w, bar_h = 530, 845, 230, 10
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

        w_res = pygame.Rect(status_panel_x + 30, 700, 170, 40)
        pygame.draw.rect(self.screen, LIGHT_GRAY, w_res, border_radius=8)
        pygame.draw.rect(self.screen, DARK_RED, w_res, 2, border_radius=8)
        w_txt = self.small_font.render("White Resign", True, DARK_RED)
        self.screen.blit(w_txt, w_txt.get_rect(center=w_res.center))

        b_res = pygame.Rect(status_panel_x + 210, 700, 170, 40)
        pygame.draw.rect(self.screen, LIGHT_GRAY, b_res, border_radius=8)
        pygame.draw.rect(self.screen, DARK_RED, b_res, 2, border_radius=8)
        b_txt = self.small_font.render("Black Resign", True, DARK_RED)
        self.screen.blit(b_txt, b_txt.get_rect(center=b_res.center))

        quit_btn = pygame.Rect(status_panel_x + 30, 760, 350, 50)
        pygame.draw.rect(self.screen, (200, 50, 50), quit_btn, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, quit_btn, 2, border_radius=8)
        q_txt = self.font.render("Quit", True, CREAM_WHITE)
        self.screen.blit(q_txt, q_txt.get_rect(center=quit_btn.center))

    def draw_pieces(self, turn_step, selection, flipped=False):
        margin = (800 - (8 * self.square_size)) // 2
        start_x = margin
        start_y = margin

        for i, piece in enumerate(self.white_pieces):
            x, y = piece.position
            sx = 7 - x if flipped else x
            sy = y if flipped else 7 - y
            screen_x = start_x + sx * self.square_size
            screen_y = start_y + sy * self.square_size
            ox = (self.square_size - piece.image.get_width()) // 2
            oy = (self.square_size - piece.image.get_height()) // 2
            self.screen.blit(piece.image, (screen_x + ox, screen_y + oy))
            if turn_step < 2 and selection == i:
                pygame.draw.rect(self.screen, RED,
                                 [screen_x + 2, screen_y + 2, self.square_size - 4, self.square_size - 4], 3,
                                 border_radius=5)

        for i, piece in enumerate(self.black_pieces):
            x, y = piece.position
            sx = 7 - x if flipped else x
            sy = y if flipped else 7 - y
            screen_x = start_x + sx * self.square_size
            screen_y = start_y + sy * self.square_size
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
        except:
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

    def draw_valid_moves(self, valid_moves, turn_step, flipped=False):
        margin = (800 - (8 * self.square_size)) // 2
        start_x = margin
        start_y = margin

        color = RED if turn_step < 2 else BLUE
        for x, y in valid_moves:
            sx = 7 - x if flipped else x
            sy = y if flipped else 7 - y
            cx = start_x + sx * self.square_size + self.square_size // 2
            cy = start_y + sy * self.square_size + self.square_size // 2
            surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            c = color if isinstance(color, tuple) else pygame.Color(color)
            pygame.draw.circle(surf, (*c[:3], 150), (10, 10), 10)
            self.screen.blit(surf, (cx - 10, cy - 10))

    def draw_check(self, counter, flipped=False):
        margin = (800 - (8 * self.square_size)) // 2
        start_x = margin
        start_y = margin

        check = False
        pulse = 4 + abs(math.sin(counter * 0.2) * 3)

        for king, opponent, ring_color in [
            (next((p for p in self.white_pieces if p.piece_type == 'king'), None), self.black_pieces, DARK_RED),
            (next((p for p in self.black_pieces if p.piece_type == 'king'), None), self.white_pieces, DARK_BLUE),
        ]:
            if king:
                for op in opponent:
                    if king.get_pos() in op.get_valid_moves():
                        check = True
                        x, y = king.position
                        sx = 7 - x if flipped else x
                        sy = y if flipped else 7 - y
                        screen_x = start_x + sx * self.square_size
                        screen_y = start_y + sy * self.square_size
                        pygame.draw.rect(self.screen, ring_color,
                                         [screen_x - pulse, screen_y - pulse, self.square_size + pulse * 2,
                                          self.square_size + pulse * 2],
                                         int(pulse), border_radius=5)
        return check

    def draw_promotion(self, color, turn_step):
        panel = pygame.Rect(850, 200, 300, 450)
        pygame.draw.rect(self.screen, (45, 45, 60), panel, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, panel, 4, border_radius=15)
        title = self.medium_font.render("Promote", True, CREAM_WHITE)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 30)))
        pygame.draw.line(self.screen, GOLD, (panel.x + 20, panel.y + 60), (panel.right - 20, panel.y + 60), 2)

        for i, pt in enumerate(PROMOTION_PIECES):
            piece = make_piece(pt, color, (0, 0), self)
            opt = pygame.Rect(panel.x + 50, panel.y + 80 + i * 90, 200, 70)
            bg = LIGHT_BLUE if i == self.highlight_promotion_option else CREAM_WHITE
            pygame.draw.rect(self.screen, bg, opt, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, opt, 2, border_radius=10)
            self.screen.blit(piece.image, (opt.x + 20, opt.y + (opt.height - piece.image.get_height()) // 2))
            nm = self.font.render(pt.capitalize(), True, BLACK)
            self.screen.blit(nm, nm.get_rect(midleft=(opt.x + 100, opt.centery)))

    def draw_castling(self, castling_moves, turn_step, flipped=False):
        margin = (800 - (8 * self.square_size)) // 2
        start_x = margin
        start_y = margin

        color = RED if turn_step < 2 else BLUE
        for king_pos, rook_pos in castling_moves:
            kx, ky = king_pos
            rx, ry = rook_pos

            ksx = 7 - kx if flipped else kx
            ksy = ky if flipped else 7 - ky
            rsx = 7 - rx if flipped else rx
            rsy = ry if flipped else 7 - ry

            kcx = start_x + ksx * self.square_size + self.square_size // 2
            kcy = start_y + ksy * self.square_size + self.square_size // 2
            rcx = start_x + rsx * self.square_size + self.square_size // 2
            rcy = start_y + rsy * self.square_size + self.square_size // 2

            pygame.draw.line(self.screen, color, (kcx, kcy + 20), (rcx, rcy + 20), 3)
            pygame.draw.circle(self.screen, color, (kcx, kcy + 20), 10)
            pygame.draw.circle(self.screen, color, (rcx, rcy + 20), 10)

    def get_square_under_mouse(self, pos, flipped=False):
        margin = (800 - (8 * self.square_size)) // 2
        start_x = margin
        start_y = margin

        vx = (pos[0] - start_x) // self.square_size
        vy = (pos[1] - start_y) // self.square_size

        if vx < 0 or vx >= 8 or vy < 0 or vy >= 8:
            return None

        if flipped:
            x = 7 - vx
            y = vy
        else:
            x = vx
            y = 7 - vy

        return (x, y)

    def is_king_in_check(self, color):
        king = next((p for p in (self.white_pieces if color == WHITE else self.black_pieces) if p.piece_type == 'king'),
                    None)
        if not king: return False
        opp = self.black_pieces if color == WHITE else self.white_pieces
        return any(king.get_pos() in p.get_valid_moves() for p in opp)

    def is_square_under_attack(self, position, attacking_color):
        pieces = self.white_pieces if attacking_color == WHITE else self.black_pieces
        return any(position in p.get_valid_moves() for p in pieces)

    def _has_legal_moves(self, color):
        # Ghost pawn fix correctly integrated for simulations
        pieces = self.white_pieces if color == WHITE else self.black_pieces
        for p in pieces:
            orig = list(p.position)
            for m in p.get_valid_moves():
                cap_pos = m
                if p.piece_type == 'pawn':
                    if p.color == WHITE and tuple(m) == self.black_ep:
                        cap_pos = (m[0], m[1] - 1)
                    elif p.color == BLACK and tuple(m) == self.white_ep:
                        cap_pos = (m[0], m[1] + 1)

                cap = self.get_piece_at_position(cap_pos)
                if cap:
                    if cap.color == WHITE:
                        self.white_pieces.remove(cap)
                    else:
                        self.black_pieces.remove(cap)

                p.position = list(m)
                safe = not self.is_king_in_check(color)
                p.position = orig

                if cap:
                    if cap.color == WHITE:
                        self.white_pieces.append(cap)
                    else:
                        self.black_pieces.append(cap)

                if safe: return True
        return False

    def is_checkmate(self, color):
        return self.is_king_in_check(color) and not self._has_legal_moves(color)

    def is_stalemate(self, color):
        return not self.is_king_in_check(color) and not self._has_legal_moves(color)

    def check_castling(self, color):
        moves = []
        if self.is_king_in_check(color):
            return moves

        pieces = self.white_pieces if color == WHITE else self.black_pieces
        opp_color = BLACK if color == WHITE else WHITE
        king = next((p for p in pieces if p.piece_type == 'king'), None)
        rooks = [p for p in pieces if p.piece_type == 'rook']

        if not king or king.has_moved:
            return moves

        kx, ky = king.position

        for rook in rooks:
            if rook.has_moved: continue

            rx, ry = rook.position
            is_kingside = rx > kx

            # Chess960 castling target rule
            king_dest_x = 6 if is_kingside else 2
            rook_dest_x = 5 if is_kingside else 3

            king_dest = (king_dest_x, ky)
            rook_dest = (rook_dest_x, ky)

            min_x = min(kx, rx, king_dest_x, rook_dest_x)
            max_x = max(kx, rx, king_dest_x, rook_dest_x)
            path_clear = True

            all_pieces = self.white_pieces + self.black_pieces
            for x in range(min_x, max_x + 1):
                if x == kx or x == rx: continue
                if any(p.position == [x, ky] for p in all_pieces):
                    path_clear = False
                    break

            if not path_clear: continue

            king_min_x = min(kx, king_dest_x)
            king_max_x = max(kx, king_dest_x)
            safe_path = True

            for x in range(king_min_x, king_max_x + 1):
                if self.is_square_under_attack((x, ky), opp_color):
                    safe_path = False
                    break

            if not safe_path: continue
            moves.append((king_dest, rook_dest))

        return moves

    def get_piece_at_position(self, position):
        for p in self.white_pieces + self.black_pieces:
            if tuple(p.position) == tuple(position):
                return p
        return None

    def get_all_piece_positions(self):
        return [tuple(p.position) for p in self.white_pieces + self.black_pieces]

    def get_piece_positions(self, color):
        pieces = self.white_pieces if color == WHITE else self.black_pieces
        return [tuple(p.position) for p in pieces]

    def get_opponent_positions(self, color):
        pieces = self.black_pieces if color == WHITE else self.white_pieces
        return [tuple(p.position) for p in pieces]

    def get_en_passant_square(self, color):
        return self.white_ep if color == WHITE else self.black_ep

    def set_playing_side(self, as_white):
        self.playing_as_white = as_white