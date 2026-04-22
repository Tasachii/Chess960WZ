import pygame
import math
from constants import *
from chess_piece import ChessPiece


class ChessBoard:
    # Setup the board
    def __init__(self, screen):
        self.screen = screen
        self.white_pieces = []
        self.black_pieces = []
        self.captured_white = []
        self.captured_black = []

        # Load fonts
        try:
            self.font = pygame.font.Font('freesansbold.ttf', 20)
            self.medium_font = pygame.font.Font('freesansbold.ttf', 40)
            self.big_font = pygame.font.Font('freesansbold.ttf', 50)
        except FileNotFoundError:
            print("Warning: Font not found, using system font.")
            self.font = pygame.font.SysFont('Arial', 20)
            self.medium_font = pygame.font.SysFont('Arial', 40)
            self.big_font = pygame.font.SysFont('Arial', 50)

        self.selected_piece = None
        self.white_ep = (100, 100)  # En passant square
        self.black_ep = (100, 100)  # En passant square
        self.playing_as_white = True  # Which side player picked

        # Board size stuff
        self.square_size = 90  # Size of each square
        self.start_pos = 20  # Space from edge
        self.board_size = self.square_size * 8 + self.start_pos * 2

        # For promotion options
        self.highlight_promotion_option = -1

    def setup_board(self):
        # Clear board
        self.white_pieces = []
        self.black_pieces = []
        self.captured_white = []
        self.captured_black = []

        # Standard piece order: R N B Q K B N R
        standard_piece_types = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']

        # Add white pieces
        for i, piece_type in enumerate(standard_piece_types):
            self.white_pieces.append(ChessPiece(piece_type, WHITE, (i, 0), self))

        # Add white pawns
        for i in range(8):
            self.white_pieces.append(ChessPiece('pawn', WHITE, (i, 1), self))

        # Add black pieces
        for i, piece_type in enumerate(standard_piece_types):
            self.black_pieces.append(ChessPiece(piece_type, BLACK, (i, 7), self))

        # Add black pawns
        for i in range(8):
            self.black_pieces.append(ChessPiece('pawn', BLACK, (i, 6), self))

    def set_playing_side(self, as_white):
        self.playing_as_white = as_white
        self.setup_board()

    def draw_board(self, flipped=False):
        # Draw wooden border
        pygame.draw.rect(self.screen, WOOD_BROWN, [0, 0, self.board_size, self.board_size])

        # Draw squares
        for row in range(8):
            for col in range(8):
                screen_y = 7 - row if flipped else row

                # Calculate position
                rect = [self.start_pos + col * self.square_size,
                        self.start_pos + screen_y * self.square_size,
                        self.square_size,
                        self.square_size]

                if (row + col) % 2 == 0:
                    # Blue squares
                    color = LIGHT_BLUE
                    pygame.draw.rect(self.screen, color, rect)
                    # Add highlight
                    pygame.draw.line(self.screen, LIGHT_BLUE_HIGHLIGHT,
                                     (rect[0], rect[1]), (rect[0] + rect[2], rect[1]), 2)
                else:
                    pygame.draw.rect(self.screen, CREAM_WHITE, rect)

        # Draw labels (A-H, 1-8)
        try:
            label_font = pygame.font.Font('freesansbold.ttf', 16)
        except:
            label_font = pygame.font.SysFont('Arial', 16)

        for i in range(8):
            # File labels (A-H)
            file_label = chr(65 + i)  # A=65, B=66, etc.
            x_pos = self.start_pos + i * self.square_size + self.square_size // 2 - 5

            # Adjust if board is flipped
            if not flipped:
                self.screen.blit(label_font.render(file_label, True, WOOD_DARK), (x_pos, 5))
                self.screen.blit(label_font.render(file_label, True, WOOD_DARK), (x_pos, self.board_size - 15))
            else:
                # Flip labels when board is flipped
                rev_file = chr(65 + (7 - i))
                self.screen.blit(label_font.render(rev_file, True, WOOD_DARK), (x_pos, 5))
                self.screen.blit(label_font.render(rev_file, True, WOOD_DARK), (x_pos, self.board_size - 15))

            # Rank labels (1-8)
            rank_label = str(8 - i) if not flipped else str(i + 1)
            y_pos = self.start_pos + i * self.square_size + self.square_size // 2 - 5
            self.screen.blit(label_font.render(rank_label, True, WOOD_DARK), (5, y_pos))
            self.screen.blit(label_font.render(rank_label, True, WOOD_DARK), (self.board_size - 15, y_pos))

        # Display board info
        try:
            info_box = pygame.Rect(830, 30, 350, 100)
            pygame.draw.rect(self.screen, WOOD_BROWN, info_box, border_radius=10)
            pygame.draw.rect(self.screen, WOOD_DARK, info_box, 3, border_radius=10)

            flip_status = "Flipped (Black side)" if flipped else "Normal (White side)"
            side_text = "Playing as: White" if self.playing_as_white else "Playing as: Black"

            # Add text
            try:
                self.screen.blit(self.font.render(f"Board: {flip_status}", True, CREAM_WHITE), (850, 50))
                self.screen.blit(self.font.render(side_text, True, CREAM_WHITE), (850, 80))
            except Exception as e:
                print(f"Text error: {e}")
        except Exception as e:
            print(f"Box error: {e}")

    def draw_menu(self):
        # Background color
        self.screen.fill(DARK_GRAY)

        # Try to add piece images in background
        try:
            bg_pieces = ['king', 'queen', 'knight', 'rook']
            for i, piece_type in enumerate(bg_pieces):
                piece_img = pygame.image.load(f"images/white {piece_type}.png")
                piece_img = pygame.transform.scale(piece_img, (150, 150))
                piece_img.set_alpha(50)  # Make see-through
                self.screen.blit(piece_img, (150 + i * 250, 600))
        except:
            # Skip if images don't load
            pass

        # Add title with shadow
        title_text = "CHESS MASTER"
        shadow_font = pygame.font.Font('freesansbold.ttf', 72)
        title_font = pygame.font.Font('freesansbold.ttf', 70)

        shadow = shadow_font.render(title_text, True, WOOD_DARK)
        title = title_font.render(title_text, True, GOLD)

        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        shadow_rect = shadow.get_rect(center=(WIDTH // 2 + 4, 150 + 4))

        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)

        # Button hover effect
        button_hover = None
        mouse_pos = pygame.mouse.get_pos()

        # Make the main buttons
        white_button = pygame.Rect(WIDTH // 2 - 175, 300, 350, 90)
        black_button = pygame.Rect(WIDTH // 2 - 175, 420, 350, 90)

        # Make a quit button
        quit_button = pygame.Rect(WIDTH - 150, HEIGHT - 80, 120, 50)

        # Check if mouse is over buttons
        if white_button.collidepoint(mouse_pos):
            button_hover = "white"
        elif black_button.collidepoint(mouse_pos):
            button_hover = "black"
        elif quit_button.collidepoint(mouse_pos):
            button_hover = "quit"

        # Make white button glow if hovered
        if button_hover == "white":
            pygame.draw.rect(self.screen, LIGHT_BLUE, white_button.inflate(10, 10), border_radius=15)
        pygame.draw.rect(self.screen, WHITE, white_button, border_radius=15)
        pygame.draw.rect(self.screen, GOLD if button_hover == "white" else WOOD_DARK, white_button, 4, border_radius=15)

        # Make black button glow if hovered
        if button_hover == "black":
            pygame.draw.rect(self.screen, LIGHT_BLUE, black_button.inflate(10, 10), border_radius=15)
        pygame.draw.rect(self.screen, BLACK, black_button, border_radius=15)
        pygame.draw.rect(self.screen, GOLD if button_hover == "black" else WOOD_DARK, black_button, 4, border_radius=15)

        # Make quit button glow if hovered
        if button_hover == "quit":
            pygame.draw.rect(self.screen, LIGHT_BLUE, quit_button.inflate(10, 10), border_radius=10)
        pygame.draw.rect(self.screen, DARK_RED, quit_button, border_radius=10)
        pygame.draw.rect(self.screen, GOLD if button_hover == "quit" else WOOD_DARK, quit_button, 3, border_radius=10)

        # Add text to buttons
        white_text = self.medium_font.render("Play as White", True, 'black')
        black_text = self.medium_font.render("Play as Black", True, 'white')

        # Smaller text for quit button
        quit_font = pygame.font.Font('freesansbold.ttf', 24)
        quit_text = quit_font.render("Quit", True, 'white')

        white_text_rect = white_text.get_rect(center=white_button.center)
        black_text_rect = black_text.get_rect(center=black_button.center)
        quit_text_rect = quit_text.get_rect(center=quit_button.center)

        self.screen.blit(white_text, white_text_rect)
        self.screen.blit(black_text, black_text_rect)
        self.screen.blit(quit_text, quit_text_rect)

        # Add instructions at bottom
        instruction_font = pygame.font.Font('freesansbold.ttf', 18)
        instructions = "Press F to flip board | Press R to restart game"
        inst_text = instruction_font.render(instructions, True, LIGHT_GRAY)
        self.screen.blit(inst_text, (WIDTH // 2 - inst_text.get_width() // 2, HEIGHT - 50))

        return white_button, black_button, quit_button

    def draw_status_area(self, turn_step, white_time=0, black_time=0):
        # Status panel at the bottom
        status_rect = pygame.Rect(0, 800, WIDTH, 100)
        pygame.draw.rect(self.screen, WOOD_BROWN, status_rect)
        pygame.draw.rect(self.screen, GOLD, status_rect, 2)

        # Side panel
        side_panel = pygame.Rect(800, 0, 400, HEIGHT)
        pygame.draw.rect(self.screen, WOOD_BROWN, side_panel)
        pygame.draw.rect(self.screen, GOLD, side_panel, 2)

        # Whose turn indicator
        turn_color = WHITE if turn_step < 2 else BLACK
        turn_text = "White's Turn" if turn_step < 2 else "Black's Turn"

        # Draw turn indicator box
        turn_rect = pygame.Rect(30, 820, 180, 60)
        indicator_color = WHITE if turn_step < 2 else BLACK
        pygame.draw.rect(self.screen, indicator_color, turn_rect, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, turn_rect, 3, border_radius=10)

        turn_font = pygame.font.Font('freesansbold.ttf', 32)
        text_color = BLACK if turn_step < 2 else WHITE

        # Center the text
        turn_label = turn_font.render(turn_text, True, text_color)
        self.screen.blit(turn_label, (turn_rect.centerx - turn_label.get_width() // 2,
                                    turn_rect.centery - turn_label.get_height() // 2))

        # Display time for both sides
        time_font = pygame.font.Font('freesansbold.ttf', 32)

        # White time display
        white_minutes = int(white_time) // 60
        white_seconds = int(white_time) % 60
        white_time_text = f"{white_minutes:02d}:{white_seconds:02d}"
        white_time_label = time_font.render(white_time_text, True, 'black')

        white_time_rect = pygame.Rect(240, 820, 120, 60)
        pygame.draw.rect(self.screen, WHITE, white_time_rect, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, white_time_rect, 3, border_radius=10)
        self.screen.blit(white_time_label, (white_time_rect.centerx - white_time_label.get_width() // 2,
                                            white_time_rect.centery - white_time_label.get_height() // 2))

        # Black time display
        black_minutes = int(black_time) // 60
        black_seconds = int(black_time) % 60
        black_time_text = f"{black_minutes:02d}:{black_seconds:02d}"
        black_time_label = time_font.render(black_time_text, True, 'white')

        black_time_rect = pygame.Rect(380, 820, 120, 60)
        pygame.draw.rect(self.screen, BLACK, black_time_rect, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, black_time_rect, 3, border_radius=10)
        self.screen.blit(black_time_label, (black_time_rect.centerx - black_time_label.get_width() // 2,
                                            black_time_rect.centery - black_time_label.get_height() // 2))

        # Forfeit button
        forfeit_rect = pygame.Rect(850, 830, 220, 50)
        pygame.draw.rect(self.screen, LIGHT_GRAY, forfeit_rect, border_radius=10)
        pygame.draw.rect(self.screen, DARK_RED, forfeit_rect, 3, border_radius=10)

        forfeit_text = self.font.render("FORFEIT GAME", True, DARK_RED)
        self.screen.blit(forfeit_text, (forfeit_rect.centerx - forfeit_text.get_width() // 2,
                                        forfeit_rect.centery - forfeit_text.get_height() // 2))

        # Controls help
        controls_rect = pygame.Rect(810, 700, 380, 100)
        pygame.draw.rect(self.screen, LIGHT_GRAY, controls_rect, border_radius=10)

        self.screen.blit(self.font.render('F - Flip Board', True, 'black'), (830, 710))
        self.screen.blit(self.font.render('R - Return to Menu', True, 'black'), (830, 750))

    def draw_pieces(self, turn_step, selection, flipped=False):
        # Draw white pieces
        for i, piece in enumerate(self.white_pieces):
            x, y = piece.position
            # Flip coordinates if needed
            screen_y = 7 - y if flipped else y

            # Calculate screen position
            screen_x = self.start_pos + x * self.square_size
            screen_y = self.start_pos + screen_y * self.square_size

            # Center the pieces
            if piece.piece_type == 'pawn':
                offset_x = (self.square_size - piece.image.get_width()) // 2
                offset_y = (self.square_size - piece.image.get_height()) // 2
                self.screen.blit(piece.image, (screen_x + offset_x, screen_y + offset_y))
            else:
                offset_x = (self.square_size - piece.image.get_width()) // 2
                offset_y = (self.square_size - piece.image.get_height()) // 2
                self.screen.blit(piece.image, (screen_x + offset_x, screen_y + offset_y))

            # Highlight selected piece
            if turn_step < 2 and selection == i:
                pygame.draw.rect(self.screen, RED,
                                [screen_x + 2, screen_y + 2, self.square_size - 4, self.square_size - 4], 3,
                                border_radius=5)

        # Draw black pieces
        for i, piece in enumerate(self.black_pieces):
            x, y = piece.position
            # Flip coordinates if needed
            screen_y = 7 - y if flipped else y

            # Calculate screen position
            screen_x = self.start_pos + x * self.square_size
            screen_y = self.start_pos + screen_y * self.square_size

            # Center the pieces
            if piece.piece_type == 'pawn':
                offset_x = (self.square_size - piece.image.get_width()) // 2
                offset_y = (self.square_size - piece.image.get_height()) // 2
                self.screen.blit(piece.image, (screen_x + offset_x, screen_y + offset_y))
            else:
                offset_x = (self.square_size - piece.image.get_width()) // 2
                offset_y = (self.square_size - piece.image.get_height()) // 2
                self.screen.blit(piece.image, (screen_x + offset_x, screen_y + offset_y))

            # Highlight selected piece
            if turn_step >= 2 and selection == i:
                pygame.draw.rect(self.screen, BLUE,
                                [screen_x + 2, screen_y + 2, self.square_size - 4, self.square_size - 4], 3,
                                border_radius=5)

    def draw_captured(self):
        # Area for captured pieces
        captured_rect = pygame.Rect(810, 150, 380, 500)
        pygame.draw.rect(self.screen, LIGHT_GRAY, captured_rect, border_radius=10)

        # "Captured Pieces" title
        title_font = pygame.font.Font('freesansbold.ttf', 24)
        captured_title = title_font.render("Captured Pieces", True, 'black')
        self.screen.blit(captured_title, (captured_rect.centerx - captured_title.get_width() // 2, 160))

        # Tables for black and white pieces
        white_table = pygame.Rect(captured_rect.x + 10, 200, captured_rect.width // 2 - 20, 430)
        black_table = pygame.Rect(captured_rect.centerx + 10, 200, captured_rect.width // 2 - 20, 430)

        # Draw table areas
        pygame.draw.rect(self.screen, CREAM_WHITE, white_table, border_radius=5)
        pygame.draw.rect(self.screen, (80, 80, 80), black_table, border_radius=5)

        # Add borders
        pygame.draw.rect(self.screen, WOOD_DARK, white_table, 2, border_radius=5)
        pygame.draw.rect(self.screen, GOLD, black_table, 2, border_radius=5)

        # Table labels
        white_label = self.font.render("White", True, 'black')
        black_label = self.font.render("Black", True, 'white')

        # Display table names
        self.screen.blit(white_label, (white_table.centerx - white_label.get_width() // 2, white_table.y + 10))
        self.screen.blit(black_label, (black_table.centerx - black_label.get_width() // 2, black_table.y + 10))

        # Display captured white pieces
        piece_size = 40
        max_per_row = 3
        start_y = white_table.y + 40

        for i, piece in enumerate(self.captured_white):
            row = i // max_per_row
            col = i % max_per_row
            x_pos = white_table.x + 10 + col * (piece_size + 10)
            y_pos = start_y + row * (piece_size + 10)

            # Draw circle behind pieces
            pygame.draw.circle(self.screen, LIGHT_BLUE,
                              (x_pos + piece_size // 2, y_pos + piece_size // 2),
                              piece_size // 2 + 2)

            self.screen.blit(piece.small_image, (x_pos, y_pos))

        # Display captured black pieces
        for i, piece in enumerate(self.captured_black):
            row = i // max_per_row
            col = i % max_per_row
            x_pos = black_table.x + 10 + col * (piece_size + 10)
            y_pos = start_y + row * (piece_size + 10)

            # Draw circle behind pieces
            pygame.draw.circle(self.screen, CREAM_WHITE,
                              (x_pos + piece_size // 2, y_pos + piece_size // 2),
                              piece_size // 2 + 2)

            self.screen.blit(piece.small_image, (x_pos, y_pos))

        # Display count of captured pieces
        white_count = len(self.captured_white)
        black_count = len(self.captured_black)

        count_font = pygame.font.Font('freesansbold.ttf', 18)
        white_count_text = count_font.render(f"Pieces: {white_count}", True, 'black')
        black_count_text = count_font.render(f"Pieces: {black_count}", True, 'white')

        # Display piece count
        self.screen.blit(white_count_text, (white_table.centerx - white_count_text.get_width() // 2,
                                            white_table.bottom - 30))
        self.screen.blit(black_count_text, (black_table.centerx - black_count_text.get_width() // 2,
                                            black_table.bottom - 30))

    def draw_valid_moves(self, valid_moves, turn_step, flipped=False):
        # Draw indicators for valid moves
        color = RED if turn_step < 2 else BLUE

        for move in valid_moves:
            x, y = move
            # Flip coordinates if needed
            screen_y = 7 - y if flipped else y

            # Center position
            center_x = self.start_pos + x * self.square_size + self.square_size // 2
            center_y = self.start_pos + screen_y * self.square_size + self.square_size // 2

            # Draw translucent circle
            circle_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, color + (150,) if isinstance(color, tuple) else color, (10, 10), 10)
            self.screen.blit(circle_surf, (center_x - 10, center_y - 10))

    def draw_check(self, counter, flipped=False):
        check = False

        # Pulsating effect
        pulse_size = 4 + abs(math.sin(counter * 0.2) * 3)

        # Check if white king is in check
        white_king = next((p for p in self.white_pieces if p.piece_type == 'king'), None)
        if white_king:
            for black_piece in self.black_pieces:
                black_moves = black_piece.get_valid_moves()
                if white_king.position in black_moves:
                    check = True
                    x, y = white_king.position
                    # Flip coordinates if needed
                    screen_y = 7 - y if flipped else y

                    # Calculate screen position
                    screen_x = self.start_pos + x * self.square_size
                    screen_y = self.start_pos + screen_y * self.square_size

                    # Draw pulsing effect around king
                    rect = [screen_x - pulse_size,
                            screen_y - pulse_size,
                            self.square_size + pulse_size * 2,
                            self.square_size + pulse_size * 2]

                    pygame.draw.rect(self.screen, DARK_RED, rect, int(pulse_size), border_radius=5)

        # Check if black king is in check
        black_king = next((p for p in self.black_pieces if p.piece_type == 'king'), None)
        if black_king:
            for white_piece in self.white_pieces:
                white_moves = white_piece.get_valid_moves()
                if black_king.position in white_moves:
                    check = True
                    x, y = black_king.position
                    # Flip coordinates if needed
                    screen_y = 7 - y if flipped else y

                    # Calculate screen position
                    screen_x = self.start_pos + x * self.square_size
                    screen_y = self.start_pos + screen_y * self.square_size

                    # Draw pulsing effect around king
                    rect = [screen_x - pulse_size,
                            screen_y - pulse_size,
                            self.square_size + pulse_size * 2,
                            self.square_size + pulse_size * 2]

                    pygame.draw.rect(self.screen, DARK_BLUE, rect, int(pulse_size), border_radius=5)

        return check

    def draw_castling(self, castling_moves, turn_step, flipped=False):
        # Draw castling move indicators
        color = RED if turn_step < 2 else BLUE

        for king_pos, rook_pos in castling_moves:
            k_x, k_y = king_pos
            r_x, r_y = rook_pos

            # Flip coordinates if needed
            k_screen_y = 7 - k_y if flipped else k_y
            r_screen_y = 7 - r_y if flipped else r_y

            # Calculate screen positions
            k_screen_x = self.start_pos + k_x * self.square_size + self.square_size // 2
            k_screen_y = self.start_pos + k_screen_y * self.square_size + self.square_size // 2
            r_screen_x = self.start_pos + r_x * self.square_size + self.square_size // 2
            r_screen_y = self.start_pos + r_screen_y * self.square_size + self.square_size // 2

            # Draw connecting line
            pygame.draw.line(self.screen, color, (k_screen_x, k_screen_y + 20),
                             (r_screen_x, r_screen_y + 20), 3)

            # Draw indicators
            pygame.draw.circle(self.screen, color, (k_screen_x, k_screen_y + 20), 10)
            pygame.draw.circle(self.screen, color, (r_screen_x, r_screen_y + 20), 10)

            # Add labels
            king_label = self.font.render("King", True, 'black')
            rook_label = self.font.render("Rook", True, 'black')

            # Add background for text
            king_bg = pygame.Rect(k_screen_x - 25, k_screen_y + 30, 50, 20)
            rook_bg = pygame.Rect(r_screen_x - 25, r_screen_y + 30, 50, 20)

            pygame.draw.rect(self.screen, LIGHT_GRAY, king_bg, border_radius=5)
            pygame.draw.rect(self.screen, LIGHT_GRAY, rook_bg, border_radius=5)

            self.screen.blit(king_label, (k_screen_x - king_label.get_width() // 2, k_screen_y + 30))
            self.screen.blit(rook_label, (r_screen_x - rook_label.get_width() // 2, r_screen_y + 30))

    def draw_promotion(self, color, turn_step):
        # Panel for promotion selection
        panel_rect = pygame.Rect(850, 200, 300, 450)
        pygame.draw.rect(self.screen, WOOD_BROWN, panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 4, border_radius=15)

        # Add title
        title_font = pygame.font.Font('freesansbold.ttf', 28)
        title = title_font.render("Promote Pawn", True, CREAM_WHITE)
        self.screen.blit(title, (panel_rect.centerx - title.get_width() // 2, panel_rect.y + 20))

        # Draw divider
        pygame.draw.line(self.screen, GOLD, (panel_rect.x + 20, panel_rect.y + 60),
                         (panel_rect.right - 20, panel_rect.y + 60), 2)

        # Display promotion options
        promotions = PROMOTION_PIECES
        for i, piece_type in enumerate(promotions):
            # Create piece for option
            piece = ChessPiece(piece_type, color, (0, 0), self)

            # Make button for each option
            option_rect = pygame.Rect(panel_rect.x + 50, panel_rect.y + 80 + i * 90, 200, 70)

            # Highlight selected option
            if i == self.highlight_promotion_option if hasattr(self, 'highlight_promotion_option') else -1:
                pygame.draw.rect(self.screen, LIGHT_BLUE, option_rect, border_radius=10)
            else:
                pygame.draw.rect(self.screen, CREAM_WHITE, option_rect, border_radius=10)

            pygame.draw.rect(self.screen, GOLD, option_rect, 2, border_radius=10)

            # Draw piece image
            self.screen.blit(piece.image,
                           (option_rect.x + 20, option_rect.y + (option_rect.height - piece.image.get_height()) // 2))

            # Display piece name
            piece_name = piece_type.capitalize()
            name_text = self.font.render(piece_name, True, 'black')
            self.screen.blit(name_text, (option_rect.x + 100, option_rect.centery - name_text.get_height() // 2))

        # Draw instruction
        pygame.draw.rect(self.screen, GRAY, [0, 800, WIDTH - 200, 100])
        pygame.draw.rect(self.screen, GOLD, [0, 800, WIDTH - 200, 100], 5)

        instruction = self.big_font.render('Select Piece to Promote Pawn', True, 'black')
        self.screen.blit(instruction, (20, 820))

    def is_king_in_check(self, color):
        # Find the king
        if color == WHITE:
            king = next((p for p in self.white_pieces if p.piece_type == 'king'), None)
            opponent_pieces = self.black_pieces
        else:
            king = next((p for p in self.black_pieces if p.piece_type == 'king'), None)
            opponent_pieces = self.white_pieces

        # If king not found, return False
        if not king:
            return False

        # Check if any opponent piece can capture the king
        for piece in opponent_pieces:
            if king.position in piece.get_valid_moves():
                return True

        return False

    def is_square_under_attack(self, position, attacking_color):
        # Get opponent pieces
        if attacking_color == WHITE:
            opponent_pieces = self.white_pieces
        else:
            opponent_pieces = self.black_pieces

        # Check if any piece can move to target
        for piece in opponent_pieces:
            if position in piece.get_valid_moves():
                return True

        return False

    def is_checkmate(self, color):
        # If not in check, can't be checkmate
        if not self.is_king_in_check(color):
            return False

        # Try all possible moves to escape check
        pieces_to_check = self.white_pieces if color == WHITE else self.black_pieces

        for piece in pieces_to_check:
            valid_moves = piece.get_valid_moves()
            original_position = piece.position

            # Try each move
            for move in valid_moves:
                # Keep track of captured piece
                captured_piece = self.get_piece_at_position(move)
                captured_black = None
                captured_white = None

                # Handle piece capture
                if captured_piece is not None:
                    if captured_piece.color == WHITE:
                        self.white_pieces.remove(captured_piece)
                        captured_white = captured_piece
                    else:
                        self.black_pieces.remove(captured_piece)
                        captured_black = captured_piece

                # Simulate the move
                piece.position = move

                # Check if king is still in check
                still_in_check = self.is_king_in_check(color)

                # Undo the move
                piece.position = original_position

                # Put back any captured piece
                if captured_white is not None:
                    self.white_pieces.append(captured_white)
                if captured_black is not None:
                    self.black_pieces.append(captured_black)

                # If this move escapes check, not checkmate
                if not still_in_check:
                    return False

        # If no move escapes check, it's checkmate
        return True

    def check_castling(self, color):
        castling_moves = []

        # Can't castle while in check
        if self.is_king_in_check(color):
            return castling_moves

        # Find king and rooks
        if color == WHITE:
            king = next((p for p in self.white_pieces if p.piece_type == 'king'), None)
            rooks = [p for p in self.white_pieces if p.piece_type == 'rook']
            opponent_color = BLACK
        else:
            king = next((p for p in self.black_pieces if p.piece_type == 'king'), None)
            rooks = [p for p in self.black_pieces if p.piece_type == 'rook']
            opponent_color = WHITE

        # If king has moved, can't castle
        if not king or king.has_moved:
            return castling_moves

        # Check each rook for castling
        for rook in rooks:
            # Skip if rook has moved
            if rook.has_moved:
                continue

            # Get positions
            king_x, king_y = king.position
            rook_x, rook_y = rook.position

            # Kingside vs queenside castling
            if rook_x > king_x:  # Kingside
                # Check squares between king and rook
                path_squares = [(king_x + 1, king_y), (king_x + 2, king_y)]
                # Final positions
                king_dest = (king_x + 2, king_y)
                rook_dest = (king_x + 1, king_y)
            else:  # Queenside
                # Check squares between king and rook
                path_squares = [(king_x - 1, king_y), (king_x - 2, king_y)]
                # Extra square for queenside
                extra_square = (king_x - 3, king_y)
                # Final positions
                king_dest = (king_x - 2, king_y)
                rook_dest = (king_x - 1, king_y)

                # For queenside, check one more square
                if extra_square in self.get_all_piece_positions():
                    continue

            # Path must be clear and safe
            path_safe = True

            # Check if path is clear
            for square in path_squares:
                if square in self.get_all_piece_positions():
                    path_safe = False
                    break

            # Check if squares are safe
            for square in path_squares:
                if self.is_square_under_attack(square, opponent_color):
                    path_safe = False
                    break

            # Add castling move if ok
            if path_safe:
                castling_moves.append((king_dest, rook_dest))

        return castling_moves

    def get_piece_at_position(self, position):
        # Find piece at position
        for piece in self.white_pieces + self.black_pieces:
            if piece.position == position:
                return piece
        return None

    def get_all_piece_positions(self):
        # Get all piece positions
        return [piece.position for piece in self.white_pieces + self.black_pieces]

    def get_piece_positions(self, color):
        # Get positions of pieces by color
        if color == WHITE:
            return [piece.position for piece in self.white_pieces]
        else:
            return [piece.position for piece in self.black_pieces]

    def get_opponent_positions(self, color):
        # Get opponent piece positions
        if color == WHITE:
            return [piece.position for piece in self.black_pieces]
        else:
            return [piece.position for piece in self.white_pieces]

    def get_en_passant_square(self, color):
        # Get en passant target square
        return self.white_ep if color == WHITE else self.black_ep