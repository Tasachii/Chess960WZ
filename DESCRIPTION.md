# Project Description

## 1. Project Overview

- **Project Name:** Chess960 WZ

- **Brief Description:**
  Chess960 WZ is a two-player Chess960 (Fischer Random Chess) desktop game built with Python and Pygame. The back rank of each side is randomized using the official 5-step combinatorial algorithm, producing one of 960 unique starting positions per game. Players choose their side (White or Black), select a time control (Bullet, Blitz, Rapid, or Classical), and then play a full chess match with standard rules including castling, en passant, and pawn promotion.

  Beyond the game itself, Chess960 WZ tracks detailed per-move and per-game statistics stored in CSV files and visualizes them through an interactive Analytics Dashboard with multiple chart types. Every finished game is also exported as a PGN file so results can be reviewed in any chess tool.

- **Problem Statement:**
  Standard chess programs almost always start from the same position, making it easy to rely on memorized openings rather than genuine strategic thinking. Chess960 forces players to think from move one. This project brings that variant to life while adding data analysis tools that let players review how they think and play over time.

- **Target Users:**
  Chess players who want to improve by reducing opening memorization, or anyone curious about personal play-style statistics.

- **Key Features:**
  - Chess960 random back-rank generation (960 unique positions)
  - Full chess rule enforcement: legal move validation, check/checkmate detection, castling (Chess960-compatible), en passant, pawn promotion
  - Four time controls: Bullet (1 min), Blitz (3 min), Rapid (10 min), Classical (30 min)
  - Board flip so either player can sit on the same keyboard
  - Move notation panel (algebraic notation, live during game)
  - PGN export after every game
  - Per-move CSV logging (piece type, move time, capture, check, castle, promotion)
  - Per-game CSV logging (winner, duration, move counts, capture counts, time used)
  - Interactive Analytics Dashboard with 7 chart types:
    - Piece Dependency (pie chart)
    - Think Time by Phase (line chart)
    - Capture Hesitation (bar chart)
    - Lethality Matrix (stacked bar)
    - Win Rates (pie chart)
    - Duration Distribution (histogram)
    - Move Count Trend (line chart)
  - Game History & Statistics summary screen

---

## 2. Concept

### 2.1 Background

Chess960 was invented by former World Champion Bobby Fischer in 1996 as a way to reduce the impact of opening theory and put the focus back on pure chess understanding. In standard chess, the first 15–20 moves of many games are essentially memorized sequences. Chess960 breaks this by randomizing the starting position while keeping all other rules identical, so players must reason independently from the very first move.

This project exists to bring Chess960 to a local two-player desktop experience while also answering a question that most chess apps ignore: *how do I actually play?* By logging every move with its timing, capture, and phase data, the analytics dashboard makes patterns visible — which pieces you rely on, how long you think in each game phase, which pieces you use to capture most aggressively.

### 2.2 Objectives

- Implement all standard chess rules correctly in an object-oriented architecture
- Generate valid Chess960 starting positions using the official 5-step algorithm
- Provide a smooth two-player local game experience with visual feedback (check highlighting, valid-move dots, promotion dialog)
- Record detailed move-level and game-level statistics automatically during play
- Visualize those statistics through an in-app interactive dashboard
- Export every game as a standard PGN file for use in external chess tools

---

## 3. UML Class Diagram

The full class diagram is attached as **`uml.pdf`** in the repository root.

**Classes and key relationships:**

```
ChessGame ──uses──> ChessBoard
ChessGame ──uses──> ChessStatistics
ChessGame ──uses──> PGNExporter
ChessGame ──uses──> Chess960Generator
ChessBoard ──contains──> Square (8×8)
ChessBoard ──contains──> ChessPiece (list)
ChessPiece <|── Pawn
ChessPiece <|── Rook
ChessPiece <|── Knight
ChessPiece <|── Bishop
ChessPiece <|── Queen
ChessPiece <|── King
```

---

## 4. Object-Oriented Programming Implementation

| Class | File | Description |
|---|---|---|
| `ChessGame` | `chess_game.py` | Main controller. Manages game state, event loop, turn logic, timer, promotion, and routing between screens. |
| `ChessBoard` | `chess_board.py` | Holds the 8×8 grid of `Square` objects and all piece lists. Handles drawing (board, pieces, valid moves, check highlight, promotion dialog, notation panel) and game-logic queries (check, checkmate, castling, en passant positions). |
| `ChessPiece` | `chess_piece.py` | Abstract base class for all pieces. Stores piece type, color, position, and `has_moved` flag. Loads the sprite image and defines the `get_valid_moves()` interface. |
| `Pawn` | `chess_piece.py` | Extends `ChessPiece`. Implements forward movement (×1 or ×2 from start), diagonal capture, and en passant detection. |
| `Rook` | `chess_piece.py` | Extends `ChessPiece`. Slides along ranks and files until blocked. |
| `Knight` | `chess_piece.py` | Extends `ChessPiece`. Jumps in L-shapes; ignores intervening pieces. |
| `Bishop` | `chess_piece.py` | Extends `ChessPiece`. Slides diagonally until blocked. |
| `Queen` | `chess_piece.py` | Extends `ChessPiece`. Combines Rook and Bishop movement. |
| `King` | `chess_piece.py` | Extends `ChessPiece`. Moves one square in any direction (castling handled separately in `ChessBoard`). |
| `Square` | `square.py` | Represents one cell (col, row). Stores the piece on it and its light/dark color. |
| `ChessStatistics` | `chess_statistics.py` | Records moves and game results to CSV files. Generates matplotlib charts for the analytics dashboard. |
| `PGNExporter` | `pgn_exporter.py` | Builds algebraic notation strings and writes standard PGN files after each game. |
| `Chess960Generator` | `chess960_generator.py` | Implements the 5-step algorithm to produce a valid Chess960 back rank and generates the starting FEN string. |

**OOP Principles used:**
- **Inheritance** — all six piece classes extend `ChessPiece`
- **Polymorphism** — `get_valid_moves()` is overridden in each subclass; `ChessGame` calls it uniformly without knowing the concrete type
- **Encapsulation** — board state, statistics, and export logic are each in dedicated classes with clear interfaces
- **Factory Pattern** — `make_piece(piece_type, color, position, board)` in `chess_piece.py` creates the correct subclass without the caller needing to import each one

---

## 5. Statistical Data

### 5.1 Data Recording Method

Data is recorded automatically during gameplay with no action required from the player.

- **Per-move data** → appended to `statistics/moves_detail.csv` after every move via `ChessStatistics.record_move()`
- **Per-game data** → appended to `statistics/games_history.csv` when the game ends via `ChessStatistics.end_game()`
- CSV files are created with headers on first run and appended on subsequent runs, so history accumulates across sessions.

### 5.2 Data Features

**`moves_detail.csv` columns:**

| Column | Type | Description |
|---|---|---|
| `game_id` | string | Timestamp-based unique ID for the game |
| `move_number` | int | Sequential move number within the game |
| `piece_type` | string | Which piece moved (pawn, rook, …) |
| `color` | string | `white` or `black` |
| `to_col` / `to_row` | int | Destination square coordinates (0–7) |
| `move_time` | float | Seconds taken to make this move |
| `is_capture` | 0/1 | Whether the move captured a piece |
| `captured_piece` | string | Type of captured piece, or `none` |
| `is_check` | 0/1 | Whether the move gave check |
| `is_castle` | 0/1 | Whether the move was a castle |
| `is_promotion` | 0/1 | Whether the move was a pawn promotion |

**`games_history.csv` columns:**

| Column | Type | Description |
|---|---|---|
| `game_id` | string | Matches moves_detail |
| `timestamp` | datetime | When the game started |
| `winner` | string | `white`, `black`, or `draw` |
| `duration` | float | Total game time in seconds |
| `total_moves` | int | Number of half-moves |
| `white_moves` / `black_moves` | int | Moves per side |
| `white_captures` / `black_captures` | int | Captures per side |
| `check_events` | int | Total check events in the game |
| `white_time_used` / `black_time_used` | float | Clock time consumed per side |
| `game_type` | string | Time control name (bullet, blitz, …) |

---

## 6. Changed Proposed Features

_(Fill in if your final implementation differs from the original proposal.)_

---

## 7. External Sources

- **Pygame** — game framework, https://www.pygame.org — LGPL license
- **pandas** — data processing, https://pandas.pydata.org — BSD license
- **matplotlib** — chart generation, https://matplotlib.org — PSF/matplotlib license
- **Chess piece images** — _(add credit and license here if images are not original)_
- **Chess960 algorithm** — based on the specification at https://en.wikipedia.org/wiki/Fischer_random_chess_numbering_scheme
