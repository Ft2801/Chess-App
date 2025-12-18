import chess
from typing import List, Optional
from chess import Square, PieceType
import copy

# Helper types equivalent to TS interfaces
class RawMove:
    def __init__(self, piece: PieceType, color: chess.Color, from_square: Square, to_square: Square):
        self.piece = piece
        self.color = color
        self.from_square = from_square
        self.to_square = to_square

    def __repr__(self):
        return f"RawMove(piece={self.piece}, color={self.color}, from={chess.square_name(self.from_square)}, to={chess.square_name(self.to_square)})"

    def __eq__(self, other):
        if not isinstance(other, RawMove):
            return False
        return (self.piece == other.piece and 
                self.color == other.color and 
                self.from_square == other.from_square and 
                self.to_square == other.to_square)

    def __hash__(self):
        return hash((self.piece, self.color, self.from_square, self.to_square))


def flip_color(color: chess.Color) -> chess.Color:
    return not color

def get_turn_fen(fen: str, color: chess.Color) -> str:
    """Sets the active color in FEN string."""
    parts = fen.split(" ")
    parts[1] = "w" if color == chess.WHITE else "b"
    # Reset castling rights or en passant if needed? TS implementation of setFenTurn just replaces the char.
    return " ".join(parts)

def direct_attacking_moves(board: chess.Board, piece_square: Square, piece_color: chess.Color) -> List[RawMove]:
    """
    Get direct attacking moves targeting a specific piece/square.
    Matches logic from wintrchess attackers.ts: directAttackingMoves
    """
    # 1. Set turn to attacker's side (opposite of piece)
    attacker_color = flip_color(piece_color)
    attacker_fen = get_turn_fen(board.fen(), attacker_color)
    attacker_board = chess.Board(attacker_fen)
    
    attacking_moves: List[RawMove] = []
    
    # 2. Find all moves that capture on the piece's square
    # Note: chess.Board.generate_legal_moves() respects turn.
    # attacker_board.legal_moves yields moves for attacker_color.
    for move in attacker_board.legal_moves:
        if move.to_square == piece_square:
            # It's a capture or move to that square (which is occupied by 'piece' on 'board', 
            # but here on 'attacker_board' it might be same piece if we just flipped turn).
            # Wait, if we just flip turn in FEN, the piece is still there. 
            # So move.to_square == piece_square is a capture.
            
            attacker_piece = attacker_board.piece_at(move.from_square)
            if attacker_piece:
                attacking_moves.append(RawMove(
                    piece=attacker_piece.piece_type,
                    color=attacker_piece.color,
                    from_square=move.from_square,
                    to_square=move.to_square
                ))
    
    # 3. Handle King attacks manual check?
    # chess.js might not generate King captures King legal moves?
    # Python-chess definitely doesn't generate moves that capture King or move King into check.
    # But here we want 'attacking moves'. 
    # TS implementation manually checks if King is attacking.
    
    # In python-chess, board.attackers(color, square) is efficient.
    # Let's verify if we should use that instead of iterating all moves.
    # TS iterates moves.
    # But python-chess has `board.attackers(attacker_color, piece_square)`.
    # This returns a Set[Square].
    # Then we can construct RawMoves.
    
    # However, strict porting of `directAttackingMoves` includes `kingAttackerSquare` check.
    # This implies we want to know if the King *could* capture it, even if illegal?
    # Or just if the King is attacking it.
    
    # Let's use `board.attackers` for robustness and simplicity where possible, 
    # but TS logic:
    # `attackerBoard.moves(...)` -> standard legal moves.
    # Then it manually adds King attack if `kingAttackerSquare` exists.
    
    # Re-implementing using python-chess `attackers`:
    attackers = attacker_board.attackers(attacker_color, piece_square)
    for sq in attackers:
        piece = attacker_board.piece_at(sq)
        if piece:
            # Verify if this attack is reachable via legal move? 
            # TS uses legal moves (checks pin).
            # `board.attackers` includes pinned pieces!
            # We must filter for legal moves if we want to match `attackerBoard.moves()`.
            # BUT, TS `directAttackingMoves` uses `attackerBoard.moves()` which ARE legal moves.
            
            # So we should stick to iterating legal moves.
            pass
            
    # Correct approach matching TS:
    # `attacking_moves` already populated from legal moves.
    
    # Now check King manual attack (often relevant if King is attacking but it's illegal due to check).
    # TS assumes `attackerBoard.attackers(piece.square)`...
    # Wait, does chess.js `attackers` include illegal ones? Yes, usually pseudo-legal.
    
    # "King cannot be at the front of a battery" handled in transitive.
    
    # Let's replicate strict TS logic:
    # The King attack might be illegal (e.g. King taking protected piece), but we count it as an attack?
    # "kingAttackerSquare ... && !attackingMoves.some(attack => attack.piece == KING)"
    # If legal moves didn't include King capture (because it's protected), we add it manually?
    # Yes. "King takes protected piece" is illegal, but it's an "attack".
    
    king_attackers = attacker_board.attackers(attacker_color, piece_square)
    king_sq = None
    for sq in king_attackers:
        p = attacker_board.piece_at(sq)
        if p and p.piece_type == chess.KING:
            king_sq = sq
            break
            
    already_has_king_attack = any(m.piece == chess.KING for m in attacking_moves)
    
    if king_sq is not None and not already_has_king_attack:
        attacking_moves.append(RawMove(
            piece=chess.KING,
            color=attacker_color,
            from_square=king_sq,
            to_square=piece_square
        ))
        
    return attacking_moves


def get_attacking_moves(board: chess.Board, piece_square: Square, piece_color: chess.Color, transitive: bool = True) -> List[RawMove]:
    """
    Get all attacking moves on a piece, optionally including transitive (revealed) attacks.
    Matches wintrchess/shared/src/lib/reporter/utils/attackers.ts
    """
    attacking_moves = direct_attacking_moves(board, piece_square, piece_color)
    
    if not transitive:
        return attacking_moves

    # Transitive logic (Batteries)
    # Frontier: List of dicts (directFen, square, type)
    frontier = []
    for am in attacking_moves:
        frontier.append({
            'directFen': board.fen(),
            'square': am.from_square,
            'type': am.piece
        })
        
    processed_configs = set() # Avoid infinite loops just in case, though TS deps on removing pieces.

    while frontier:
        attacker_info = frontier.pop()
        
        # A king cannot be at the front of a battery (TS logic)
        if attacker_info['type'] == chess.KING:
            continue
            
        transitive_board = chess.Board(attacker_info['directFen'])
        
        # Remove the piece at the front of the battery
        transitive_board.remove_piece_at(attacker_info['square'])
        
        # We need to find "revealed" attackers.
        # TS logic: 
        # 1. new_direct = directAttackingMoves(transitiveBoard)
        # 2. revealed = new_direct XOR (old_direct minus removed_piece)
        
        # Recalculate old attackers on this board BEFORE removal? 
        # No, TS says "oldAttackingMoves = directAttackingMoves(transitiveBoard, piece)" BEFORE removal?
        # NO. TS:
        # const oldAttackingMoves = directAttackingMoves(transitiveBoard, piece); <-- THIS IS WRONG in my reading?
        # Re-read TS trace:
        # const transitiveBoard = new Chess(transitiveAttacker.directFen);
        # ...
        # const oldAttackingMoves = directAttackingMoves(transitiveBoard, piece);
        # transitiveBoard.remove(transitiveAttacker.square);
        # const revealed = xorWith(old... filter(!removed), new...)
        
        # Yes, calculate atts before removal, then after removal.
        # Then find the ones that are NEW.
        
        # Note: 'transitiveBoard' is just recreated from FEN, so it's identical to parent state.
        # So 'oldAttackingMoves' should be effectively 'attackingMoves' from previous iteration (or initial).
        # We can optimize this if needed, but strict port is safer.
        
        # Restore piece for 'old' calc? 
        # Wait, step 1: create board from FEN. 
        # step 2: get attackers (old).
        # step 3: remove piece.
        # step 4: get attackers (new).
        
        old_attacking_moves = direct_attacking_moves(transitive_board, piece_square, piece_color)
        
        # Remove piece
        transitive_board.remove_piece_at(attacker_info['square'])
        
        new_attacking_moves = direct_attacking_moves(transitive_board, piece_square, piece_color)
        
        # Filter old: exclude the one we just removed
        old_filtered = [m for m in old_attacking_moves if m.from_square != attacker_info['square']]
        
        # XOR / Diff: We want moves in NEW that were NOT in OLD.
        # TS uses `xorWith`, which means elements in A but not B, OR B but not A.
        # But logically, we only care about NEWLY revealed attacks (in NEW, not in OLD).
        # If an attack disappeared (other than the removed piece), that's weird.
        # Let's stick to: revealed = [m for m in new if m not in old_filtered]
        
        # Wait, TS `xorWith` implies symmetric difference. 
        # "Find revealed attackers as a XOR between old ... and new"
        # If a piece was blocking another, removing it reveals the other.
        # So NEW has +1 attack. OLD has original attacks.
        # XOR returns the difference. 
        
        revealed_attacking_moves = []
        for nm in new_attacking_moves:
            found = False
            for om in old_filtered:
                if nm == om:
                    found = True
                    break
            if not found:
                revealed_attacking_moves.append(nm)
                
        # Also strictly, xorWith would include things in OLD not in NEW. However, that shouldn't happen for battery reveals?
        # Unless blocking piece was somehow enabling an attack? (Not standard chess).
        
        # Add to main list
        for rm in revealed_attacking_moves:
            # check uniqueness to avoid duplicates
            if rm not in attacking_moves:
                attacking_moves.append(rm)
                # Queue for recursion
                frontier.append({
                    'directFen': transitive_board.fen(),
                    'square': rm.from_square,
                    'type': rm.piece
                })
                
    return attacking_moves
