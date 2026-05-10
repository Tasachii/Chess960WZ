# Project Description

## 1. Project Overview

- **Project Name:** Chess960WZ

- **Brief Description:**
  Chess960WZ is a local two-player Fischer Random Chess (Chess960) desktop application built with Python and Pygame. At the start of every game, the back-rank pieces are randomized using the official 5-step combinatorial algorithm, producing one of 960 valid starting positions. The game enforces standard chess rules in full — including Chess960-aware castling, en passant, pawn promotion, check, checkmate, and stalemate — so players are forced to think tactically from move one rather than rely on memorized openings.

  In addition to gameplay, the system acts as an analytical tool. Every move and every completed game is logged to CSV automatically, and the in-app Interactive Analytics Dashboard renders seven dynamic chart types (Piece Dependency, Capture Hesitation, Think Time by Phase, Lethality Matrix, Win Rates, Duration Distribution, Move Count Trend) with White / Black / Both side filters. Each finished match is also exported as a standard PGN file compatible with Lichess and Chess.com.

- **Problem Statement:**
  Standard chess relies heavily on memorized opening sequences, reducing the role of pure calculation in the early game. Players also lack accessible, data-driven tools for analyzing their own decision patterns — which pieces they over-rely on, how long they hesitate before captures, how their thinking speed shifts between phases. Chess960WZ addresses both: it removes opening theory from the equation and turns each played game into measurable feedback.

- **Target Users:**
  Chess players who want to train calculation skills without depending on opening preparation, and data-curious players who want to see their own playstyle quantified through real per-move statistics.

- **Key Features:**
  - Chess960 randomized starting position generator (960 unique back-ranks).
  - Full chess rule enforcement, including Chess960-aware castling, en passant, pawn promotion, check, checkmate, stalemate, and the 50-move rule.
  - Four time control modes (Bullet, Blitz, Rapid, Classical) with per-side countdown clocks.
  - Board-flip support (F key) for same-keyboard two-player play.
  - Live algebraic notation panel updating beside the board on every move.
  - Automatic PGN export after each game (`pgn_files/`).
  - Per-move and per-game CSV data logging that accumulates across sessions.
  - Interactive Analytics Dashboard with seven dynamic chart types and a White / Black / Both filter.

**Screenshots:**
- **Gameplay overview:** ![Gameplay](screenshots/gameplay/game1.png)
- **Data visualization dashboard:** ![Dashboard Overview](screenshots/visualization/dashboard_overview.png)

**Documents & Presentation:**
- **Proposal:** [Project Proposal (PDF)](proposal.pdf)
- **YouTube Presentation:** [Watch the Video Demonstration](https://youtu.be/vuvZLTAKJtE)
  *(The video covers a short intro, a demonstration of the game and statistics, an explanation of the class design, and an overview of the data visualization.)*

---

## 2. Concept

### 2.1 Background

- **Why this project exists:** Chess960 was invented by Bobby Fischer specifically to neutralize the modern reliance on memorized opening preparation. By randomizing the back-rank, both players are pulled out of theory immediately and must rely on calculation and pattern recognition from the very first move. Chess960WZ brings this variant to a clean local desktop environment without requiring an internet account or external chess engine.

- **What inspired the project:** Casual chess players often have no way to see how they actually play — which pieces they lean on, when they spend the most time thinking, which captures make them hesitate. Even strong online platforms surface aggregate ratings rather than per-move behavioral patterns. Chess960WZ was inspired by the idea that a single game already contains enough signal (40–80 timestamped moves with full context) to surface those patterns, if it is recorded carefully enough.

- **Importance of solving this problem:** Combining the calculation-first nature of Chess960 with automatic per-move data collection turns each completed game into an immediate feedback loop. Players see what they did, not just whether they won.

### 2.2 Objectives

- Implement a fully playable, object-oriented Chess960 game with an accurate rule engine — every legal move, every restriction, no shortcuts.
- Collect statistics silently in the background during normal play, with no extra steps for the user, so the game remains the focus.
- Provide a responsive Pygame GUI with helpers (valid-move dots, last-move highlight, check indicator, material bar, live notation panel, board flip).
- Ensure interoperability with the wider chess ecosystem by exporting standard PGN files that load correctly in Lichess, Chess.com, and any standard PGN viewer.
- Render the collected data through a multi-chart Interactive Analytics Dashboard so the player can explore their own patterns without leaving the app.

---

## 3. UML Class Diagram

The UML Class Diagram represents the system structure: classes, attributes, methods, and the relationships between them (composition, association, inheritance).

**Submission Requirement:**
- Attached in `.pdf` format: **[uml.pdf](uml.pdf)**

The diagram emphasizes three relationship types:
- **Composition** — `ChessGame` owns one `ChessBoard`; `ChessBoard` owns an 8×8 grid of `Square` objects; `ChessGame` owns one `ChessStatistics` and one `PGNExporter`.
- **Inheritance** — `ChessPiece` is the abstract base; `Pawn`, `Rook`, `Knight`, `Bishop`, `Queen`, and `King` each inherit from it and override `get_valid_moves()`. `Pawn` additionally overrides `get_attack_squares()` because its capture squares differ from its move squares.
- **Association** — `Square` references the `ChessPiece` currently occupying it; `Chess960Generator` is a stateless utility used by `ChessGame` at game start.

---

## 4. Object-Oriented Programming Implementation

- **ChessGame:** Top-level controller. Owns the game loop, screen routing (menu, time-select, playing, history, chart viewer), turn state, mouse / keyboard input handling, timer updates, and the orchestration of the move pipeline (selection → validation → move → notation → stats → state-check).

- **ChessBoard:** Owns the 8×8 grid of `Square` objects and the live lists of white and black pieces. Responsible for board rendering, the notation panel, the material bar, check / checkmate / stalemate detection, Chess960-aware castling validation, and en passant tracking.

- **Square:** Represents one cell on the board. Stores its grid coordinate, its visual color (light / dark based on `(col + row) % 2`), and a reference to the `ChessPiece` currently on it. Provides convenience predicates (`is_empty`, `has_enemy`, `has_ally`).

- **ChessPiece (abstract base):** Defines the shared piece interface — color, position, `has_moved` flag, image loading with placeholder fallback, and the abstract `get_valid_moves()` and `get_attack_squares()` hooks. The default `get_attack_squares()` returns the same squares as `get_valid_moves()`, which is correct for every piece except the pawn.

- **Pawn, Rook, Knight, Bishop, Queen, King:** Concrete subclasses, each implementing `get_valid_moves()` for its movement rule (one-step pawn advance with optional two-step opening, sliding rook / bishop / queen, knight L-jump, single-step king). `Pawn` additionally overrides `get_attack_squares()` so that its capture diagonals are reported even on empty squares, which is required for correct castling validation.

- **ChessStatistics:** Data engine. Maintains the per-game record dictionary, appends one row per move to `moves_detail.csv` and one row per finished game to `games_history.csv`, and uses `pandas` + `matplotlib` to render the seven dashboard charts on demand.

- **Chess960Generator:** Stateless utility. Produces a valid Chess960 back-rank using the 5-step combinatorial algorithm and translates that back-rank into a starting FEN string for the PGN headers.

- **PGNExporter:** Translation layer. Converts each move (from / to coordinates plus capture, check, mate, promotion, castling flags) into standard algebraic notation, accumulates them into a move list, and writes a well-formed `.pgn` file with the full required header block including `[Variant "Chess960"]` and `[FEN "..."]`.

---

## 5. Statistical Data

### 5.1 Data Recording Method

Data is recorded automatically during gameplay with no user intervention required.

- **Per-move data:** every completed turn appends one row to `statistics/moves_detail.csv` immediately after the move resolves. Each row carries the move number, piece type, color, destination column / row, time spent on the move (seconds), and boolean flags for capture, captured piece type, check, castle, and promotion.
- **Per-game data:** when a game ends (checkmate, stalemate, timeout, or resignation), one summary row is appended to `statistics/games_history.csv` with the game id, timestamp, winner, total duration, move counts per side, capture counts per side, total check events, time used per side, and the time-control mode label.
- Both CSVs persist across launches, so the analytics dashboard always reflects the player's full history rather than a single session.

### 5.2 Data Features

- **`games_history.csv` (one row per game):** `game_id`, `timestamp`, `winner`, `duration`, `total_moves`, `white_moves`, `black_moves`, `white_captures`, `black_captures`, `check_events`, `white_time_used`, `black_time_used`, `game_type`.
- **`moves_detail.csv` (one row per half-move):** `game_id`, `move_number`, `piece_type`, `color`, `to_col`, `to_row`, `move_time`, `is_capture`, `captured_piece`, `is_check`, `is_castle`, `is_promotion`.

These two tables together are the source for every visualization in the dashboard. The dashboard reads them fresh each time the user switches a chart or filter, so newly played games appear in the analytics immediately.

---

## 6. Changed Proposed Features

The implementation follows the v2.1 proposal closely. Two refinements were made during development:

- **Cleaner separation of concerns:** all complex board-state queries (simulated moves for checkmate / stalemate detection, castling path safety, pawn-attack coverage) live inside `ChessBoard` rather than `ChessGame`. The proposal already implied this structure; in implementation it was made strict so `ChessGame` only orchestrates and never reaches into board internals.
- **Explicit `get_attack_squares()` separate from `get_valid_moves()`:** added so that pawn capture diagonals are correctly reported on empty squares. Without it, castling validation would let the king walk through a square that an enemy pawn was actually covering. This was not in the proposal because the issue is only visible once Chess960 castling is fully implemented and tested.

All other proposed features (Chess960 generator, full rule enforcement, four time controls, live notation panel, PGN export, seven-chart analytics dashboard with side filter) are implemented as described.

---

## 7. External Sources

- **Pygame** — game rendering and event framework. Author: Pygame Community. https://www.pygame.org. License: LGPL.
- **pandas** — CSV data processing and aggregation. Author: Pandas Development Team. https://pandas.pydata.org. License: BSD.
- **matplotlib** — chart generation for the analytics dashboard. Original author: John D. Hunter. https://matplotlib.org. License: PSF / matplotlib license.
- **Chess piece images** — standard classic chess set, public domain.
- **Chess960 algorithm reference** — Fischer Random Chess numbering scheme. https://en.wikipedia.org/wiki/Fischer_random_chess_numbering_scheme.