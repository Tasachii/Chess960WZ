from datetime import datetime
from pathlib import Path


class PGNExporter:
    """Builds and saves a standard PGN file from recorded moves."""

    def __init__(self, starting_fen=None):
        self.moves = []       # list of algebraic notation strings
        self.starting_fen = starting_fen
        self.result = "*"     # unknown until game ends

        Path("pgn_files").mkdir(exist_ok=True)

    def record_move(self, notation):
        """Add one half-move in algebraic notation."""
        self.moves.append(notation)

    def set_result(self, winner):
        """winner: 'white', 'black', or 'draw'"""
        if winner == 'white':
            self.result = "1-0"
        elif winner == 'black':
            self.result = "0-1"
        else:
            self.result = "1/2-1/2"

    def export(self, filename=None):
        """Write the PGN file and return its path."""
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pgn_files/game_{ts}.pgn"

        lines = []
        lines.append('[Event "Chess960WZ"]')
        lines.append(f'[Date "{datetime.now().strftime("%Y.%m.%d")}"]')
        lines.append('[White "Player1"]')
        lines.append('[Black "Player2"]')
        lines.append(f'[Result "{self.result}"]')
        lines.append('[Variant "Chess960"]')
        if self.starting_fen:
            lines.append('[SetUp "1"]')
            lines.append(f'[FEN "{self.starting_fen}"]')
        lines.append("")

        # format move list: "1. e4 e5 2. Nf3 ..."
        move_text = ""
        for i, m in enumerate(self.moves):
            if i % 2 == 0:
                move_text += f"{i // 2 + 1}. "
            move_text += m + " "
            # wrap at ~80 chars
            if len(move_text.split('\n')[-1]) > 75:
                move_text += "\n"

        move_text += self.result
        lines.append(move_text.strip())

        with open(filename, 'w') as f:
            f.write('\n'.join(lines) + '\n')

        return filename

    @staticmethod
    def to_algebraic(piece_type, from_pos, to_pos, is_capture=False,
                     is_check=False, is_checkmate=False,
                     promotion=None, castling=None):
        """Convert move data to algebraic notation string."""
        if castling == 'kingside':
            return "O-O"
        if castling == 'queenside':
            return "O-O-O"

        files = 'abcdefgh'
        piece_symbols = {
            'king': 'K', 'queen': 'Q', 'rook': 'R',
            'bishop': 'B', 'knight': 'N', 'pawn': ''
        }

        symbol = piece_symbols.get(piece_type, '')
        from_file = files[from_pos[0]]
        to_file = files[to_pos[0]]
        to_rank = str(to_pos[1] + 1)

        if piece_type == 'pawn':
            if is_capture:
                notation = f"{from_file}x{to_file}{to_rank}"
            else:
                notation = f"{to_file}{to_rank}"
        else:
            capture_str = 'x' if is_capture else ''
            notation = f"{symbol}{capture_str}{to_file}{to_rank}"

        if promotion:
            promo_sym = piece_symbols.get(promotion, promotion[0].upper())
            notation += f"={promo_sym}"

        if is_checkmate:
            notation += "#"
        elif is_check:
            notation += "+"

        return notation