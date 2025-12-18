import chess
from chess import Square, PieceType
from src.analysis.piece_safety import is_piece_safe, to_board_piece
from src.analysis.danger_levels import move_creates_greater_threat
from src.analysis.attackers import RawMove

def is_piece_trapped(board: chess.Board, square: Square, danger_levels: bool = True) -> bool:
    """
    A piece is trapped if it is currently unsafe, and ALL its legal moves lead to unsafe squares.
    """
    piece = board.piece_at(square)
    if not piece: return False
    
    # 1. Current safety
    if is_piece_safe(board, square, piece.color):
        return False # Not trapped if currently safe?
        # TS: "If a piece is unsafe on its current square ... return !standingPieceSafety && allMovesUnsafe"
        
    # 2. Check all escapes
    # We need moves STARTING from 'square'.
    piece_moves = [m for m in board.legal_moves if m.from_square == square]
    
    all_escapes_fail = True
    
    for move in piece_moves:
        if board.piece_at(move.to_square) and board.piece_at(move.to_square).piece_type == chess.KING:
            continue # Can't capture King
            
        # Check Danger Levels (Counter threat on escape)
        # "if moving it allows the opponent a larger counterthreat"
        # We model our move as 'RawMove'
        raw_move = RawMove(piece.piece_type, piece.color, move.from_square, move.to_square)
        
        # NOTE: moveCreatesGreaterThreat usage in TS for `isPieceTrapped`:
        # "moveCreatesGreaterThreat(escapeBoard, piece, move)"
        # But `moveCreatesGreaterThreat` expects 'actingMove' to be an ATTACK on 'piece'.
        # Here 'move' is the ESCAPE move by the piece itself.
        # TS might be using valid overloading or I misunderstood.
        # "assuming that a given piece is under threat, act on the threat through a given move... 
        # For example ... moving it to safety."
        # OK, `moveCreatesGreaterThreat` works for ANY move 'actingMove'.
        # It checks if `actingMove.color` (Protag) creates new threats on THEMSELVES?
        # No, `relativeUnsafePieceAttacks` adapts to `actingMove.color`.
        # If I move my Queen (escape), do I expose my Rook?
        # Yes, that's the logic.
        
        if danger_levels and move_creates_greater_threat(board, square, raw_move):
            # If escaping creates a BIGGER threat elsewhere (e.g. unblocks a mate), then it's not a valid escape.
            # So this move counts as "unsafe".
            continue
            
        # Simulate move
        escape_board = board.copy()
        escape_board.push(move)
        
        # Check safety on new square
        # We need piece object on new square
        if is_piece_safe(escape_board, move.to_square, piece.color, move):
            all_escapes_fail = False
            break
            
    return all_escapes_fail
