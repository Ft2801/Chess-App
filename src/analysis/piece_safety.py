# piece_safety.py
import chess
from typing import List, Optional
from src.analysis.attackers_defenders import get_attacking_moves, get_defending_moves
from src.analysis.analysis_config import PIECE_VALUES

def is_piece_safe(board: chess.Board, square: chess.Square, played_move: Optional[chess.Move] = None) -> bool:
    piece = board.piece_at(square)
    if not piece:
        return True
    
    direct_attackers = get_attacking_moves(board, square, not piece.color, transitive=False)
    all_attackers = get_attacking_moves(board, square, not piece.color, transitive=True)
    defenders = get_defending_moves(board, square, piece.color)
    
    # Favorable sacrifice check (e.g. Rook for 2 minors)
    if played_move:
        captured_piece = board.piece_at(played_move.to_square)
        if (captured_piece and 
            piece.piece_type == chess.ROOK and
            PIECE_VALUES.get(captured_piece.piece_type, 0) == PIECE_VALUES[chess.KNIGHT] and
            len(all_attackers) == 1 and len(defenders) > 0):
                return True

    # Attacked by lower value piece? Unsafe.
    for attacker_square in direct_attackers:
        attacker_piece = board.piece_at(attacker_square)
        if attacker_piece and PIECE_VALUES[attacker_piece.piece_type] < PIECE_VALUES[piece.piece_type]:
            return False
    
    # More defenders than attackers? Safe.
    if len(all_attackers) <= len(defenders):
        return True
    
    # If piece is lower value than any attacker, AND we have at least one defender lower value than attacker.
    if direct_attackers:
        lowest_attacker_val = min(PIECE_VALUES[board.piece_at(sq).piece_type] for sq in direct_attackers if board.piece_at(sq))
        
        if PIECE_VALUES[piece.piece_type] < lowest_attacker_val:
            if any(board.piece_at(d) and PIECE_VALUES[board.piece_at(d).piece_type] < lowest_attacker_val for d in defenders):
                return True

    # Defended by pawn? Generally safe.
    if any(board.piece_at(d) and board.piece_at(d).piece_type == chess.PAWN for d in defenders):
        return True
        
    return False

def get_unsafe_pieces(board: chess.Board, color: chess.Color, played_move: Optional[chess.Move] = None) -> List[chess.Square]:
    captured_val = 0
    if played_move and board.piece_at(played_move.to_square):
         captured_val = PIECE_VALUES.get(board.piece_at(played_move.to_square).piece_type, 0)
         
    unsafe = []
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if (piece and piece.color == color and 
            piece.piece_type not in [chess.PAWN, chess.KING] and
            # Only consider valuable pieces if they weren't just captured (logic simplified)
            not is_piece_safe(board, square, played_move)):
            unsafe.append(square)
    return unsafe
