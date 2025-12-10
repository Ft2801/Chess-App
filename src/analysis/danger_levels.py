# danger_levels.py
import chess
from typing import List
from src.analysis.piece_safety import get_unsafe_pieces
from src.analysis.analysis_config import PIECE_VALUES

def move_creates_greater_threat(board: chess.Board, threatened_square: chess.Square, 
                               acting_move: chess.Move) -> bool:
    threatened_piece = board.piece_at(threatened_square)
    if not threatened_piece:
        return False

    temp_board = board.copy()
    try:
        temp_board.push(acting_move)
    except:
        return False

    acting_color = not temp_board.turn

    # Check unsafe pieces before
    # Simplified logic: compare number/value of unsafe pieces
    # For MVP, assume if we create a NEW threat on a piece >= value, it's a greater threat.
    
    current_unsafe = get_unsafe_pieces(temp_board, acting_color, acting_move)
    
    # Are there threats on pieces >= threatened_piece that weren't there before?
    # This is complex to check perfectly without diffing. 
    # Let's assume ANY threat on a Queen/Rook created is "Greater"
    
    for sq in current_unsafe:
        p = temp_board.piece_at(sq)
        if p and PIECE_VALUES[p.piece_type] >= PIECE_VALUES[threatened_piece.piece_type]:
            # Crude approximation: if we threaten a big piece, it's a "counter threat"
            return True
            
    return False
