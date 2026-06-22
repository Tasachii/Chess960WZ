"""C6 PGN round-trip + to_algebraic unit tests.

Play a scripted legal game through the pure core, export via ``PGNExporter``,
re-import with python-chess, and assert every move is legal and the final
position matches the engine's. Also checks header tags and the algebraic
notation helper (O-O / O-O-O, exd5, +, #, =Q).
"""
import io

import chess
import chess.pgn

from chess_core import BLACK, WHITE, CoreBoard
from chess960_generator import Chess960Generator
from pgn_exporter import PGNExporter

from _core_helpers import OTHER

STANDARD = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']

# Scholar's mate: 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#  (last move is a capture + mate)
SCHOLARS_MATE = [
    ('pawn', (4, 1), (4, 3), WHITE),
    ('pawn', (4, 6), (4, 4), BLACK),
    ('bishop', (5, 0), (2, 3), WHITE),
    ('knight', (1, 7), (2, 5), BLACK),
    ('queen', (3, 0), (7, 4), WHITE),
    ('knight', (6, 7), (5, 5), BLACK),
    ('queen', (7, 4), (5, 6), WHITE),
]


def _play_and_export(script, back_rank, result, tmp_path):
    """Drive the core through ``script``, build notation as the game does, and
    export a PGN to ``tmp_path``. Returns (pgn_text, final_core_board)."""
    b = CoreBoard()
    b.setup_board(back_rank)
    pgn = PGNExporter(Chess960Generator.starting_fen(back_rank))

    for piece_type, frm, to, color in script:
        piece = b.get_piece_at_position(frm)
        assert piece is not None and piece.piece_type == piece_type
        assert tuple(to) in b.get_valid_moves_for(piece, color)
        is_capture = b.get_piece_at_position(to) is not None
        b.move_piece(piece, to)
        opp = OTHER[color]
        is_check = b.is_king_in_check(opp)
        is_mate = b.is_checkmate(opp)
        notation = PGNExporter.to_algebraic(
            piece_type, frm, to,
            is_capture=is_capture, is_check=is_check, is_checkmate=is_mate,
        )
        pgn.record_move(notation)

    pgn.set_result(result)
    out_file = tmp_path / "game.pgn"
    pgn.export(filename=str(out_file))
    return out_file.read_text(), b


def test_scripted_game_round_trips_through_python_chess(tmp_path):
    text, core = _play_and_export(SCHOLARS_MATE, STANDARD, 'white', tmp_path)

    game = chess.pgn.read_game(io.StringIO(text))
    assert game is not None

    board = game.board()
    move_count = 0
    for move in game.mainline_moves():
        assert move in board.legal_moves, f"illegal move {move} at {board.fen()}"
        board.push(move)
        move_count += 1
    assert move_count == len(SCHOLARS_MATE)

    # the reference engine confirms checkmate, matching the core
    assert board.is_checkmate()
    assert core.is_checkmate(BLACK)

    # final piece placement matches between core and python-chess
    ref_placement = board.board_fen().split()[0]
    assert ref_placement == _core_placement_fen(core)


def _core_placement_fen(board: CoreBoard) -> str:
    """Render the core board's piece placement as a FEN board field (rank 8..1)."""
    symbols = {'pawn': 'p', 'knight': 'n', 'bishop': 'b',
               'rook': 'r', 'queen': 'q', 'king': 'k'}
    grid = [['' for _ in range(8)] for _ in range(8)]
    for p in board.white_pieces:
        c, r = p.position
        grid[r][c] = symbols[p.piece_type].upper()
    for p in board.black_pieces:
        c, r = p.position
        grid[r][c] = symbols[p.piece_type]
    rows = []
    for r in range(7, -1, -1):
        row = ''
        empty = 0
        for c in range(8):
            if grid[r][c]:
                if empty:
                    row += str(empty)
                    empty = 0
                row += grid[r][c]
            else:
                empty += 1
        if empty:
            row += str(empty)
        rows.append(row)
    return '/'.join(rows)


def test_pgn_header_tags(tmp_path):
    text, _ = _play_and_export(SCHOLARS_MATE, STANDARD, 'white', tmp_path)
    assert '[Variant "Chess960"]' in text
    assert '[SetUp "1"]' in text
    assert '[FEN "' in text
    assert '[Result "1-0"]' in text       # white win mapping


def test_pgn_header_includes_sp_number(tmp_path):
    # When an SP-number is supplied, it is emitted as an [Opening] tag.
    sp = Chess960Generator.sp_number(STANDARD)  # 518 for the standard arrangement
    b = CoreBoard()
    b.setup_board(STANDARD)
    pgn = PGNExporter(Chess960Generator.starting_fen(STANDARD), sp_number=sp)
    pgn.record_move("e4")
    pgn.set_result('draw')
    out_file = tmp_path / "sp.pgn"
    pgn.export(filename=str(out_file))
    text = out_file.read_text()
    assert f'[Opening "Chess960 SP{sp}"]' in text
    assert sp == 518


def test_pgn_result_mapping(tmp_path):
    _, _ = _play_and_export(SCHOLARS_MATE, STANDARD, 'white', tmp_path)
    for winner, tag in [('white', '1-0'), ('black', '0-1'), ('draw', '1/2-1/2')]:
        exporter = PGNExporter("startfen")
        exporter.set_result(winner)
        assert exporter.result == tag


# ----------------------------------------------------------- to_algebraic units

def test_to_algebraic_castling():
    assert PGNExporter.to_algebraic('king', (4, 0), (6, 0), castling='kingside') == "O-O"
    assert PGNExporter.to_algebraic('king', (4, 0), (2, 0), castling='queenside') == "O-O-O"


def test_to_algebraic_pawn_capture():
    # e-file pawn capturing onto d5 -> exd5
    assert PGNExporter.to_algebraic('pawn', (4, 3), (3, 4), is_capture=True) == "exd5"


def test_to_algebraic_check_and_mate():
    assert PGNExporter.to_algebraic('queen', (7, 4), (7, 6), is_check=True) == "Qh7+"
    assert PGNExporter.to_algebraic('queen', (5, 4), (5, 6), is_checkmate=True) == "Qf7#"


def test_to_algebraic_promotion():
    # pawn promoting on e8 to a queen
    assert PGNExporter.to_algebraic('pawn', (4, 6), (4, 7), promotion='queen') == "e8=Q"


def test_to_algebraic_piece_move():
    assert PGNExporter.to_algebraic('knight', (6, 0), (5, 2)) == "Nf3"
    assert PGNExporter.to_algebraic('bishop', (5, 0), (2, 3), is_capture=True) == "Bxc4"
