import chess
from typing import List, Optional, Any
from chess import Square, PieceType
from src.analysis.attackers import get_attacking_moves, RawMove, flip_color, get_turn_fen

def get_defending_moves(board: chess.Board, piece_square: Square, piece_color: chess.Color, transitive: bool = True) -> List[RawMove]:
    """
    Get moves that defend a piece.
    Matches wintrchess/shared/src/lib/reporter/utils/defenders.ts
    """
    # 1. Create defender board (copy of current)
    defender_board = board.copy()
    
    # 2. Get attackers on the piece
    attacking_moves = get_attacking_moves(defender_board, piece_square, piece_color, transitive=False)
    
    if attacking_moves:
        # Case A: There are attackers.
        # Simulate taking the piece with each attacker, and see if we can recapture.
        # "Record the minima of recaptures" -> We want the set of defenders that can recapture 
        # against the "best" attack (or any attack? TS logic takes 'minBy' length).
        
        # TS: smallestRecapturerSet = minBy(attackingMoves.map(...), recapturers => recapturers.length)
        # This implies: If multiple attackers, we find the attacker that has the FEWEST recaptures (defenders).
        # That set of recaptures represents the "Defenders".
        
        smallest_recapturer_set: Optional[List[RawMove]] = None
        min_len = float('inf')
        
        for am in attacking_moves:
            # Create board where attacker HAS captured
            # We need to simulate the move 'am'.
            capture_board = defender_board.copy()
            
            # The attacking move is 'am'. We need to make it on capture_board.
            # But 'capture_board' turn matches 'defender_board' (which is whatever passed in).
            # Attacking move is by 'am.color'.
            # We must force turn to am.color to make the move legally (or pseudo).
            capture_board.turn = am.color # Force turn
            
            # Construct chess.Move
            move_obj = chess.Move(am.from_square, am.to_square)
            
            if capture_board.is_legal(move_obj):
                capture_board.push(move_obj)
            else:
                # If illegal (e.g. pinned), this attacker actually can't capture.
                # TS: try { captureBoard.move(...) } catch { return }
                continue
                
            # Now we want "Recaptures" targeting the square (am.to_square).
            # The piece there is now the Attacker.
            # We want 'attacking_moves' on THIS new piece/square.
            # "getAttackingMoves(captureBoard, {type: am.piece, color: am.color, square: am.to}, transitive)"
            
            recapturers = get_attacking_moves(
                capture_board, 
                am.to_square, 
                am.color, 
                transitive
            )
            
            if len(recapturers) < min_len:
                min_len = len(recapturers)
                smallest_recapturer_set = recapturers
                
        return smallest_recapturer_set if smallest_recapturer_set is not None else []
            
    else:
        # Case B: No attackers.
        # "Flip the colour of the piece and count the attackers of the flipped piece"
        # i.e. If it were an enemy piece, who could attack it? Those are the defenders.
        
        # We need to manually place a piece of opposite color at 'piece_square'.
        flipped_color = flip_color(piece_color)
        piece_type = defender_board.piece_at(piece_square).piece_type
        
        defender_board.remove_piece_at(piece_square) # Remove original
        defender_board.set_piece_at(piece_square, chess.Piece(piece_type, flipped_color)) # Place flipped
        
        # Now get attackers on this flipped piece
        # "getAttackingMoves(defenderBoard, flippedPiece, transitive)"
        return get_attacking_moves(defender_board, piece_square, flipped_color, transitive)
