# Screen dimensions and settings
WIDTH = 1200
HEIGHT = 900
FPS = 90

# Colors
WHITE = 'white'
CREAM_WHITE = (255, 253, 245)
BLACK = 'black'

GRAY = 'gray'
LIGHT_GRAY = 'light gray'
DARK_GRAY = 'dark gray'

GOLD = 'gold'

WOOD_BROWN = (160, 115, 65)
WOOD_DARK = (120, 85, 45)

GREEN = 'green'
DARK_GREEN = (0, 153, 76)

DARK_RED = 'dark red'
RED = 'red'

BLUE = 'blue'
LIGHT_BLUE = (173, 216, 230)
LIGHT_BLUE_HIGHLIGHT = (193, 226, 240)
DARK_BLUE = 'dark blue'

# Add missing colors
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Piece types
PIECE_TYPES = ['pawn', 'queen', 'king', 'knight', 'rook', 'bishop']
PROMOTION_PIECES = ['bishop', 'knight', 'rook', 'queen']

# Game states
MENU = 0
PLAYING = 1
TIME_SELECT = 2
CHART_VIEWER = 6  # game state for viewing charts

# Time controls
BULLET = 0  # 1 min
BLITZ = 1   # 3 min
RAPID = 2   # 10 min
CLASSICAL = 3  # 30 min

# Time in seconds
TIME_CONTROLS = [60, 180, 600, 1800]  # 1, 3, 10, 30 minutes
TIME_NAMES = ["Bullet", "Blitz", "Rapid", "Classical"]