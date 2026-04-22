import pygame
from constants import *
from chess_board import ChessBoard
from chess_piece import make_piece
from chess_statistics import ChessStatistics
from chess960_generator import Chess960Generator
from pgn_exporter import PGNExporter


class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode([WIDTH, HEIGHT])
        pygame.display.set_caption('Chess960WZ')
        self.clock = pygame.time.Clock()
        self.board = ChessBoard(self.screen)

        self.turn_step = 0
        self.selection = 100
        self.valid_moves = []
        self.castling_moves = []
        self.counter = 0
        self.check = False
        self.winner = ''
        self.winner_by_time = False
        self.game_over = False
        self.stats_saved = False
        self.white_promote = False
        self.black_promote = False
        self.promo_index = 100
        self.board_flipped = False
        self.last_flip_time = 0

        self.player_color = WHITE
        self.time_control = BLITZ
        self.white_time = 0
        self.black_time = 0
        self.last_move_time = 0
        self.last_move_start = 0

        self.game_state = MENU
        self.HISTORY = 4

        self.stats = ChessStatistics()
        self.pgn = None
        self.back_rank = None

        self.current_chart_index = 0
        self.chart_filter = 'all'

        try:
            self.font       = pygame.font.Font('freesansbold.ttf', 20)
            self.small_font = pygame.font.Font('freesansbold.ttf', 16)
            self.big_font   = pygame.font.Font('freesansbold.ttf', 48)
        except:
            self.font       = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
            self.big_font   = pygame.font.SysFont('Arial', 48)

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            self.counter = (self.counter + 1) % 30

            if self.game_state == MENU:
                running = self.handle_menu()
            elif self.game_state == TIME_SELECT:
                running = self.handle_time_selection()
            elif self.game_state == PLAYING:
                running = self.handle_gameplay()
                if not self.game_over and not self.white_promote and not self.black_promote:
                    self.update_timers()
            elif self.game_state == self.HISTORY:
                running = self.handle_history_view()
            elif self.game_state == CHART_VIEWER:
                running = self.handle_chart_viewer()

            pygame.display.flip()
        pygame.quit()

    def handle_menu(self):
        white_btn, black_btn, quit_btn = self.board.draw_menu()

        mouse_pos = pygame.mouse.get_pos()
        hist_btn = pygame.Rect(WIDTH//2 - 100, 510, 200, 50)
        hover = hist_btn.collidepoint(mouse_pos)
        if hover:
            pygame.draw.rect(self.screen, LIGHT_BLUE, hist_btn.inflate(8, 8), border_radius=12)
        pygame.draw.rect(self.screen, (45, 45, 55), hist_btn, border_radius=12)
        pygame.draw.rect(self.screen, GOLD if hover else WOOD_BROWN, hist_btn, 2, border_radius=12)
        ht = self.font.render("History & Stats", True, CREAM_WHITE)
        self.screen.blit(ht, ht.get_rect(center=hist_btn.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if white_btn.collidepoint(pos):
                    self.player_color = WHITE
                    self.board.playing_as_white = True
                    self.board_flipped = True
                    self.game_state = TIME_SELECT
                elif black_btn.collidepoint(pos):
                    self.player_color = BLACK
                    self.board.playing_as_white = False
                    self.board_flipped = False
                    self.game_state = TIME_SELECT
                elif quit_btn.collidepoint(pos):
                    return False
                elif hist_btn.collidepoint(pos):
                    self.game_state = self.HISTORY
        return True

    def handle_time_selection(self):
        self.screen.fill(DARK_GRAY)
        title = self.big_font.render("Select Time Control", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WIDTH//2, 150)))

        mouse_pos = pygame.mouse.get_pos()
        buttons = []
        try:
            bf = pygame.font.Font('freesansbold.ttf', 36)
        except:
            bf = pygame.font.SysFont('Arial', 36)

        for i in range(4):
            btn = pygame.Rect(WIDTH//2 - 200, 250 + i*100, 400, 80)
            buttons.append(btn)
            hover = btn.collidepoint(mouse_pos)
            if hover:
                pygame.draw.rect(self.screen, LIGHT_BLUE, btn.inflate(10, 10), border_radius=15)
            pygame.draw.rect(self.screen, WOOD_BROWN, btn, border_radius=15)
            pygame.draw.rect(self.screen, GOLD if hover else WOOD_DARK, btn, 4, border_radius=15)
            mins = TIME_CONTROLS[i] // 60
            txt = bf.render(f"{TIME_NAMES[i]}: {mins} min{'s' if mins>1 else ''}", True, CREAM_WHITE)
            self.screen.blit(txt, txt.get_rect(center=btn.center))

        back_btn = pygame.Rect(30, HEIGHT-80, 120, 50)
        bh = back_btn.collidepoint(mouse_pos)
        if bh:
            pygame.draw.rect(self.screen, LIGHT_BLUE, back_btn.inflate(10, 10), border_radius=10)
        pygame.draw.rect(self.screen, WOOD_DARK, back_btn, border_radius=10)
        pygame.draw.rect(self.screen, GOLD if bh else WOOD_BROWN, back_btn, 3, border_radius=10)
        self.screen.blit(self.font.render("Back", True, CREAM_WHITE),
                         self.font.render("Back", True, CREAM_WHITE).get_rect(center=back_btn.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if back_btn.collidepoint(pos):
                    self.game_state = MENU; return True
                for i, btn in enumerate(buttons):
                    if btn.collidepoint(pos):
                        self.time_control = i
                        self.white_time = TIME_CONTROLS[i]
                        self.black_time = TIME_CONTROLS[i]
                        self.start_game(); break
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = MENU
        return True

    def start_game(self):
        self.back_rank = Chess960Generator.generate()
        self.pgn = PGNExporter(Chess960Generator.starting_fen(self.back_rank))

        self.game_state = PLAYING
        self.turn_step = 0; self.selection = 100
        self.valid_moves = []; self.castling_moves = []
        self.counter = 0; self.check = False
        self.winner = ''; self.winner_by_time = False
        self.game_over = False; self.stats_saved = False
        self.white_promote = False; self.black_promote = False
        self.promo_index = 100

        self.board.setup_board(self.back_rank)
        self.last_move_time = pygame.time.get_ticks()
        self.last_move_start = pygame.time.get_ticks()

        self.stats.game_data['game_type'] = TIME_NAMES[self.time_control].lower()
        self.stats.start_game()

    def update_timers(self):
        now = pygame.time.get_ticks()
        elapsed = (now - self.last_move_time) / 1000.0

        if self.turn_step < 2:
            self.white_time -= elapsed
            if self.white_time <= 0:
                self.white_time = 0
                self.winner = BLACK; self.winner_by_time = True; self.game_over = True
        else:
            self.black_time -= elapsed
            if self.black_time <= 0:
                self.black_time = 0
                self.winner = WHITE; self.winner_by_time = True; self.game_over = True

        self.last_move_time = now

    def handle_gameplay(self):
        try:
            keys = pygame.key.get_pressed()
            now = pygame.time.get_ticks()
            if keys[pygame.K_f] and now - self.last_flip_time > 300:
                self.board_flipped = not self.board_flipped
                self.last_flip_time = now

            self.screen.fill(DARK_GRAY)
            self.board.draw_board(self.board_flipped)
            self.board.draw_status_area(self.turn_step, self.white_time, self.black_time)
            self.board.draw_pieces(self.turn_step, self.selection, self.board_flipped)
            self.board.draw_captured()

            prev_check = self.check
            self.check = self.board.draw_check(self.counter, self.board_flipped)
            if self.check and not prev_check:
                self.stats.record_check()

            if not self.game_over:
                self.check_promotion()
                if self.white_promote:
                    self.board.draw_promotion(WHITE, self.turn_step)
                    self.check_promotion_selection()
                elif self.black_promote:
                    self.board.draw_promotion(BLACK, self.turn_step)
                    self.check_promotion_selection()

            if self.selection != 100 and self.turn_step in (1, 3):
                self.draw_valid_moves()

            if not self.game_over and self.check:
                if self.turn_step < 2 and self.board.is_checkmate(WHITE):
                    self.winner = BLACK; self.game_over = True
                elif self.turn_step >= 2 and self.board.is_checkmate(BLACK):
                    self.winner = WHITE; self.game_over = True

            if self.winner and not self.stats_saved:
                self.stats_saved = True
                tc = TIME_CONTROLS[self.time_control]
                self.stats.end_game(self.winner, tc - self.white_time, tc - self.black_time)
                if self.pgn:
                    self.pgn.set_result(self.winner)
                    print(f"PGN saved: {self.pgn.export()}")

            if self.winner:
                self.draw_game_over()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.game_over and not self.white_promote and not self.black_promote:
                        self.handle_mouse_click(event.pos)
                    elif self.white_promote or self.black_promote:
                        self.handle_promotion_click(event.pos)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game_state = MENU
                    elif event.key == pygame.K_RETURN and self.game_over:
                        self.reset_game()

        except Exception as e:
            import traceback
            traceback.print_exc()
        return True

    def handle_mouse_click(self, pos):
        sq = self.board.square_size
        sp = self.board.start_pos
        if sp <= pos[0] < sp + sq*8 and sp <= pos[1] < sp + sq*8:
            cx = (pos[0] - sp) // sq
            cy = (pos[1] - sp) // sq
            if self.board_flipped:
                cy = 7 - cy
            else:
                cx = 7 - cx
        else:
            w_res = pygame.Rect(820, 760, 170, 40)
            b_res = pygame.Rect(1000, 760, 170, 40)
            quit_btn = pygame.Rect(820, 820, 350, 50)

            if w_res.collidepoint(pos):
                self.winner = BLACK
                self.game_over = True
            elif b_res.collidepoint(pos):
                self.winner = WHITE
                self.game_over = True
            elif quit_btn.collidepoint(pos):
                self.game_state = MENU
            return

        if self.turn_step <= 1:
            self._handle_player_move((cx, cy), WHITE)
        else:
            self._handle_player_move((cx, cy), BLACK)

    def _handle_player_move(self, click, color):
        pieces = self.board.white_pieces if color == WHITE else self.board.black_pieces
        step_select = 0 if color == WHITE else 2
        step_move   = 1 if color == WHITE else 3

        if self.turn_step == step_select:
            for i, p in enumerate(pieces):
                if tuple(p.position) == click:
                    self.selection = i
                    self.turn_step = step_move
                    self.get_valid_moves()
                    self.last_move_start = pygame.time.get_ticks()
                    break

        elif self.turn_step == step_move and self.selection != 100:
            piece = pieces[self.selection]
            move_time = (pygame.time.get_ticks() - self.last_move_start) / 1000.0

            if click in self.valid_moves and self.is_move_safe_for_king(piece, click, color):
                is_castle = piece.piece_type == 'king' and abs(click[0] - piece.position[0]) == 2
                is_ep = False
                if piece.piece_type == 'pawn':
                    if color == WHITE and click == self.board.black_ep: is_ep = True
                    if color == BLACK and click == self.board.white_ep: is_ep = True

                from_pos = tuple(piece.position)
                cap_piece = self.board.get_piece_at_position(click)
                is_cap = cap_piece is not None

                self.move_piece(piece, click)

                opp = BLACK if color == WHITE else WHITE
                is_check = self.board.is_king_in_check(opp)
                is_cm = self.board.is_checkmate(opp)

                castling_side = None
                if is_castle:
                    castling_side = 'kingside' if click[0] > from_pos[0] else 'queenside'

                notation = PGNExporter.to_algebraic(
                    piece.piece_type, from_pos, click,
                    is_capture=is_cap, is_check=is_check,
                    is_checkmate=is_cm, castling=castling_side
                )
                self.board.add_notation(notation)
                if self.pgn: self.pgn.record_move(notation)

                self.stats.record_move(
                    piece.piece_type, color, click,
                    is_castling=is_castle, is_en_passant=is_ep,
                    move_time=move_time, is_capture=is_cap, is_check=is_check
                )

                self.turn_step = 2 if color == WHITE else 0
                self.selection = 100
                self.valid_moves = []

            elif piece.piece_type == 'king':
                for kd, rd in self.castling_moves:
                    if click == kd:
                        side = 'kingside' if kd[0] > piece.position[0] else 'queenside'
                        rook = next((p for p in pieces if p.piece_type == 'rook' and
                            ((side == 'kingside'  and p.position[0] > piece.position[0]) or
                             (side == 'queenside' and p.position[0] < piece.position[0]))), None)
                        if rook:
                            from_pos = tuple(piece.position)
                            mt = (pygame.time.get_ticks() - self.last_move_start) / 1000.0
                            piece.move(kd); rook.move(rd)
                            self.last_move_time = pygame.time.get_ticks()
                            notation = PGNExporter.to_algebraic('king', from_pos, kd, castling=side)
                            self.board.add_notation(notation)
                            if self.pgn: self.pgn.record_move(notation)
                            self.stats.record_move('king', color, kd, is_castling=True, move_time=mt)
                        self.turn_step = 2 if color == WHITE else 0
                        self.selection = 100
                        self.valid_moves = []; self.castling_moves = []
                        break

            if any(tuple(p.position) == click for p in pieces):
                for i, p in enumerate(pieces):
                    if tuple(p.position) == click:
                        self.selection = i; self.get_valid_moves(); break

    def is_move_safe_for_king(self, piece, new_pos, color):
        orig = list(piece.position)
        cap = self.board.get_piece_at_position(new_pos)
        cap_w = cap_b = None
        if cap:
            if cap.color == WHITE: self.board.white_pieces.remove(cap); cap_w = cap
            else: self.board.black_pieces.remove(cap); cap_b = cap
        piece.position = list(new_pos)
        safe = not self.board.is_king_in_check(color)
        piece.position = orig
        if cap_w: self.board.white_pieces.append(cap_w)
        if cap_b: self.board.black_pieces.append(cap_b)
        return safe

    def get_valid_moves(self):
        self.valid_moves = []; self.castling_moves = []
        pieces = self.board.white_pieces if self.turn_step <= 1 else self.board.black_pieces
        color  = WHITE if self.turn_step <= 1 else BLACK
        if 0 <= self.selection < len(pieces):
            piece = pieces[self.selection]
            for m in piece.get_valid_moves():
                if self.is_move_safe_for_king(piece, m, color):
                    self.valid_moves.append(m)
            if piece.piece_type == 'king':
                self.castling_moves = self.board.check_castling(color)

    def move_piece(self, piece, new_pos):
        if piece.piece_type == 'pawn':
            if piece.color == WHITE and tuple(new_pos) == self.board.black_ep:
                cap = self.board.get_piece_at_position((new_pos[0], new_pos[1]-1))
                if cap:
                    self.board.black_pieces.remove(cap)
                    self.board.captured_black.append(cap)
                    self.stats.record_capture(cap.piece_type, piece.color)
            elif piece.color == BLACK and tuple(new_pos) == self.board.white_ep:
                cap = self.board.get_piece_at_position((new_pos[0], new_pos[1]+1))
                if cap:
                    self.board.white_pieces.remove(cap)
                    self.board.captured_white.append(cap)
                    self.stats.record_capture(cap.piece_type, piece.color)

        if piece.piece_type == 'pawn' and abs(piece.position[1] - new_pos[1]) == 2:
            mid_y = (piece.position[1] + new_pos[1]) // 2
            if piece.color == WHITE: self.board.white_ep = (new_pos[0], mid_y)
            else: self.board.black_ep = (new_pos[0], mid_y)
        else:
            if piece.color == WHITE: self.board.white_ep = (100, 100)
            else: self.board.black_ep = (100, 100)

        cap = self.board.get_piece_at_position(new_pos)
        if cap:
            if cap.piece_type == 'king': return False
            if cap.color == WHITE:
                self.board.white_pieces.remove(cap)
                self.board.captured_white.append(cap)
            else:
                self.board.black_pieces.remove(cap)
                self.board.captured_black.append(cap)
            self.stats.record_capture(cap.piece_type, piece.color)

        piece.move(new_pos)
        self.last_move_time = pygame.time.get_ticks()
        return True

    def check_promotion(self):
        self.white_promote = False; self.black_promote = False
        for i, p in enumerate(self.board.white_pieces):
            if p.piece_type == 'pawn' and p.position[1] == 7:
                self.white_promote = True; self.promo_index = i; break
        for i, p in enumerate(self.board.black_pieces):
            if p.piece_type == 'pawn' and p.position[1] == 0:
                self.black_promote = True; self.promo_index = i; break

    def handle_promotion_click(self, pos):
        panel = pygame.Rect(850, 200, 300, 450)
        if not panel.collidepoint(pos): return
        idx = (pos[1] - (panel.y + 80)) // 90
        if idx < 0 or idx >= len(PROMOTION_PIECES): return
        promo_type = PROMOTION_PIECES[idx]

        if self.white_promote:
            pawn = self.board.white_pieces[self.promo_index]
            pawn_pos = list(pawn.position)
            self.board.white_pieces.pop(self.promo_index)
            self.board.white_pieces.append(make_piece(promo_type, WHITE, pawn_pos, self.board))
            self.white_promote = False
            self.stats.record_promotion(promo_type, WHITE, pawn_pos)
            self.board.add_notation(f"{chr(96+pawn_pos[0])}{pawn_pos[1]+1}={promo_type[0].upper()}")
            if self.board.is_checkmate(BLACK): self.winner = WHITE; self.game_over = True
        elif self.black_promote:
            pawn = self.board.black_pieces[self.promo_index]
            pawn_pos = list(pawn.position)
            self.board.black_pieces.pop(self.promo_index)
            self.board.black_pieces.append(make_piece(promo_type, BLACK, pawn_pos, self.board))
            self.black_promote = False
            self.stats.record_promotion(promo_type, BLACK, pawn_pos)
            self.board.add_notation(f"{chr(96+pawn_pos[0])}{pawn_pos[1]+1}={promo_type[0].upper()}")
            if self.board.is_checkmate(WHITE): self.winner = BLACK; self.game_over = True

    def check_promotion_selection(self):
        mp = pygame.mouse.get_pos()
        panel = pygame.Rect(850, 200, 300, 450)
        idx = (mp[1] - (panel.y + 80)) // 90 if panel.collidepoint(mp) else -1
        self.board.highlight_promotion_option = idx if 0 <= idx < len(PROMOTION_PIECES) else -1
        if pygame.mouse.get_pressed()[0]:
            self.handle_promotion_click(mp)

    def draw_valid_moves(self):
        self.board.draw_valid_moves(self.valid_moves, self.turn_step, self.board_flipped)
        if self.castling_moves:
            self.board.draw_castling(self.castling_moves, self.turn_step, self.board_flipped)

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect((WIDTH-520)//2, (HEIGHT-220)//2, 520, 220)
        border_c = (240,240,240) if self.winner == WHITE else (30,30,30)
        pygame.draw.rect(self.screen, WOOD_BROWN, panel, border_radius=18)
        pygame.draw.rect(self.screen, border_c, panel, 5, border_radius=18)

        try:
            tf = pygame.font.Font('freesansbold.ttf', 48)
            mf = pygame.font.Font('freesansbold.ttf', 22)
        except:
            tf = pygame.font.SysFont('Arial', 48)
            mf = pygame.font.SysFont('Arial', 22)

        side = "White" if self.winner == WHITE else "Black"
        win_str = f"{side} Wins!" + ("  (Timeout)" if self.winner_by_time else "")
        t = tf.render(win_str, True, CREAM_WHITE)
        m = mf.render("Enter = play again   |   R = menu", True, LIGHT_GRAY)
        self.screen.blit(t, t.get_rect(center=(panel.centerx, panel.y+80)))
        self.screen.blit(m, m.get_rect(center=(panel.centerx, panel.y+148)))

    def handle_history_view(self):
        self.screen.fill(DARK_GRAY)
        header = self.big_font.render("Game History & Statistics", True, GOLD)
        self.screen.blit(header, header.get_rect(center=(WIDTH//2, 50)))

        games   = self.stats.get_all_games()
        summary = self.stats.get_summary_statistics()

        panel = pygame.Rect(30, 90, 520, 670)
        pygame.draw.rect(self.screen, WOOD_BROWN, panel, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, panel, 3, border_radius=15)
        self.screen.blit(self.font.render("Summary Statistics", True, GOLD), (panel.x+20, panel.y+14))

        y = panel.y + 44
        tbl = self.stats.generate_summary_table()
        if tbl:
            hdr_txt = f"{'Feature':<26}{'Min':>6}{'Max':>7}{'Mean':>7}{'Med':>7}{'Std':>7}"
            self.screen.blit(self.small_font.render(hdr_txt, True, GOLD), (panel.x+14, y)); y += 22
            pygame.draw.line(self.screen, GOLD, (panel.x+10, y), (panel.right-10, y), 1); y += 6
            for feat, v in tbl.items():
                row = f"{feat[:25]:<26}{v['min']:>6.1f}{v['max']:>7.1f}{v['mean']:>7.1f}{v['median']:>7.1f}{v['std']:>7.1f}"
                self.screen.blit(self.small_font.render(row, True, CREAM_WHITE), (panel.x+14, y))
                y += 22

        y += 14
        if summary:
            for line in [
                f"Total Games : {summary['total_games']}",
                f"White Wins  : {summary['win_rates']['white']:.1f}%",
                f"Black Wins  : {summary['win_rates']['black']:.1f}%",
                f"Draws       : {summary['win_rates']['draw']:.1f}%",
                f"Avg Duration: {summary['averages']['duration']/60:.1f} min",
                f"Avg Moves   : {summary['averages']['moves']:.1f}",
                f"Playtime    : {summary['total_playtime']:.2f} hrs",
            ]:
                self.screen.blit(self.font.render(line, True, CREAM_WHITE), (panel.x+20, y))
                y += 28

        rp = pygame.Rect(570, 90, 600, 670)
        pygame.draw.rect(self.screen, WOOD_BROWN, rp, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, rp, 3, border_radius=15)
        self.screen.blit(self.font.render("Recent Games", True, GOLD), (rp.x+20, rp.y+14))

        y = rp.y + 48
        for i, g in enumerate(reversed(games[-20:])):
            winner = g.get('winner','?').capitalize()
            dur    = self.stats.safe_float(g.get('duration',0)) / 60
            moves  = g.get('total_moves','?')
            gt     = g.get('game_type','?')
            txt    = f"#{len(games)-i:>3}  {winner:<6}  {dur:>5.1f}min  {moves:>3}mv  [{gt}]"
            self.screen.blit(self.small_font.render(txt, True, CREAM_WHITE), (rp.x+20, y))
            y += 24

        mouse_pos = pygame.mouse.get_pos()
        back_btn   = pygame.Rect(30,  HEIGHT-70, 120, 50)
        charts_btn = pygame.Rect(170, HEIGHT-70, 230, 50)
        export_btn = pygame.Rect(420, HEIGHT-70, 180, 50)

        for btn, label, base_c in [
            (back_btn,   "← Back",          WOOD_DARK),
            (charts_btn, "Generate Charts",  DARK_GREEN),
            (export_btn, "Export CSV",       BLUE),
        ]:
            hv = btn.collidepoint(mouse_pos)
            pygame.draw.rect(self.screen, LIGHT_BLUE if hv else base_c, btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, btn, 2, border_radius=10)
            bt = self.font.render(label, True, WHITE)
            self.screen.blit(bt, bt.get_rect(center=btn.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if back_btn.collidepoint(pos):
                    self.game_state = MENU
                elif charts_btn.collidepoint(pos):
                    self.stats.generate_charts()
                    self.game_state = CHART_VIEWER
                    self.current_chart_index = 0
                    self.chart_filter = 'all'
                elif export_btn.collidepoint(pos):
                    self.stats.export_data_to_csv()
                    print("Exported.")
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = MENU
        return True

    def handle_chart_viewer(self):
        self.screen.fill(DARK_GRAY)
        header = self.big_font.render("Statistical Charts", True, GOLD)
        self.screen.blit(header, header.get_rect(center=(WIDTH//2, 45)))

        charts_dir  = self.stats.save_directory / "charts"
        all_charts  = sorted(charts_dir.glob("*.png")) if charts_dir.exists() else []

        filters = [
            ('all',     'All',        []),
            ('white',   'White Side', ['white', 'w_']),
            ('black',   'Black Side', ['black', 'b_']),
            ('time',    'Time/Speed', ['duration', 'move_time', 'speed', 'trend']),
            ('capture', 'Captures',   ['capture']),
        ]

        mouse_pos = pygame.mouse.get_pos()
        fx = 30
        filter_rects = []
        for fkey, flabel, _ in filters:
            fb = pygame.Rect(fx, 90, 145, 36)
            filter_rects.append((fkey, fb))
            active = self.chart_filter == fkey
            bg = GOLD if active else (LIGHT_BLUE if fb.collidepoint(mouse_pos) else WOOD_DARK)
            pygame.draw.rect(self.screen, bg, fb, border_radius=8)
            pygame.draw.rect(self.screen, GOLD, fb, 2, border_radius=8)
            fc = BLACK if active else CREAM_WHITE
            ft = self.small_font.render(flabel, True, fc)
            self.screen.blit(ft, ft.get_rect(center=fb.center))
            fx += 155

        keywords = next((kw for fk, _, kw in filters if fk == self.chart_filter), [])
        if keywords:
            visible = [f for f in all_charts if any(k in f.stem.lower() for k in keywords)]
            if not visible: visible = all_charts
        else:
            visible = all_charts

        if visible:
            self.current_chart_index = self.current_chart_index % len(visible)
            try:
                img = pygame.image.load(str(visible[self.current_chart_index]))
                iw, ih = img.get_size()
                scale = min(700/iw, 490/ih)
                img = pygame.transform.scale(img, (int(iw*scale), int(ih*scale)))
                self.screen.blit(img, img.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))

                name = visible[self.current_chart_index].stem.replace('_', ' ').title()
                self.screen.blit(self.font.render(name, True, CREAM_WHITE),
                                 self.font.render(name, True, CREAM_WHITE).get_rect(center=(WIDTH//2, 145)))

                ct = self.small_font.render(
                    f"{self.current_chart_index+1} / {len(visible)}  —  filter: {self.chart_filter}",
                    True, LIGHT_GRAY)
                self.screen.blit(ct, ct.get_rect(center=(WIDTH//2, HEIGHT-128)))
            except Exception as e:
                self.screen.blit(self.font.render(f"Error: {e}", True, RED), (50, HEIGHT//2))
        else:
            self.screen.blit(
                self.font.render("No charts. Use History → Generate Charts.", True, CREAM_WHITE),
                self.font.render("No charts. Use History → Generate Charts.", True, CREAM_WHITE).get_rect(center=(WIDTH//2, HEIGHT//2))
            )

        back_btn = pygame.Rect(30,  HEIGHT-75, 110, 46)
        prev_btn = pygame.Rect(200, HEIGHT-75, 150, 46)
        next_btn = pygame.Rect(370, HEIGHT-75, 150, 46)

        for btn, label, col in [
            (back_btn, "← Back",  WOOD_DARK),
            (prev_btn, "◀ Prev",  BLUE),
            (next_btn, "Next ▶",  BLUE),
        ]:
            hv = btn.collidepoint(mouse_pos)
            pygame.draw.rect(self.screen, LIGHT_BLUE if hv else col, btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, btn, 2, border_radius=10)
            bt = self.font.render(label, True, WHITE)
            self.screen.blit(bt, bt.get_rect(center=btn.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if back_btn.collidepoint(pos):
                    self.game_state = self.HISTORY
                elif prev_btn.collidepoint(pos) and visible:
                    self.current_chart_index = (self.current_chart_index - 1) % len(visible)
                elif next_btn.collidepoint(pos) and visible:
                    self.current_chart_index = (self.current_chart_index + 1) % len(visible)
                for fkey, fb in filter_rects:
                    if fb.collidepoint(pos):
                        self.chart_filter = fkey
                        self.current_chart_index = 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.game_state = self.HISTORY
                if event.key == pygame.K_LEFT  and visible:
                    self.current_chart_index = (self.current_chart_index - 1) % len(visible)
                if event.key == pygame.K_RIGHT and visible:
                    self.current_chart_index = (self.current_chart_index + 1) % len(visible)
        return True

    def reset_game(self):
        playing_as_white = self.board.playing_as_white
        player_color     = self.player_color
        tc               = self.time_control

        self.board = ChessBoard(self.screen)
        self.board.playing_as_white = playing_as_white
        self.back_rank = Chess960Generator.generate()
        self.board.setup_board(self.back_rank)

        self.turn_step = 0; self.selection = 100
        self.valid_moves = []; self.castling_moves = []
        self.counter = 0; self.check = False
        self.winner = ''; self.winner_by_time = False
        self.game_over = False; self.stats_saved = False
        self.white_promote = False; self.black_promote = False
        self.promo_index = 100
        self.player_color = player_color
        self.board_flipped = (player_color == WHITE)

        self.time_control = tc
        self.white_time = TIME_CONTROLS[tc]
        self.black_time = TIME_CONTROLS[tc]
        self.last_move_time = pygame.time.get_ticks()
        self.last_move_start = pygame.time.get_ticks()

        self.pgn = PGNExporter(Chess960Generator.starting_fen(self.back_rank))
        self.stats.start_game()