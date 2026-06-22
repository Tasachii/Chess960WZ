"""Entry point: initialize pygame and run the Chess960WZ game loop."""
import pygame
from chess_game import ChessGame


def main():
    pygame.init()
    game = ChessGame()
    game.run()


if __name__ == "__main__":
    main()