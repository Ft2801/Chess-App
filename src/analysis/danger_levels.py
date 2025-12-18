import chess
from typing import List
from chess import Square, PieceType
from src.analysis.attackers import RawMove, get_attacking_moves, flip_color
from src.analysis.piece_safety import get_unsafe_pieces, get_piece_value

def relative_unsafe_piece_attacks(action_board: chess.Board, threatened_piece_square: Square, color: chess.Color, played_move: chess.Move = None) -> List[RawMove]:
    """
    Returns attacking moves of unsafe pieces of 'color' that are higher/equal value to threatened piece.
    """
    threatened_piece = action_board.piece_at(threatened_piece_square)
    if not threatened_piece: return []
    threat_val = get_piece_value(threatened_piece.piece_type)
    
    unsafe_sqs = get_unsafe_pieces(action_board, color, played_move)
    
    result_moves = []
    for sq in unsafe_sqs:
        if sq == threatened_piece_square: continue
        
        p = action_board.piece_at(sq)
        if get_piece_value(p.piece_type) >= threat_val:
            # Get attacks FROM this unsafe piece
            # "getAttackingMoves(actionBoard, unsafePiece, false)"
            # Wait, TS: getAttackingMoves(board, unsafePiece...) -> gets moves ATTACKING the piece.
            # But here TS calls it on `unsafePiece`. 
            # `relativeUnsafePieceAttacks` -> `.map(unsafePiece => getAttackingMoves(..., unsafePiece, false))`
            # Does `getAttackingMoves` return attacks BY the piece or ON the piece?
            # looking at attackers.ts: `directAttackingMoves` filters `move.to_square == piece.square`.
            # So it returns moves ATTACKING the piece.
            
            # TS Logic: `relativeUnsafePieceAttacks` ->
            # "Returns a list of attacking moves of unsafe pieces... that are higher or equal... to threatened piece."
            # The naming is ambiguous.
            # If `getAttackingMoves` returns attacks ON `unsafePiece`, then `relativeUnsafePieceAttacks` returns attacks ON our other unsafe pieces?
            
            # Context: "Detect equal or greater counterthreats when unsafe piece is taken".
            # If I leave a Rook unsafe (threatenedPiece), but I create a threat on their Queen.
            # The Queen is now "unsafe" for them? No.
            
            # Let's re-read `dangerLevels.ts`:
            # `relativeUnsafePieceAttacks`: 
            #   getUnsafePieces(color) .map(unsafePiece => getAttackingMoves(..., unsafePiece))
            # So it gathers ALL attacks ON my unsafe pieces.
            
            # `moveCreatesGreaterThreat`:
            #  prev = relativeUnsafePieceAttacks(threatenedPiece...)
            #  move()
            #  curr = relativeUnsafePieceAttacks(threatenedPiece...)
            #  diff = curr - prev.
            # MEANING: Did I expose MORE valuable pieces to attack by moving?
            # Wait, "counterthreat".
            # If I make a move, and suddenly the opponent has NEW attacks on my pieces... that's bad.
            # But danger levels is usually "I ignore your threat because I create a BIGGER threat".
            
            # If `adaptPieceColour(actingMove.color)` is MY color.
            # `relativeUnsafePieceAttacks` finds attacks ON MY pieces.
            # If `moveCreatesGreaterThreat` checks if attacks ON MY pieces increased...
            # Then it's not "danger levels" (counter-attack), it's "hanging pieces".
            
            # Let's check `brilliant.ts`:
            # `dangerLevelsProtected = unsafePieces.every(p => hasDangerLevels(..., p, getAttackingMoves(..., p)))`
            # `current.board`, `unsafePiece` (which is MY piece).
            # `getAttackingMoves` returns opponent's moves hitting my piece.
            # `hasDangerLevels(board, threatenedPiece, actingMoves)`
            # -> `actingMoves` are the ATTACKERS (opponent moves).
            
            # `hasDangerLevels` iterates `actingMoves` (opponent's attacks).
            # calling `moveCreatesGreaterThreat(board, threatenedPiece, actingMove)`
            # `actingMove` is the OPPONENT attack.
            
            # Inside `moveCreatesGreaterThreat`:
            # `actingMove.color` is OPPONENT.
            # `relativeUnsafePieceAttacks(..., adaptPieceColour(actingMove.color))`
            # -> Gets unsafe pieces of OPPONENT.
            # -> And attacks ON OPPONENT pieces.
            
            # So:
            # 1. I left a piece unsafe.
            # 2. Opponent can take it (actingMove).
            # 3. If Opponent takes it, do THEY have unsafe pieces (Threats to THEM)?
            # 4. comparison: `newRelativeAttacks` (Threats to opponent AFTER they take) vs `previous`.
            # 5. If threats to opponent increase (or exist?), then I have a counter-threat?
            
            # Actually: "Returns whether playing the move creates a greater counterthreat than that already imposed..."
            # IF Opponent plays `actingMove` (captures my piece),
            # DO THEY CREATE A THREAT ON THEMSELVES? (i.e. move into discovered attack?)
            # OR, more likely: `relativeUnsafePieceAttacks` finds attacks on the ACTOR'S pieces.
            
            # So: `moveCreatesGreaterThreat` checks if the ACTOR (Opponent) exposes THEMSELVES to greater threats by playing the move.
            # i.e. "If you take my Rook, you hang your Queen." -> Danger Level.
            
            attacks_on_unsafe = get_attacking_moves(action_board, sq, color, False)
            result_moves.extend(attacks_on_unsafe)
            
    return result_moves

def move_creates_greater_threat(board: chess.Board, threatened_piece_square: Square, acting_move_raw: RawMove) -> bool:
    """
    Checks if 'acting_move_raw' (opponent capture) leads to bad consequences for them (Counter-threat).
    """
    # acting_move_raw is a move by Opponent.
    # acting_move_raw.color is Opponent.
    
    # 1. Existing threats to Opponent (before they move)
    prev_attacks = relative_unsafe_piece_attacks(board, threatened_piece_square, acting_move_raw.color)
    
    # 2. Make the move
    game_board = board.copy()
    move_obj = chess.Move(acting_move_raw.from_square, acting_move_raw.to_square)
    
    if not game_board.is_legal(move_obj):
        return False
        
    game_board.push(move_obj)
    
    # 3. New threats to Opponent (after they move)
    curr_attacks = relative_unsafe_piece_attacks(game_board, threatened_piece_square, acting_move_raw.color)
    
    # 4. Check if new threats exist that weren't there before
    # Simple diff: compare sets or lists
    # We rely on RawMove equality
    
    prev_set = set(prev_attacks)
    curr_set = set(curr_attacks)
    
    new_threats = curr_set - prev_set
    
    if new_threats:
        return True
        
    # Check simple mate threats (low value sacrifice for mate)
    # If the piece we (Protag) are losing is cheap, and opponent (Antag) gets mated...
    # `threatened_piece` is Protag's piece.
    # `acting_move` captures it.
    
    threatened_piece = board.piece_at(threatened_piece_square)
    if not threatened_piece: return False
    
    if get_piece_value(threatened_piece.piece_type) < get_piece_value(chess.QUEEN):
        # check for mate in moves (next turn moves for Protag)
        # game_board turn is now Protag.
        for m in game_board.legal_moves:
             game_board.push(m)
             if game_board.is_checkmate():
                 game_board.pop()
                 return True
             game_board.pop()
             
    return False

def has_danger_levels(board: chess.Board, threatened_piece_square: Square, acting_moves: List[RawMove]) -> bool:
    """
    For every way the opponent can take my piece, do they suffer a greater counter-threat?
    """
    return all(move_creates_greater_threat(board, threatened_piece_square, am) for am in acting_moves)
