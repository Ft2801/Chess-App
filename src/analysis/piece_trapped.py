# piece_trapped.py
import chess
from src.analysis.piece_safety import is_piece_safe
from src.analysis.danger_levels import move_creates_greater_threat

def is_piece_trapped(board: chess.Board, square: chess.Square) -> bool:
    piece = board.piece_at(square)
    if not piece or is_piece_safe(board, square):
        return False
        
    temp_board = board.copy()
    temp_board.turn = piece.color
    
    moves = [m for m in temp_board.legal_moves if m.from_square == square]
    
    for move in moves:
        temp_board.push(move)
        safe = is_piece_safe(temp_board, move.to_square, move)
        temp_board.pop()
        
        if safe:
            return False
            
    return True
