import pygame
import math
import os
from constants import *
from chess_board import ChessBoard
from chess_piece import ChessPiece
from chess_statistics import ChessStatistics


class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode([WIDTH, HEIGHT])
        pygame.display.set_caption('Chess Master')
        self.clock = pygame.time.Clock()
        self.board = ChessBoard(self.screen)
        self.turn_step = 0  # 0-white select, 1-white move, 2-black select, 3-black move
        self.selection = 100  # stores which piece player clicked on
        self.valid_moves = []
        self.castling_moves = []
        self.counter = 0  # used for animations like pulsing check warning
        self.check = False
        self.winner = ''
        self.winner_by_time = False
        self.game_over = False
        self.white_promote = False
        self.black_promote = False
        self.promo_index = 100
        self.board_flipped = False  # false = white at bottom, true = black at bottom
        self.last_flip_time = 0  # prevents accidental double-clicks on F key

        # player preferences
        self.player_color = WHITE
        self.computer_plays = False

        # timer settings
        self.time_control = BLITZ
        self.white_time = 0
        self.black_time = 0
        self.last_move_time = 0

        # game state management
        self.game_state = MENU
        self.HISTORY = 4  # state for game history
        self.CHARTS = 5  # state for viewing charts

        # history navigation
        self.history_scroll = 0
        self.selected_game_index = -1
        self.history_view = 'overview'  # overview, detailed, charts

        # stats tracking
        self.stats = ChessStatistics()

        # fonts for different text sizes
        try:
            self.font = pygame.font.Font('freesansbold.ttf', 20)
            self.small_font = pygame.font.Font('freesansbold.ttf', 16)
            self.tiny_font = pygame.font.Font('freesansbold.ttf', 12)
            self.big_font = pygame.font.Font('freesansbold.ttf', 48)
        except:
            self.font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
            self.tiny_font = pygame.font.SysFont('Arial', 12)
            self.big_font = pygame.font.SysFont('Arial', 48)

    def run(self):
        game_running = True
        while game_running:
            self.clock.tick(FPS)

            # animation counter
            if self.counter < 30:
                self.counter += 1
            else:
                self.counter = 0

            # route to different screens
            if self.game_state == MENU:
                game_running = self.handle_menu()
            elif self.game_state == TIME_SELECT:
                game_running = self.handle_time_selection()
            elif self.game_state == PLAYING:
                game_running = self.handle_gameplay()
                # count down timers only when game is active
                if not self.game_over and not self.white_promote and not self.black_promote:
                    self.update_timers()
            elif self.game_state == self.HISTORY:
                game_running = self.handle_history_view()
            elif self.game_state == self.CHARTS:
                game_running = self.handle_charts_view()
            elif self.game_state == CHART_VIEWER:
                game_running = self.handle_chart_viewer()

            pygame.display.flip()

        pygame.quit()

    def handle_menu(self):
        # get the standard menu buttons
        white_button, black_button, quit_button = self.board.draw_menu()

        # add history button
        mouse_pos = pygame.mouse.get_pos()
        history_button = pygame.Rect(30, HEIGHT - 140, 200, 60)
        history_hover = history_button.collidepoint(mouse_pos)

        # draw history button
        if history_hover:
            pygame.draw.rect(self.screen, LIGHT_BLUE, history_button.inflate(10, 10), border_radius=15)
        pygame.draw.rect(self.screen, DARK_GRAY, history_button, border_radius=15)
        pygame.draw.rect(self.screen, GOLD if history_hover else WOOD_BROWN, history_button, 3, border_radius=15)

        # history button text
        history_text = self.font.render("History & Stats", True, 'white')
        history_text_rect = history_text.get_rect(center=history_button.center)
        self.screen.blit(history_text, history_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                if white_button.collidepoint(mouse_pos):
                    # player chose white
                    self.player_color = WHITE
                    self.board.playing_as_white = True
                    self.board_flipped = False
                    self.computer_plays = False
                    self.game_state = TIME_SELECT

                elif black_button.collidepoint(mouse_pos):
                    # player chose black
                    self.player_color = BLACK
                    self.board.playing_as_white = False
                    self.board_flipped = True
                    self.computer_plays = True
                    self.game_state = TIME_SELECT

                elif quit_button.collidepoint(mouse_pos):
                    return False

                elif history_button.collidepoint(mouse_pos):
                    self.game_state = self.HISTORY

        return True

    def handle_history_view(self):
        """Display comprehensive game history interface"""
        self.screen.fill(DARK_GRAY)

        # header
        header = self.big_font.render("Game History & Statistics", True, GOLD)
        header_rect = header.get_rect(center=(WIDTH // 2, 50))
        self.screen.blit(header, header_rect)

        # navigation tabs
        tab_y = 100
        tab_height = 40
        tab_names = ['Overview', 'Game Details', 'Statistical Analysis']
        tab_width = 250

        for i, tab_name in enumerate(tab_names):
            tab_x = (WIDTH - (len(tab_names) * tab_width + (len(tab_names) - 1) * 10)) // 2 + i * (tab_width + 10)
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)

            mouse_pos = pygame.mouse.get_pos()
            tab_hover = tab_rect.collidepoint(mouse_pos)
            tab_active = (i == 0 and self.history_view == 'overview') or \
                         (i == 1 and self.history_view == 'detailed') or \
                         (i == 2 and self.history_view == 'charts')

            # draw tab
            if tab_active:
                pygame.draw.rect(self.screen, GOLD, tab_rect, border_radius=10)
                text_color = 'black'
            else:
                color = LIGHT_BLUE if tab_hover else WOOD_BROWN
                pygame.draw.rect(self.screen, color, tab_rect, border_radius=10)
                text_color = 'black' if tab_hover else 'white'

            tab_text = self.font.render(tab_name, True, text_color)
            tab_text_rect = tab_text.get_rect(center=tab_rect.center)
            self.screen.blit(tab_text, tab_text_rect)

        # display appropriate view
        if self.history_view == 'overview':
            self.draw_history_overview()
        elif self.history_view == 'detailed':
            self.draw_game_details()
        elif self.history_view == 'charts':
            self.draw_statistical_analysis()

        # control buttons
        self.draw_history_controls()

        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_history_click(event.pos)

            # keyboard navigation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = MENU
                elif event.key == pygame.K_UP:
                    self.history_scroll = max(0, self.history_scroll - 1)
                elif event.key == pygame.K_DOWN:
                    self.history_scroll += 1
                elif event.key == pygame.K_1:
                    self.history_view = 'overview'
                elif event.key == pygame.K_2:
                    self.history_view = 'detailed'
                elif event.key == pygame.K_3:
                    self.history_view = 'charts'

        return True

    def draw_history_overview(self):
        """Show summary of all games"""
        # get all games
        games = self.stats.get_all_games()
        if not games:
            no_data_text = self.font.render("No games in history yet", True, CREAM_WHITE)
            no_data_rect = no_data_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(no_data_text, no_data_rect)
            return

        # summary statistics panel
        summary_panel = pygame.Rect(50, 160, 500, 600)
        pygame.draw.rect(self.screen, WOOD_BROWN, summary_panel, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, summary_panel, 4, border_radius=15)

        # title
        title = self.font.render("Game Summary", True, CREAM_WHITE)
        self.screen.blit(title, (summary_panel.x + 20, summary_panel.y + 20))

        # get summary statistics
        summary = self.stats.get_summary_statistics()
        if summary:
            y_offset = 60
            line_height = 30

            stats_text = [
                f"Total Games: {summary['total_games']}",
                f"White Wins: {summary['win_rates']['white']:.1f}%",
                f"Black Wins: {summary['win_rates']['black']:.1f}%",
                f"Draws: {summary['win_rates']['draw']:.1f}%",
                f"Average Duration: {summary['averages']['duration'] / 60:.1f} min",
                f"Average Moves: {summary['averages']['moves']:.1f}",
                f"Total Playtime: {summary['total_playtime']:.1f} hours"
            ]

            for text in stats_text:
                self.screen.blit(self.font.render(text, True, CREAM_WHITE),
                                 (summary_panel.x + 30, summary_panel.y + y_offset))
                y_offset += line_height

            # popular openings
            if summary['popular_openings']:
                y_offset += 20
                self.screen.blit(self.font.render("Popular Openings:", True, CREAM_WHITE),
                                 (summary_panel.x + 30, summary_panel.y + y_offset))
                y_offset += line_height

                for opening, count in summary['popular_openings'][:3]:
                    text = f"• {opening}: {count} games"
                    self.screen.blit(self.small_font.render(text, True, CREAM_WHITE),
                                     (summary_panel.x + 50, summary_panel.y + y_offset))
                    y_offset += line_height - 5

        # recent games list
        games_panel = pygame.Rect(570, 160, 600, 600)
        pygame.draw.rect(self.screen, WOOD_BROWN, games_panel, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, games_panel, 4, border_radius=15)

        # title
        title = self.font.render("Recent Games", True, CREAM_WHITE)
        self.screen.blit(title, (games_panel.x + 20, games_panel.y + 20))

        # list of games
        y_offset = 60
        games_to_show = 15
        start_index = self.history_scroll

        for i in range(start_index, min(start_index + games_to_show, len(games))):
            game = games[-(i + 1)]  # newest first

            # game info
            winner_text = game.get('winner', 'Draw').capitalize()
            try:
                duration = float(game.get('duration', 0))
                duration_text = f"{duration / 60:.1f}min"
            except (ValueError, TypeError):
                duration_text = "??min"
                duration = 0  # Set default value when an error occurs

            moves = game.get('total_moves', 0)
            timestamp = game.get('timestamp', 'Unknown')

            # format text
            game_text = f"Game {len(games) - i}: {winner_text} in {duration_text} ({moves} moves)"

            # highlight selected game
            if i == self.selected_game_index:
                highlight_rect = pygame.Rect(games_panel.x + 10, games_panel.y + y_offset - 5,
                                             games_panel.width - 20, 25)
                pygame.draw.rect(self.screen, LIGHT_BLUE, highlight_rect, border_radius=5)

            # draw text
            self.screen.blit(self.small_font.render(game_text, True, CREAM_WHITE),
                             (games_panel.x + 30, games_panel.y + y_offset))
            y_offset += 25

    def draw_game_details(self):
        """Show detailed view of selected game"""
        games = self.stats.get_all_games()

        if not games or self.selected_game_index < 0 or self.selected_game_index >= len(games):
            # show message to select a game
            message = self.font.render("Select a game from the Overview tab", True, CREAM_WHITE)
            message_rect = message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(message, message_rect)
            return

        game = games[self.selected_game_index]

        # main panel
        detail_panel = pygame.Rect(50, 160, WIDTH - 100, 600)
        pygame.draw.rect(self.screen, WOOD_BROWN, detail_panel, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, detail_panel, 4, border_radius=15)

        # title
        title = self.font.render(f"Game Details - {game.get('timestamp', 'Unknown')}", True, CREAM_WHITE)
        self.screen.blit(title, (detail_panel.x + 20, detail_panel.y + 20))

        # create two columns
        left_x = detail_panel.x + 30
        right_x = detail_panel.x + detail_panel.width // 2 + 30
        y_offset = 60
        line_height = 30

        # Helper function to safely get numeric values
        def safe_float(value, default=0):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=0):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        # left column - basic info
        left_info = [
            f"Winner: {game.get('winner', 'Draw').capitalize()}",
            f"Duration: {safe_float(game.get('duration', 0)) / 60:.1f} minutes",
            f"Total Moves: {safe_int(game.get('total_moves', 0))}",
            f"White Moves: {safe_int(game.get('white_moves', 0))}",
            f"Black Moves: {safe_int(game.get('black_moves', 0))}",
            f"Average Move Time: {safe_float(game.get('avg_move_time', 0)):.2f} sec",
        ]

        for text in left_info:
            self.screen.blit(self.font.render(text, True, CREAM_WHITE),
                             (left_x, detail_panel.y + y_offset))
            y_offset += line_height

        # right column - game events
        y_offset = 60
        right_info = [
            f"White Captures: {safe_int(game.get('white_captures', 0))}",
            f"Black Captures: {safe_int(game.get('black_captures', 0))}",
            f"Castling (White): {safe_int(game.get('castling_white', 0))}",
            f"Castling (Black): {safe_int(game.get('castling_black', 0))}",
            f"En Passant: {safe_int(game.get('en_passant', 0))}",
            f"Check Events: {safe_int(game.get('check_events', 0))}",
            f"Promotions: {safe_int(game.get('promotions', 0))}",
        ]

        for text in right_info:
            self.screen.blit(self.font.render(text, True, CREAM_WHITE),
                             (right_x, detail_panel.y + y_offset))
            y_offset += line_height

    def draw_statistical_analysis(self):
        """Show statistical analysis options"""
        # main panel
        analysis_panel = pygame.Rect(50, 160, WIDTH - 100, 600)
        pygame.draw.rect(self.screen, WOOD_BROWN, analysis_panel, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, analysis_panel, 4, border_radius=15)

        # title
        title = self.font.render("Statistical Analysis", True, CREAM_WHITE)
        self.screen.blit(title, (analysis_panel.x + 20, analysis_panel.y + 20))

        # analysis options
        options = [
            ("Win Rate Analysis", "View win/loss/draw distribution"),
            ("Game Duration Trends", "See how game length changes over time"),
            ("Piece Usage Patterns", "Analyze most used pieces"),
            ("Position Heatmap", "See where pieces move most often"),
            ("Performance Trends", "Track improvement over time"),
            ("Opening Analysis", "Most played opening moves"),
        ]

        option_height = 50
        option_width = 500
        start_y = 80

        for i, (option, description) in enumerate(options):
            option_y = analysis_panel.y + start_y + i * (option_height + 15)
            option_rect = pygame.Rect(analysis_panel.x + 50, option_y, option_width, option_height)

            mouse_pos = pygame.mouse.get_pos()
            hover = option_rect.collidepoint(mouse_pos)

            # draw option button
            color = LIGHT_BLUE if hover else DARK_GRAY
            pygame.draw.rect(self.screen, color, option_rect, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, option_rect, 2, border_radius=10)

            # option text
            text_color = 'black' if hover else 'white'
            option_text = self.font.render(option, True, text_color)
            desc_text = self.small_font.render(description, True, text_color)

            self.screen.blit(option_text, (option_rect.x + 20, option_rect.y + 10))
            self.screen.blit(desc_text, (option_rect.x + 20, option_rect.y + 28))

        # generate all charts button
        generate_btn = pygame.Rect(analysis_panel.x + 50, analysis_panel.y + 480, 500, 50)
        mouse_pos = pygame.mouse.get_pos()
        gen_hover = generate_btn.collidepoint(mouse_pos)

        color = DARK_GREEN if gen_hover else WOOD_DARK
        pygame.draw.rect(self.screen, color, generate_btn, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, generate_btn, 3, border_radius=10)

        gen_text = self.font.render("Generate All Charts & Export Data", True, 'white')
        gen_text_rect = gen_text.get_rect(center=generate_btn.center)
        self.screen.blit(gen_text, gen_text_rect)

    def draw_history_controls(self):
        """Draw navigation controls for history view"""
        controls_y = HEIGHT - 80

        # control buttons
        back_btn = pygame.Rect(30, controls_y, 120, 50)
        export_btn = pygame.Rect(170, controls_y, 140, 50)
        refresh_btn = pygame.Rect(330, controls_y, 120, 50)
        charts_btn = pygame.Rect(WIDTH - 220, controls_y, 180, 50)

        buttons = [
            (back_btn, "Back", WOOD_DARK),
            (export_btn, "Export CSV", DARK_GREEN),
            (refresh_btn, "Refresh", BLUE),
            (charts_btn, "View Charts", PURPLE)
        ]

        mouse_pos = pygame.mouse.get_pos()

        for btn_rect, text, base_color in buttons:
            hover = btn_rect.collidepoint(mouse_pos)
            color = LIGHT_BLUE if hover else base_color

            pygame.draw.rect(self.screen, color, btn_rect, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, btn_rect, 3, border_radius=10)

            btn_text = self.font.render(text, True, 'white')
            btn_text_rect = btn_text.get_rect(center=btn_rect.center)
            self.screen.blit(btn_text, btn_text_rect)

        # scroll indicators
        if self.history_view == 'overview':
            scroll_text = f"Scroll: {self.history_scroll} (↑↓ keys)"
            scroll_surface = self.small_font.render(scroll_text, True, LIGHT_GRAY)
            self.screen.blit(scroll_surface, (500, controls_y + 15))

    def handle_history_click(self, pos):
        """Handle mouse clicks in history view"""
        mouse_pos = pos

        # check tab clicks
        tab_y = 100
        tab_names = ['overview', 'detailed', 'charts']
        for i, view_name in enumerate(tab_names):
            tab_x = (WIDTH - (3 * 250 + 2 * 10)) // 2 + i * 260
            tab_rect = pygame.Rect(tab_x, tab_y, 250, 40)
            if tab_rect.collidepoint(mouse_pos):
                self.history_view = view_name
                return

        # check control button clicks
        controls_y = HEIGHT - 80
        back_btn = pygame.Rect(30, controls_y, 120, 50)
        export_btn = pygame.Rect(170, controls_y, 140, 50)
        refresh_btn = pygame.Rect(330, controls_y, 120, 50)
        charts_btn = pygame.Rect(WIDTH - 220, controls_y, 180, 50)

        if back_btn.collidepoint(mouse_pos):
            self.game_state = MENU
        elif export_btn.collidepoint(mouse_pos):
            # export all data
            self.stats.export_data_to_csv()
            print("Data exported successfully to statistics folder!")
        elif refresh_btn.collidepoint(mouse_pos):
            # reload stats
            self.stats = ChessStatistics()
        elif charts_btn.collidepoint(mouse_pos):
            # generate and view charts
            charts_dir = self.stats.generate_charts()
            self.stats.generate_heatmap()
            print(f"Charts generated in {charts_dir}")
            self.game_state = CHART_VIEWER
            self.current_chart_index = a = 0

        # check game selection in overview
        if self.history_view == 'overview':
            games_panel = pygame.Rect(570, 160, 600, 600)
            if games_panel.collidepoint(mouse_pos):
                # calculate which game was clicked
                click_y = mouse_pos[1] - games_panel.y - 60
                if click_y >= 0:
                    game_index = click_y // 25 + self.history_scroll
                    games = self.stats.get_all_games()
                    if 0 <= game_index < len(games):
                        self.selected_game_index = len(games) - 1 - game_index
                        self.history_view = 'detailed'

        # Check for chart option clicks in charts view
        if self.history_view == 'charts':
            analysis_panel = pygame.Rect(50, 160, WIDTH - 100, 600)

            option_height = 50
            option_width = 500
            start_y = 80

            for i, (option, description) in enumerate([
                ("Win Rate Analysis", "View win/loss/draw distribution"),
                ("Game Duration Trends", "See how game length changes over time"),
                ("Piece Usage Patterns", "Analyze most used pieces"),
                ("Position Heatmap", "See where pieces move most often"),
                ("Performance Trends", "Track improvement over time"),
                ("Opening Analysis", "Most played opening moves")
            ]):
                option_y = analysis_panel.y + start_y + i * (option_height + 15)
                option_rect = pygame.Rect(analysis_panel.x + 50, option_y, option_width, option_height)

                if option_rect.collidepoint(mouse_pos):
                    # If option clicked, find matching chart
                    chart_types = {
                        "Win Rate Analysis": "win_rate",
                        "Game Duration Trends": "durations",
                        "Piece Usage Patterns": "piece_usage",
                        "Position Heatmap": "heatmap",
                        "Performance Trends": "move_trends",
                        "Opening Analysis": "opening_analysis"
                    }

                    chart_keyword = chart_types.get(option, "")
                    if chart_keyword:
                        # Generate charts if they don't exist yet
                        charts_dir = self.stats.save_directory / "charts"
                        if not charts_dir.exists():
                            self.stats.generate_charts()

                        # Look for matching chart
                        charts = list(charts_dir.glob(f"*{chart_keyword}*.png"))
                        if charts:
                            self.game_state = CHART_VIEWER
                            # Find the chart's index in the list of all charts
                            all_charts = list(charts_dir.glob("*.png"))
                            try:
                                self.current_chart_index = all_charts.index(charts[0])
                            except:
                                self.current_chart_index = 0
                        else:
                            # If no matching chart, generate and show all charts
                            self.stats.generate_charts()
                            self.game_state = CHART_VIEWER
                            self.current_chart_index = 0

            # Generate all charts button
            generate_btn = pygame.Rect(analysis_panel.x + 50, analysis_panel.y + 480, 500, 50)
            if generate_btn.collidepoint(mouse_pos):
                # Generate all charts and report
                report_file = self.stats.generate_statistics_report()
                print(f"Complete report generated: {report_file}")
                self.game_state = CHART_VIEWER
                self.current_chart_index = 0

    def handle_charts_view(self):
        """Handle viewing generated charts"""
        # redirect to history with charts tab
        self.history_view = 'charts'
        return self.handle_history_view()

    def show_chart_viewer(self):
        """Display a chart viewer screen showing all available charts"""
        self.screen.fill(DARK_GRAY)

        # Header
        header = self.big_font.render("Statistical Charts", True, GOLD)
        header_rect = header.get_rect(center=(WIDTH // 2, 50))
        self.screen.blit(header, header_rect)

        # Find all chart files
        charts_dir = self.stats.save_directory / "charts"
        if not charts_dir.exists():
            # No charts available yet
            no_data_text = self.font.render("No charts available. Generate charts first.", True, CREAM_WHITE)
            no_data_rect = no_data_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(no_data_text, no_data_rect)

            # Back button
            back_btn = pygame.Rect(30, HEIGHT - 80, 120, 50)
            pygame.draw.rect(self.screen, WOOD_DARK, back_btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, back_btn, 3, border_radius=10)
            back_text = self.font.render("Back", True, CREAM_WHITE)
            back_text_rect = back_text.get_rect(center=back_btn.center)
            self.screen.blit(back_text, back_text_rect)

            return back_btn, None

        # Load and display the currently selected chart
        if not hasattr(self, 'current_chart_index'):
            self.current_chart_index = 0

        # Get list of chart files
        chart_files = [f for f in charts_dir.glob("*.png")]
        if not chart_files:
            no_data_text = self.font.render("No charts available. Generate charts first.", True, CREAM_WHITE)
            no_data_rect = no_data_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(no_data_text, no_data_rect)

            # Back button
            back_btn = pygame.Rect(30, HEIGHT - 80, 120, 50)
            pygame.draw.rect(self.screen, WOOD_DARK, back_btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, back_btn, 3, border_radius=10)
            back_text = self.font.render("Back", True, CREAM_WHITE)
            back_text_rect = back_text.get_rect(center=back_btn.center)
            self.screen.blit(back_text, back_text_rect)

            return back_btn, None

        # Ensure index is valid
        if self.current_chart_index >= len(chart_files):
            self.current_chart_index = 0

        current_chart = chart_files[self.current_chart_index]

        try:
            # Load and display the chart
            chart_img = pygame.image.load(str(current_chart))

            # Scale image to fit without distortion
            img_rect = chart_img.get_rect()
            scale_factor = min(700 / img_rect.width, 500 / img_rect.height)
            new_width = int(img_rect.width * scale_factor)
            new_height = int(img_rect.height * scale_factor)
            chart_img = pygame.transform.scale(chart_img, (new_width, new_height))

            # Display chart in center area
            img_rect = chart_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(chart_img, img_rect)

            # Chart title - remove file extension and replace underscores with spaces
            chart_name = current_chart.stem.replace('_', ' ').title()
            title = self.font.render(chart_name, True, CREAM_WHITE)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 110))

            # Navigation buttons
            prev_btn = pygame.Rect(100, HEIGHT - 100, 150, 50)
            next_btn = pygame.Rect(WIDTH - 250, HEIGHT - 100, 150, 50)

            pygame.draw.rect(self.screen, BLUE, prev_btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, prev_btn, 3, border_radius=10)
            prev_text = self.font.render("Previous", True, CREAM_WHITE)
            prev_text_rect = prev_text.get_rect(center=prev_btn.center)
            self.screen.blit(prev_text, prev_text_rect)

            pygame.draw.rect(self.screen, BLUE, next_btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, next_btn, 3, border_radius=10)
            next_text = self.font.render("Next", True, CREAM_WHITE)
            next_text_rect = next_text.get_rect(center=next_btn.center)
            self.screen.blit(next_text, next_text_rect)

            # Back button
            back_btn = pygame.Rect(30, HEIGHT - 100, 50, 50)
            pygame.draw.rect(self.screen, WOOD_DARK, back_btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, back_btn, 3, border_radius=10)
            back_text = self.font.render("←", True, CREAM_WHITE)
            back_text_rect = back_text.get_rect(center=back_btn.center)
            self.screen.blit(back_text, back_text_rect)

            # Chart count indicator
            count_text = self.font.render(f"Chart {self.current_chart_index + 1} of {len(chart_files)}",
                                          True, CREAM_WHITE)
            self.screen.blit(count_text, (WIDTH // 2 - count_text.get_width() // 2, HEIGHT - 100))

            return back_btn, (prev_btn, next_btn)

        except Exception as e:
            error_text = self.font.render(f"Error loading chart: {e}", True, CREAM_WHITE)
            self.screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, HEIGHT // 2))

            # Back button only
            back_btn = pygame.Rect(30, HEIGHT - 80, 120, 50)
            pygame.draw.rect(self.screen, WOOD_DARK, back_btn, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, back_btn, 3, border_radius=10)
            back_text = self.font.render("Back", True, CREAM_WHITE)
            back_text_rect = back_text.get_rect(center=back_btn.center)
            self.screen.blit(back_text, back_text_rect)

            return back_btn, None

    def handle_chart_viewer(self):
        """Handle the chart viewer screen"""
        back_btn, nav_btns = self.show_chart_viewer()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                if back_btn and back_btn.collidepoint(mouse_pos):
                    self.game_state = self.HISTORY
                    self.history_view = 'charts'
                    return True

                if nav_btns:
                    prev_btn, next_btn = nav_btns
                    charts_dir = self.stats.save_directory / "charts"
                    chart_files = list(charts_dir.glob("*.png"))

                    if prev_btn.collidepoint(mouse_pos):
                        self.current_chart_index = (self.current_chart_index - 1) % len(chart_files)
                    elif next_btn.collidepoint(mouse_pos):
                        self.current_chart_index = (self.current_chart_index + 1) % len(chart_files)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = self.HISTORY
                    self.history_view = 'charts'
                elif event.key == pygame.K_LEFT:
                    charts_dir = self.stats.save_directory / "charts"
                    chart_files = list(charts_dir.glob("*.png"))
                    if chart_files:
                        self.current_chart_index = (self.current_chart_index - 1) % len(chart_files)
                elif event.key == pygame.K_RIGHT:
                    charts_dir = self.stats.save_directory / "charts"
                    chart_files = list(charts_dir.glob("*.png"))
                    if chart_files:
                        self.current_chart_index = (self.current_chart_index + 1) % len(chart_files)

        return True

    def handle_time_selection(self):
        self.screen.fill(DARK_GRAY)

        # title
        title = self.big_font.render("Select Time Control", True, GOLD)
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # create time buttons
        button_width, button_height = 400, 80
        buttons = []

        for i in range(4):
            y_pos = 250 + i * 100
            button = pygame.Rect(WIDTH // 2 - button_width // 2, y_pos, button_width, button_height)
            buttons.append(button)

            mouse_pos = pygame.mouse.get_pos()
            hover = button.collidepoint(mouse_pos)

            # button appearance with hover
            if hover:
                pygame.draw.rect(self.screen, LIGHT_BLUE, button.inflate(10, 10), border_radius=15)
            pygame.draw.rect(self.screen, WOOD_BROWN, button, border_radius=15)
            pygame.draw.rect(self.screen, GOLD if hover else WOOD_DARK, button, 4, border_radius=15)

            # button text
            button_font = pygame.font.Font('freesansbold.ttf', 36)
            minutes = TIME_CONTROLS[i] // 60
            text = f"{TIME_NAMES[i]}: {minutes} minute{'s' if minutes > 1 else ''}"
            button_text = button_font.render(text, True, CREAM_WHITE)
            text_rect = button_text.get_rect(center=button.center)
            self.screen.blit(button_text, text_rect)

        # back button
        back_button = pygame.Rect(30, HEIGHT - 80, 120, 50)
        back_hover = back_button.collidepoint(mouse_pos)

        if back_hover:
            pygame.draw.rect(self.screen, LIGHT_BLUE, back_button.inflate(10, 10), border_radius=10)
        pygame.draw.rect(self.screen, WOOD_DARK, back_button, border_radius=10)
        pygame.draw.rect(self.screen, GOLD if back_hover else WOOD_BROWN, back_button, 3, border_radius=10)

        back_text = self.font.render("Back", True, CREAM_WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        self.screen.blit(back_text, back_text_rect)

        # check clicks
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                if back_button.collidepoint(mouse_pos):
                    self.game_state = MENU
                    return True

                # check time choices
                for i, button in enumerate(buttons):
                    if button.collidepoint(mouse_pos):
                        self.time_control = i
                        self.white_time = TIME_CONTROLS[i]
                        self.black_time = TIME_CONTROLS[i]
                        self.start_game()
                        break

            # escape key goes back
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = MENU

        return True

    def start_game(self):
        self.game_state = PLAYING
        # reset game state
        self.turn_step = 0
        self.selection = 100
        self.valid_moves = []
        self.castling_moves = []
        self.counter = 0
        self.check = False
        self.winner = ''
        self.winner_by_time = False
        self.game_over = False
        self.white_promote = False
        self.black_promote = False
        self.promo_index = 100

        self.board.setup_board()
        self.last_move_time = pygame.time.get_ticks()

        # start tracking stats
        game_type = TIME_NAMES[self.time_control].lower()
        self.stats.game_data['game_type'] = game_type
        self.stats.start_game()

    def update_timers(self):
        # count down time for current player
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.last_move_time) / 1000

        if self.turn_step < 2:  # white's turn
            self.white_time -= elapsed
            if self.white_time <= 0:
                self.white_time = 0
                self.winner = BLACK
                self.winner_by_time = True
                self.game_over = True
        else:  # black's turn
            self.black_time -= elapsed
            if self.black_time <= 0:
                self.black_time = 0
                self.winner = WHITE
                self.winner_by_time = True
                self.game_over = True

        self.last_move_time = current_time

    def handle_gameplay(self):
        try:
            # flip board with F key
            keys = pygame.key.get_pressed()
            current_time = pygame.time.get_ticks()

            # prevent double flips
            if keys[pygame.K_f] and current_time - self.last_flip_time > 300:
                self.board_flipped = not self.board_flipped
                self.last_flip_time = current_time

            # draw game elements
            self.screen.fill(DARK_GRAY)
            self.board.draw_board(self.board_flipped)
            self.board.draw_status_area(self.turn_step, self.white_time, self.black_time)
            self.board.draw_pieces(self.turn_step, self.selection, self.board_flipped)
            self.board.draw_captured()

            # check status
            previous_check = self.check
            self.check = self.board.draw_check(self.counter, self.board_flipped)

            # track when check happens
            if self.check and not previous_check:
                self.stats.record_check()

            # pawn promotion
            if not self.game_over:
                self.check_promotion()
                if self.white_promote:
                    self.board.draw_promotion(WHITE, self.turn_step)
                    self.check_promotion_selection()
                elif self.black_promote:
                    self.board.draw_promotion(BLACK, self.turn_step)
                    self.check_promotion_selection()

            # show valid moves
            if self.selection != 100 and (self.turn_step == 1 or self.turn_step == 3):
                self.draw_valid_moves()

            # handle player clicks and keys
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.game_over:
                    if not self.white_promote and not self.black_promote:
                        self.handle_mouse_click(event.pos)
                    else:
                        self.handle_promotion_click(event.pos)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game_state = MENU
                    elif event.key == pygame.K_f:
                        pass  # already handled above
                    elif self.game_over and event.key == pygame.K_RETURN:
                        self.reset_game()

            # check for checkmate
            if not self.game_over and self.check:
                if self.turn_step < 2 and self.board.is_checkmate(WHITE):
                    self.winner = BLACK
                    self.game_over = True
                elif self.turn_step >= 2 and self.board.is_checkmate(BLACK):
                    self.winner = WHITE
                    self.game_over = True

            # game over screen
            if self.winner:
                self.draw_game_over()

                # save stats when game ends
                if self.game_over:
                    time_control = TIME_CONTROLS[self.time_control]
                    white_time_used = time_control - self.white_time
                    black_time_used = time_control - self.black_time
                    self.stats.end_game(self.winner, white_time_used, black_time_used)

        except Exception as e:
            print(f"Error in gameplay: {e.__class__.__name__}: {e}")

        return True

    def handle_mouse_click(self, pos):
        # convert mouse position to board squares
        square_size = self.board.square_size
        start_pos = self.board.start_pos

        # check if click is on the board
        if pos[0] >= start_pos and pos[0] < start_pos + square_size * 8 and \
                pos[1] >= start_pos and pos[1] < start_pos + square_size * 8:
            x_coord = (pos[0] - start_pos) // square_size
            y_coord = (pos[1] - start_pos) // square_size

            # flip coordinates if board is flipped
            if self.board_flipped:
                y_coord = 7 - y_coord
        else:
            # check forfeit button
            forfeit_rect = pygame.Rect(850, 830, 220, 50)
            if forfeit_rect.collidepoint(pos):
                self.winner = BLACK if self.turn_step <= 1 else WHITE
                self.game_over = True
            return

        click_coords = (x_coord, y_coord)

        # route to correct color handler
        if self.player_color == WHITE:
            if self.turn_step <= 1:
                self._handle_player_move(click_coords, WHITE)
            else:
                self._handle_player_move(click_coords, BLACK)
        else:
            if self.turn_step <= 1:
                self._handle_player_move(click_coords, WHITE)
            else:
                self._handle_player_move(click_coords, BLACK)

    def _handle_player_move(self, click_coords, color):
        """Handle selecting and moving pieces"""
        pieces = self.board.white_pieces if color == WHITE else self.board.black_pieces
        opponent_pieces = self.board.black_pieces if color == WHITE else self.board.white_pieces

        move_start_time = pygame.time.get_ticks()

        # selection phase
        if (self.turn_step == 0 and color == WHITE) or (self.turn_step == 2 and color == BLACK):
            for i, piece in enumerate(pieces):
                if piece.position == click_coords:
                    self.selection = i
                    self.turn_step += 1
                    self.get_valid_moves()
                    break
        # move phase
        elif (self.turn_step == 1 and color == WHITE) or (self.turn_step == 3 and color == BLACK):
            if self.selection != 100 and 0 <= self.selection < len(pieces):
                piece = pieces[self.selection]

                # calculate move time
                move_time = (pygame.time.get_ticks() - self.last_move_time) / 1000.0

                # try moving to clicked square
                if click_coords in self.valid_moves:
                    if self.is_move_safe_for_king(piece, click_coords, color):
                        # detect special moves
                        is_castling = False
                        is_en_passant = False

                        if piece.piece_type == 'king' and abs(click_coords[0] - piece.position[0]) == 2:
                            is_castling = True
                        elif piece.piece_type == 'pawn':
                            if piece.color == WHITE and click_coords == self.board.black_ep:
                                is_en_passant = True
                            elif piece.color == BLACK and click_coords == self.board.white_ep:
                                is_en_passant = True

                        self.move_piece(piece, click_coords)

                        # record the move
                        self.stats.record_move(piece.piece_type, piece.color, click_coords,
                                               is_castling, is_en_passant, move_time)

                        # end turn
                        self.turn_step = 2 if color == WHITE else 0
                        self.selection = 100
                        self.valid_moves = []
                    else:
                        print(f"Cannot move: King would be in check")

                # handle castling
                elif piece.piece_type == 'king':
                    for king_pos, rook_pos in self.castling_moves:
                        if click_coords == king_pos:
                            # find the right rook
                            rook = None
                            if king_pos[0] > piece.position[0]:  # kingside
                                rook = next((p for p in pieces if
                                             p.piece_type == 'rook' and p.position[0] > piece.position[0]), None)
                            else:  # queenside
                                rook = next((p for p in pieces if
                                             p.piece_type == 'rook' and p.position[0] < piece.position[0]), None)

                            if rook:
                                # move both pieces
                                piece.move(king_pos)
                                rook.move(rook_pos)
                                self.last_move_time = pygame.time.get_ticks()

                                # record castling
                                self.stats.record_move('king', piece.color, king_pos, True, False, move_time)

                            # end turn
                            self.turn_step = 2 if color == WHITE else 0
                            self.selection = 100
                            self.valid_moves = []
                            self.castling_moves = []

            # re-select if clicking own piece
            if any(p.position == click_coords for p in pieces):
                for i, piece in enumerate(pieces):
                    if piece.position == click_coords:
                        self.selection = i
                        self.get_valid_moves()
                        break

    def is_move_safe_for_king(self, piece, new_position, color):
        """Check if this move puts our king in danger"""
        # save current state
        original_position = piece.position
        captured_piece = self.board.get_piece_at_position(new_position)
        captured_white = None
        captured_black = None

        # simulate capture
        if captured_piece:
            if captured_piece.color == WHITE:
                self.board.white_pieces.remove(captured_piece)
                captured_white = captured_piece
            else:
                self.board.black_pieces.remove(captured_piece)
                captured_black = captured_piece

        # simulate move
        piece.position = new_position

        # check if our king is safe
        king_safe = not self.board.is_king_in_check(color)

        # restore everything
        piece.position = original_position

        if captured_white:
            self.board.white_pieces.append(captured_white)
        if captured_black:
            self.board.black_pieces.append(captured_black)

        return king_safe

    def get_valid_moves(self):
        self.valid_moves = []
        self.castling_moves = []

        if self.turn_step <= 1:
            # white's turn
            if 0 <= self.selection < len(self.board.white_pieces):
                piece = self.board.white_pieces[self.selection]
                all_possible_moves = piece.get_valid_moves()

                # only include moves that don't put king in check
                for move in all_possible_moves:
                    if self.is_move_safe_for_king(piece, move, WHITE):
                        self.valid_moves.append(move)

                # check for castling
                if piece.piece_type == 'king':
                    self.castling_moves = self.board.check_castling(piece.color)
        else:
            # black's turn
            if 0 <= self.selection < len(self.board.black_pieces):
                piece = self.board.black_pieces[self.selection]
                all_possible_moves = piece.get_valid_moves()

                # only include moves that don't put king in check
                for move in all_possible_moves:
                    if self.is_move_safe_for_king(piece, move, BLACK):
                        self.valid_moves.append(move)

                # check for castling
                if piece.piece_type == 'king':
                    self.castling_moves = self.board.check_castling(piece.color)

    def move_piece(self, piece, new_position):
        capture_occurred = False

        # check for en passant
        if piece.piece_type == 'pawn':
            if piece.color == WHITE and new_position == self.board.black_ep:
                captured_pos = (new_position[0], new_position[1] - 1)
                captured_piece = self.board.get_piece_at_position(captured_pos)
                if captured_piece:
                    self.board.black_pieces.remove(captured_piece)
                    self.board.captured_black.append(captured_piece)
                    capture_occurred = True
            elif piece.color == BLACK and new_position == self.board.white_ep:
                captured_pos = (new_position[0], new_position[1] + 1)
                captured_piece = self.board.get_piece_at_position(captured_pos)
                if captured_piece:
                    self.board.white_pieces.remove(captured_piece)
                    self.board.captured_white.append(captured_piece)
                    capture_occurred = True

        # update en passant square for future turns
        if piece.piece_type == 'pawn' and abs(piece.position[1] - new_position[1]) == 2:
            middle_y = (piece.position[1] + new_position[1]) // 2
            if piece.color == WHITE:
                self.board.white_ep = (new_position[0], middle_y)
            else:
                self.board.black_ep = (new_position[0], middle_y)
        else:
            # reset en passant
            if piece.color == WHITE:
                self.board.white_ep = (100, 100)
            else:
                self.board.black_ep = (100, 100)

        # handle normal captures
        captured_piece = self.board.get_piece_at_position(new_position)
        if captured_piece:
            if captured_piece.piece_type == 'king':
                print("Error: Cannot capture a king")
                return False

            if captured_piece.color == WHITE:
                self.board.white_pieces.remove(captured_piece)
                self.board.captured_white.append(captured_piece)
            else:
                self.board.black_pieces.remove(captured_piece)
                self.board.captured_black.append(captured_piece)
            capture_occurred = True

            # track capture
            self.stats.record_capture(captured_piece.piece_type, piece.color)

        # actually move the piece
        piece.move(new_position)
        self.last_move_time = pygame.time.get_ticks()

        # check for checkmate
        opponent_color = BLACK if piece.color == WHITE else WHITE
        if self.board.is_checkmate(opponent_color):
            self.winner = WHITE if piece.color == WHITE else BLACK
            self.game_over = True

        return True

    def check_promotion(self):
        # check if any pawns reached the end
        self.white_promote = False
        self.black_promote = False

        for i, piece in enumerate(self.board.white_pieces):
            if piece.piece_type == 'pawn' and piece.position[1] == 7:
                self.white_promote = True
                self.promo_index = i
                break

        for i, piece in enumerate(self.board.black_pieces):
            if piece.piece_type == 'pawn' and piece.position[1] == 0:
                self.black_promote = True
                self.promo_index = i
                break

    def handle_promotion_click(self, pos):
        # check which piece player wants
        panel_rect = pygame.Rect(850, 200, 300, 450)

        if not panel_rect.collidepoint(pos):
            return

        option_height = 90
        option_index = (pos[1] - (panel_rect.y + 80)) // option_height

        if option_index < 0 or option_index >= len(PROMOTION_PIECES):
            return

        promotion_piece = PROMOTION_PIECES[option_index]

        if self.white_promote:
            pawn = self.board.white_pieces[self.promo_index]
            pawn_pos = pawn.position

            # replace pawn with chosen piece
            self.board.white_pieces.pop(self.promo_index)
            self.board.white_pieces.append(ChessPiece(promotion_piece, WHITE, pawn_pos, self.board))

            self.white_promote = False

            # record promotion
            self.stats.record_promotion(promotion_piece, WHITE, pawn_pos)

            # check for checkmate
            if self.board.is_checkmate(BLACK):
                self.winner = WHITE
                self.game_over = True

        elif self.black_promote:
            pawn = self.board.black_pieces[self.promo_index]
            pawn_pos = pawn.position

            # replace pawn with chosen piece
            self.board.black_pieces.pop(self.promo_index)
            self.board.black_pieces.append(ChessPiece(promotion_piece, BLACK, pawn_pos, self.board))

            self.black_promote = False

            # record promotion
            self.stats.record_promotion(promotion_piece, BLACK, pawn_pos)

            # check for checkmate
            if self.board.is_checkmate(WHITE):
                self.winner = BLACK
                self.game_over = True

    def check_promotion_selection(self):
        # highlight which piece mouse is over
        mouse_pos = pygame.mouse.get_pos()
        panel_rect = pygame.Rect(850, 200, 300, 450)

        if panel_rect.collidepoint(mouse_pos):
            option_height = 90
            option_index = (mouse_pos[1] - (panel_rect.y + 80)) // option_height

            if 0 <= option_index < len(PROMOTION_PIECES):
                self.board.highlight_promotion_option = option_index
        else:
            self.board.highlight_promotion_option = -1

        # check for click
        if pygame.mouse.get_pressed()[0]:
            self.handle_promotion_click(mouse_pos)

    def draw_valid_moves(self):
        # show where piece can move
        self.board.draw_valid_moves(self.valid_moves, self.turn_step, self.board_flipped)

        # show castling options
        if self.castling_moves:
            self.board.draw_castling(self.castling_moves, self.turn_step, self.board_flipped)

    def draw_game_over(self):
        # dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # winner panel
        panel_width, panel_height = 500, 200
        panel_rect = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2,
                                 panel_width, panel_height)

        winner_color = WHITE if self.winner == WHITE else BLACK

        pygame.draw.rect(self.screen, WOOD_BROWN, panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, winner_color, panel_rect, 5, border_radius=15)

        # winner message
        title_font = pygame.font.Font('freesansbold.ttf', 48)
        message_font = pygame.font.Font('freesansbold.ttf', 24)

        win_text = "White Wins!" if self.winner == WHITE else "Black Wins!"

        if self.winner_by_time:
            win_text += " (Timeout)"

        title = title_font.render(win_text, True, CREAM_WHITE)
        message = message_font.render("Press Enter to play again", True, CREAM_WHITE)

        self.screen.blit(title, (panel_rect.centerx - title.get_width() // 2, panel_rect.y + 60))
        self.screen.blit(message, (panel_rect.centerx - message.get_width() // 2, panel_rect.y + 120))

        self.game_over = True

    def reset_game(self):
        # keep settings but reset board
        playing_as_white = self.board.playing_as_white
        current_time_control = self.time_control
        player_color = self.player_color

        self.board = ChessBoard(self.screen)
        self.board.playing_as_white = playing_as_white
        self.board.setup_board()

        self.turn_step = 0
        self.selection = 100
        self.valid_moves = []
        self.castling_moves = []
        self.counter = 0
        self.check = False
        self.winner = ''
        self.winner_by_time = False
        self.game_over = False
        self.white_promote = False
        self.black_promote = False
        self.promo_index = 100
        self.player_color = player_color

        # flip board for black
        self.board_flipped = (self.player_color == BLACK)

        # reset timers
        self.time_control = current_time_control
        self.white_time = TIME_CONTROLS[self.time_control]
        self.black_time = TIME_CONTROLS[self.time_control]
        self.last_move_time = pygame.time.get_ticks()