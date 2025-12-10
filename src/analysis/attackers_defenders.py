# attackers_defenders.py
import chess
from typing import List

def get_attacking_moves(board: chess.Board, target_square: chess.Square, 
                       attacking_color: chess.Color, transitive: bool = True) -> List[chess.Square]:
    # Direct attackers
    direct_attackers = list(board.attackers(attacking_color, target_square))
    
    if not transitive:
        return direct_attackers
    
    all_attackers = direct_attackers.copy()
    frontier = direct_attackers.copy()
    
    while frontier:
        current_attacker = frontier.pop()
        attacker_piece = board.piece_at(current_attacker)
        
        if not attacker_piece or attacker_piece.piece_type == chess.KING:
            continue
        
        temp_board = board.copy()
        temp_board.remove_piece_at(current_attacker)
        
        new_attackers = list(temp_board.attackers(attacking_color, target_square))
        revealed_attackers = [sq for sq in new_attackers if sq not in all_attackers]
        
        all_attackers.extend(revealed_attackers)
        frontier.extend(revealed_attackers)
    
    return all_attackers

def get_defending_moves(board: chess.Board, target_square: chess.Square, 
                       defending_color: chess.Color, transitive: bool = True) -> List[chess.Square]:
    piece = board.piece_at(target_square)
    if not piece:
        return []
    
    attackers = get_attacking_moves(board, target_square, not defending_color, transitive=False)
    
    if not attackers:
        # Flip color to find potential defenders
        temp_board = board.copy()
        temp_board.remove_piece_at(target_square)
        temp_board.set_piece_at(target_square, chess.Piece(piece.piece_type, not piece.color))
        return list(temp_board.attackers(defending_color, target_square))
    
    # Find smallest recapture set
    smallest_recapture_set = None
    min_recapturers = float('inf')
    
    for attacker_square in attackers:
        attacker_piece = board.piece_at(attacker_square)
        if not attacker_piece:
            continue
        
        # Simulate capture
        temp_board = board.copy()
        temp_board.remove_piece_at(target_square)
        temp_board.set_piece_at(target_square, attacker_piece)
        temp_board.remove_piece_at(attacker_square)
        
        recapturers = get_attacking_moves(temp_board, target_square, defending_color, transitive)
        
        if len(recapturers) < min_recapturers:
            min_recapturers = len(recapturers)
            smallest_recapture_set = recapturers
    
    return smallest_recapture_set if smallest_recapture_set is not None else []
