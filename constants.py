"""Shared constants: window/board geometry, colors, piece sets, and game states."""
WIDTH = 1200
HEIGHT = 900
FPS = 90

# --- Board / panel geometry (A13) ------------------------------------------
# The board occupies a BOARD_PX x BOARD_PX square in the top-left; the right
# panel (status, resign/quit buttons, notation) starts at x = BOARD_PX. These
# named constants replace the scattered 800 / 530,845,230 magic numbers that
# were recomputed per draw call across the render and game layers.
BOARD_PX = 800          # board area side length in pixels
SQUARE_SIZE = 90        # one square's side in pixels
BOARD_MARGIN = (BOARD_PX - 8 * SQUARE_SIZE) // 2  # centering margin (= 40)

STATUS_PANEL_X = BOARD_PX  # x of the right-hand status/control panel

# Material-advantage bar: (x, y, width, height).
MATERIAL_BAR = (530, 845, 230, 10)

# Resign / quit buttons in the status panel (offsets from STATUS_PANEL_X).
RESIGN_WHITE_RECT = (STATUS_PANEL_X + 30, 700, 170, 40)
RESIGN_BLACK_RECT = (STATUS_PANEL_X + 210, 700, 170, 40)
STATUS_QUIT_RECT = (STATUS_PANEL_X + 30, 760, 350, 50)

WHITE = 'white'
CREAM_WHITE = (255, 253, 245)
BLACK = 'black'

GRAY = 'gray'
LIGHT_GRAY = 'light gray'
DARK_GRAY = 'dark gray'
GOLD = 'gold'

WOOD_BROWN = (160, 115, 65)
WOOD_DARK = (120, 85, 45)

BOARD_LIGHT = (238, 238, 210)
BOARD_DARK = (118, 150, 86)
BOARD_HIGHLIGHT = (246, 246, 130)

GREEN = 'green'
DARK_GREEN = (0, 153, 76)

DARK_RED = 'dark red'
RED = 'red'

BLUE = 'blue'
LIGHT_BLUE = (173, 216, 230)
LIGHT_BLUE_HIGHLIGHT = (193, 226, 240)
DARK_BLUE = 'dark blue'

PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

PIECE_TYPES = ['pawn', 'queen', 'king', 'knight', 'rook', 'bishop']
PROMOTION_PIECES = ['bishop', 'knight', 'rook', 'queen']

# Promotion panel geometry (shared by draw_promotion and the hit-tests so they
# never drift out of sync). PROMO_PANEL = (x, y, width, height).
PROMO_PANEL = (850, 200, 300, 450)
PROMO_OPTION_TOP = 80   # y offset of the first option below the panel top
PROMO_OPTION_H = 90     # vertical pitch between promotion options

MENU = 0
PLAYING = 1
TIME_SELECT = 2
HISTORY = 4
CHART_VIEWER = 6

BULLET = 0
BLITZ = 1
RAPID = 2
CLASSICAL = 3

TIME_CONTROLS = [60, 180, 600, 1800]
TIME_NAMES = ["Bullet", "Blitz", "Rapid", "Classical"]