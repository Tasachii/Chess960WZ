import pygame
from constants import *


class ChessPiece:
    def __init__(self, piece_type, color, position, board):
        self.piece_type = piece_type
        self.color = color
        self.position = position
        self.board = board
        self.has_moved = False
        self.load_image()

    def load_image(self):
        # Use color names for image loading
        color_name = "white" if self.color == WHITE else "black"

        try:
            img_name = f"images/{color_name} {self.piece_type}.png"
            self.image = pygame.image.load(img_name)

            # Size images for the board
            if self.piece_type == 'pawn':
                self.image = pygame.transform.scale(self.image, (65, 65))
            else:
                self.image = pygame.transform.scale(self.image, (70, 70))

            # Create small version for captured pieces
            self.small_image = pygame.transform.scale(self.image, (40, 40))
        except pygame.error as e:
            print(f"Error loading image: {e}")
            # Create placeholder if image fails to load
            self.image = self.create_placeholder_image()
            self.small_image = pygame.transform.scale(self.image, (40, 40))

    def create_placeholder_image(self):
        # Create simple colored rectangle as placeholder
        size = 70
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Fill with color
        bg_color = CREAM_WHITE if self.color == WHITE else (50, 50, 50)
        pygame.draw.rect(surface, bg_color, (0, 0, size, size))

        # Draw piece type text
        font = pygame.font.Font('freesansbold.ttf', 20)
        text = font.render(self.piece_type[0].upper(), True,
                          (50, 50, 50) if self.color == WHITE else CREAM_WHITE)
        text_rect = text.get_rect(center=(size // 2, size // 2))
        surface.blit(text, text_rect)

        # Draw border
        pygame.draw.rect(surface, GOLD, (0, 0, size, size), 2)

        return surface

    def draw(self, screen):
        square_size = self.board.square_size
        start_pos = self.board.start_pos

        x, y = self.position
        screen_x = start_pos + x * square_size
        screen_y = start_pos + y * square_size

        # Center the piece
        offset_x = (square_size - self.image.get_width()) // 2
        offset_y = (square_size - self.image.get_height()) // 2

        screen.blit(self.image, (screen_x + offset_x, screen_y + offset_y))

    def get_valid_moves(self):
        if self.piece_type == 'pawn':
            return self._check_pawn_moves()
        elif self.piece_type == 'rook':
            return self._check_rook_moves()
        elif self.piece_type == 'knight':
            return self._check_knight_moves()
        elif self.piece_type == 'bishop':
            return self._check_bishop_moves()
        elif self.piece_type == 'queen':
            return self._check_queen_moves()
        elif self.piece_type == 'king':
            moves, castling = self._check_king_moves()
            return moves

    def _check_pawn_moves(self):
        # Logic for pawn moves
        moves = []
        x, y = self.position

        if self.color == WHITE:
            # Forward moves
            if (x, y + 1) not in self.board.get_all_piece_positions() and y < 7:
                moves.append((x, y + 1))
                # First move can be two squares
                if not self.has_moved and (x, y + 2) not in self.board.get_all_piece_positions():
                    moves.append((x, y + 2))

            # Capture moves
            for dx in [-1, 1]:
                capture_pos = (x + dx, y + 1)
                if capture_pos in self.board.get_opponent_positions(self.color):
                    moves.append(capture_pos)

            # En passant
            if (x + 1, y + 1) == self.board.get_en_passant_square(BLACK):
                moves.append((x + 1, y + 1))
            if (x - 1, y + 1) == self.board.get_en_passant_square(BLACK):
                moves.append((x - 1, y + 1))
        else:
            # Black pawn moves (reverse direction)
            # Forward moves
            if (x, y - 1) not in self.board.get_all_piece_positions() and y > 0:
                moves.append((x, y - 1))
                # First move can be two squares
                if not self.has_moved and (x, y - 2) not in self.board.get_all_piece_positions():
                    moves.append((x, y - 2))

            # Capture moves
            for dx in [-1, 1]:
                capture_pos = (x + dx, y - 1)
                if capture_pos in self.board.get_opponent_positions(self.color):
                    moves.append(capture_pos)

            # En passant
            if (x + 1, y - 1) == self.board.get_en_passant_square(WHITE):
                moves.append((x + 1, y - 1))
            if (x - 1, y - 1) == self.board.get_en_passant_square(WHITE):
                moves.append((x - 1, y - 1))

        return moves

    def _check_rook_moves(self):
        # Logic for rook moves
        moves = []
        x, y = self.position

        # Check 4 directions (up, down, left, right)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            for dist in range(1, 8):  # Check all squares in a direction
                new_pos = (x + dist * dx, y + dist * dy)
                # Check if position is on the board
                if not (0 <= new_pos[0] <= 7 and 0 <= new_pos[1] <= 7):
                    break

                # Check if position has a friendly piece
                if new_pos in self.board.get_piece_positions(self.color):
                    break

                moves.append(new_pos)

                # If we hit an enemy piece, stop after adding this move
                if new_pos in self.board.get_opponent_positions(self.color):
                    break

        return moves

    def _check_knight_moves(self):
        # Logic for knight moves
        moves = []
        x, y = self.position

        # Knights move in L-shape
        possible_moves = [
            (x + 1, y + 2), (x + 2, y + 1), (x + 2, y - 1), (x + 1, y - 2),
            (x - 1, y - 2), (x - 2, y - 1), (x - 2, y + 1), (x - 1, y + 2)
        ]

        for new_pos in possible_moves:
            # Check if position is on the board
            if not (0 <= new_pos[0] <= 7 and 0 <= new_pos[1] <= 7):
                continue

            # Check if position has a friendly piece
            if new_pos in self.board.get_piece_positions(self.color):
                continue

            moves.append(new_pos)

        return moves

    def _check_bishop_moves(self):
        # Logic for bishop moves
        moves = []
        x, y = self.position

        # Check 4 diagonal directions
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for dist in range(1, 8):
                new_pos = (x + dist * dx, y + dist * dy)
                # Check if position is on the board
                if not (0 <= new_pos[0] <= 7 and 0 <= new_pos[1] <= 7):
                    break

                # Check if position has a friendly piece
                if new_pos in self.board.get_piece_positions(self.color):
                    break

                moves.append(new_pos)

                # If we hit an enemy piece, stop after adding this move
                if new_pos in self.board.get_opponent_positions(self.color):
                    break

        return moves

    def _check_queen_moves(self):
        # Queen combines rook and bishop moves
        return self._check_rook_moves() + self._check_bishop_moves()

    def _check_king_moves(self):
        # Logic for king moves
        moves = []
        castling_moves = []
        x, y = self.position

        # Regular moves in all 8 directions
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip current position

                new_pos = (x + dx, y + dy)
                # Check if position is on the board
                if not (0 <= new_pos[0] <= 7 and 0 <= new_pos[1] <= 7):
                    continue

                # Check if position has a friendly piece
                if new_pos in self.board.get_piece_positions(self.color):
                    continue

                moves.append(new_pos)

        # Castling logic is handled by the board class
        return moves, castling_moves

    def move(self, new_position):
        self.position = new_position
        self.has_moved = True