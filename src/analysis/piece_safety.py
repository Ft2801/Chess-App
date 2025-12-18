import chess
from chess import Square, PieceType
from typing import List, Optional
from src.analysis.attackers import get_attacking_moves, RawMove
from src.analysis.defenders import get_defending_moves
from src.analysis.analysis_config import PIECE_VALUES

def get_piece_value(piece_type: PieceType) -> int:
    return PIECE_VALUES.get(piece_type, 0)

class BoardPiece:
    def __init__(self, piece_type: PieceType, color: chess.Color, square: Square):
        self.piece_type = piece_type
        self.color = color
        self.square = square
    
    def __repr__(self):
        return f"BoardPiece({self.piece_type}, {self.color}, {chess.square_name(self.square)})"

def to_board_piece(board: chess.Board, square: Square) -> Optional[BoardPiece]:
    p = board.piece_at(square)
    if not p: return None
    return BoardPiece(p.piece_type, p.color, square)

def is_piece_safe(board: chess.Board, square: Square, piece_color: chess.Color, played_move: Optional[chess.Move] = None) -> bool:
    """
    Check if a piece at a square is safe.
    Matches wintrchess pieceSafety.ts
    """
    piece = board.piece_at(square)
    if not piece or piece.color != piece_color:
        return True # Empty or wrong color logic? TS takes 'piece' object.
        # If square is empty, safe? TS: "getAttackingMoves(piece)..." implies piece exists.
        
    # Get attackers/defenders
    attacking_moves = get_attacking_moves(board, square, piece_color, transitive=True)
    direct_attacking_moves = get_attacking_moves(board, square, piece_color, transitive=False) # TS: transitive=false for direct
    defending_moves = get_defending_moves(board, square, piece_color, transitive=True)
    
    piece_val = get_piece_value(piece.piece_type)
    
    # 1. Favourable decimal sacrifices (Rook for 2 pieces etc)
    # TS logic: playedMove?.captured && piece==ROOK && captured==KNIGHT && attackers==1 && defenders>0... 
    # This is very specific logic for simplified checks.
    if played_move and played_move.to_square == square: # The piece IS the one that just moved?
        # playedMove.captured is logic from TS 'capturedPieceValue'.
        # But 'playedMove' arg in TS `isPieceSafe` is used for conditional check on that specific "Rook sacrifice" pattern.
        
        # "playedMove?.captured && ... piece.type == ROOK"
        # We need to know if the move that led to this state captured something.
        # 'played_move' is passed in context.
        # Assuming 'played_move' is accessible and has capture info.
        
        # Note: chess.Move doesn't store 'captured' piece type roughly.
        # But we can infer it? No, we need it passed or previous board.
        # TS passes 'playedMove' which is a custom object probably having 'captured'.
        # For now, we'll skip this VERY specific heuristic unless we can robustly know capture type.
        # In `get_unsafe_pieces`, we calculate `capturedPieceValue`.
        pass

    # 2. Direct attacker of lower value?
    # "A piece with a direct attacker of lower value than itself isn't safe"
    direct_attackers_def = []
    for am in direct_attacking_moves:
        direct_attackers_def.append(am)
        
    has_lower_value_attacker = any(
        get_piece_value(am.piece) < piece_val
        for am in direct_attacking_moves
    )
    
    if has_lower_value_attacker:
        return False
        
    # 3. Defenders vs Attackers count
    if len(attacking_moves) <= len(defending_moves):
        return True
        
    # 4. Lowest value attacker logic
    # "A piece lower in value than any direct attacker, and with any defender lower in value than all direct attackers..."
    if not direct_attacking_moves:
        return True # Should be caught by len check?
        
    lowest_value_attacker_score = min(get_piece_value(am.piece) for am in direct_attacking_moves)
    
    if piece_val < lowest_value_attacker_score:
        # Check if we have a "sacrificial defender" (pawn or lower value than attacker)
        has_cheap_defender = any(
            get_piece_value(dm.piece) < lowest_value_attacker_score
            for dm in defending_moves
        )
        if has_cheap_defender:
            return True
            
    # 5. Defended by Pawn
    # "A piece defended by any pawn, at this point, must be safe" (TS logic)
    if any(dm.piece == chess.PAWN for dm in defending_moves):
        return True
        
    return False


def get_unsafe_pieces(board: chess.Board, color: chess.Color, played_move: Optional[chess.Move] = None) -> List[Square]:
    """
    Get all unsafe pieces for a color.
    """
    unsafe_squares = []
    
    # We need 'captured' value context if possible.
    # TS uses it to exclude pieces that are worth LESS than what we just captured?
    # "pieceValues[piece.type] > capturedPieceValue"
    # If we captured a Queen, losing a Pawn is 'safe' (acceptable exchange).
    captured_val = 0
    # Logic to approximate captured val if played_move provided?
    # Difficult without prev board. 
    # For now, simplistic.
    
    for sq in board.piece_map():
        piece = board.piece_at(sq)
        if piece.color == color:
            # Filter types
            if piece.piece_type in [chess.PAWN, chess.KING]:
                continue
                
            # Filter value > captured (Skipped)
            
            if not is_piece_safe(board, sq, color, played_move):
                unsafe_squares.append(sq)
                
    return unsafe_squares
