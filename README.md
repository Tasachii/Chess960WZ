# Chess960 WZ

## Project Description

- **Project by:** _(your name here)_
- **Game Genre:** Strategy / Board Game
- **Variant:** Chess960 (Fischer Random Chess)

A two-player local Chess960 game built with Python and Pygame. Each game starts from one of 960 randomly generated positions. The app tracks detailed move statistics and visualizes them through an in-app analytics dashboard.

---

## Installation

Clone this project:

```sh
git clone https://github.com/<username>/chess960-wz.git
cd chess960-wz
```

Create and activate a virtual environment, then install dependencies:

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux:**
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide

After activating the virtual environment:

**Windows:**
```bat
python main.py
```

**Mac / Linux:**
```sh
python3 main.py
```

> Make sure the `images/` folder with piece sprites is present in the same directory as `main.py`.

---

## Tutorial / Usage

1. **Main Menu** — choose to play as White or Black.
2. **Time Control** — select Bullet, Blitz, Rapid, or Classical.
3. **In Game:**
   - Click a piece to select it (valid moves shown as dots).
   - Click a destination square to move.
   - Castling: click the king, then click the destination square shown (Chess960 castling rules apply).
   - Pawn promotion: a dialog appears automatically when a pawn reaches the last rank.
   - Press **F** to flip the board (useful for same-keyboard two-player).
   - Press **R** to return to the main menu.
4. **After the game** — the result is saved automatically and a PGN file is written to `pgn_files/`.
5. **History & Stats** — accessible from the main menu. Shows a summary table and a list of recent games.
6. **Interactive Analytics** — click the button inside History & Stats to open the dashboard. Use the buttons at the top to switch between 7 chart types and filter by side (White / Black / Both).

---

## Game Features

- Chess960 random starting position (960 unique back-rank arrangements)
- Full chess rule enforcement: legal moves, check, checkmate, stalemate detection
- Chess960-compatible castling (king slides to c- or g-file, rook slides to d- or f-file)
- En passant
- Pawn promotion dialog
- Countdown clock with four time controls (Bullet 1 min · Blitz 3 min · Rapid 10 min · Classical 30 min)
- Board flip (press F)
- Live algebraic notation panel on the right side of the board
- Resign buttons for each side
- Game-over overlay with result and replay option (Enter = new game, R = menu)
- PGN export to `pgn_files/` after each game
- Statistics saved to CSV across sessions
- Interactive Analytics Dashboard (7 chart types)

---

## Known Bugs

- Stalemate is not yet detected; the game may continue when no legal moves remain without the king being in check.
- The check indicator in `record_check()` can be called twice in the same turn (once from `draw_check` and once from `record_move`), potentially over-counting check events.

---

## Unfinished Works

- Stalemate / draw detection (50-move rule, threefold repetition, insufficient material)
- AI opponent (single-player mode)
- Online / network multiplayer
- Sound effects

---

## External Sources

1. **Pygame** — https://www.pygame.org — LGPL
2. **pandas** — https://pandas.pydata.org — BSD
3. **matplotlib** — https://matplotlib.org — PSF/matplotlib license
4. **Chess piece images** — _(add source and license here)_
5. **Chess960 algorithm reference** — https://en.wikipedia.org/wiki/Fischer_random_chess_numbering_scheme
