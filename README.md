# Chess Master


A comprehensive chess game with statistics tracking and visualization built using Pygame. Chess Master provides a complete implementation of chess rules, multiple game modes, and advanced statistics to help players analyze and improve their gameplay.

## Features

### Game Features
- Complete implementation of chess rules including:
  - All standard piece movements
  - Special moves (castling, en passant, pawn promotion)
  - Check and checkmate detection
- Multiple time controls (Bullet, Blitz, Rapid, Classical)
- Play as white or black
- Board flipping with F key
- Visual move highlighting
- Check indicators and warnings
- Captured pieces display
- Game history tracking

### Statistics and Visualization
- Win rate analysis
- Game duration trends
- Piece usage statistics
- Position heatmaps
- Performance trends over time
- Comprehensive game history
- Data export to CSV

## Installation

### Prerequisites
- Python 3.8 or higher
- Pip package manager

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Tasachii/Chess_Master.git
   cd chess-master
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

Run the main script to start the game:

```bash
python main.py
```

## How to Play

### Starting a Game
1. From the main menu, select whether to play as White or Black
2. Choose your preferred time control:
   - Bullet (1 minute)
   - Blitz (3 minutes)
   - Rapid (10 minutes)
   - Classical (30 minutes)
3. The game will begin with the selected settings

### Game Controls
- **Mouse Click**: Select and move pieces
- **F Key**: Flip the board orientation
- **R Key**: Return to menu
- **Enter Key**: Reset game after checkmate

### Chess Rules
- Each piece moves according to standard chess rules
- To move a piece:
  1. Click on the piece you want to move
  2. Available moves will be highlighted
  3. Click on a valid destination square
- Special moves:
  - **Castling**: Select the king and click on the destination square two spaces away
  - **En Passant**: Capture an opponent's pawn that has just moved two squares by moving your pawn diagonally behind it
  - **Promotion**: When a pawn reaches the opposite end of the board, select the piece you want to promote to

### Game End Conditions
- **Checkmate**: When a king is in check and has no legal moves
- **Timeout**: When a player's time runs out
- **Forfeit**: Click the forfeit button to resign

## Game Statistics

Access the game statistics and visualization by clicking the "History & Stats" button on the main menu.

### Statistics Features
- **Overview**: See general statistics about your games
- **Game Details**: View detailed information about specific games
- **Statistical Analysis**: Access various charts and visualizations

### Available Charts
- Win rate distribution
- Game duration histogram
- Move count trends over time
- Piece usage statistics
- Position heatmaps
- Performance trends

### Data Export
- Export game data to CSV for external analysis

## Project Structure

```
chess-master/
├── main.py              # Main entry point
├── constants.py         # Game constants and configuration
├── chess_game.py        # Game controller class
├── chess_board.py       # Board representation and logic
├── chess_piece.py       # Piece classes and movement rules
├── chess_statistics.py  # Statistics tracking and visualization
├── images/              # Game images and assets
├── statistics/          # Generated statistics and data
│   └── charts/          # Generated charts and visualizations
└── screenshots/         # Project screenshots
    ├── gameplay/        # Game screenshots
    └── visualization/   # Visualization screenshots
```

## Technologies Used

- **Python**: Core programming language
- **Pygame**: Game development library for rendering and input handling
- **Matplotlib**: Data visualization library for charts and graphs
- **NumPy**: Library for numerical operations
- **Datetime**: Module for handling time and dates

## Development

### Future Improvements
- Online multiplayer support
- AI opponent with adjustable difficulty
- Opening book recognition
- PGN import/export
- Expanded statistics and analysis tools

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The pygame community for their excellent documentation and examples
- [Chess.com](https://www.chess.com) and [Lichess](https://lichess.org) for inspiration on chess interfaces
- Computer Programming II course at Kasetsart University