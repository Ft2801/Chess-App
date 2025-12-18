import chess
from typing import Dict, Any, Optional
from src.analysis.expected_points import get_expected_points_loss
from src.analysis.piece_safety import is_piece_safe

def to_subjective_eval(eval_info: Dict[str, Any], color: chess.Color) -> Dict[str, Any]:
    """
    Convert white-centric evaluation to subjective (side-to-move) evaluation.
    If Black is to move, flip the sign.
    """
    if not eval_info:
        return {'type': 'cp', 'value': 0}
    
    result = eval_info.copy()
    if color == chess.BLACK:
        result['value'] = -eval_info.get('value', 0)
    return result

def is_move_critical_candidate(board: chess.Board, curr_eval: Dict[str, Any], prev_eval: Dict[str, Any] = None) -> bool:
    """
    Pre-check for Critical/Brilliant.
    Matches criticalMove.ts
    
    Note: curr_eval and prev_eval should already be SUBJECTIVE (from side-to-move perspective).
    """
    # 1. Winning Condition Check
    # If we were already completely winning (prev eval > 700), strict moves aren't "Critical".
    # TS checks `previous.secondSubjectiveEval`. If we have it...
    # We might not have 2nd best eval for prev?
    # Assume if curr_eval is extremely high, maybe not critical?
    
    # TS Logic:
    # if (secondSubjectiveEval && val >= 700) return false.
    # else if (current...val >= 700) return false.
    # Basically if it's too easy (already +7), not critical.
    
    val = curr_eval.get('value', 0)
    type_ = curr_eval.get('type')
    
    if type_ == 'cp' and val >= 700:
        return False
        
    # 2. Losing positions cannot be critical (from the player's perspective)
    if val < 0:
        return False
        
    # 3. Disallow Queen Promotions
    # Not passed 'move', but 'curr' usually implies checks. 
    # TS: "current.playedMove.promotion == QUEEN".
    # We'll handle this in caller or if we pass 'move'.
    # Caller 'consider_brilliant' handles promotion check explicitly.
    # 'consider_critical' handles logic?
    
    # 4. Disallow forced moves out of check
    if board.is_check():
        return False
        
    return True

def consider_critical_classification(
    board_before: chess.Board,
    move: chess.Move,
    prev_eval: Dict[str, Any],  # WHITE-CENTRIC
    curr_eval: Dict[str, Any],  # WHITE-CENTRIC
    second_best_eval: Optional[Dict[str, Any]]  # WHITE-CENTRIC
) -> bool:
    """
    Critical = The only good move.
    Matches critical.ts
    """
    color = board_before.turn
    
    # Convert to subjective (from player's perspective)
    subj_curr = to_subjective_eval(curr_eval, color)
    subj_prev = to_subjective_eval(prev_eval, color)
    
    # 1. Candidate check
    if not is_move_critical_candidate(board_before, subj_curr, subj_prev):
        return False
        
    # 2. Mate check
    # "Not critical to find moves where you have mate" (if you are already winning with mate?)
    # TS: if (current.type == mate && val > 0) return false.
    if subj_curr['type'] == 'mate' and subj_curr['value'] > 0:
        return False
        
    # 3. Capture of free material check
    # if captured && isPieceSafe(previous, capturedSquare, capturedType)
    # i.e. If we took a piece that was hanging (safe for us to take), it's trivial, not critical.
    # We need to know if captured piece was 'safe'.
    captured_piece = board_before.piece_at(move.to_square)
    if captured_piece:
        # Was this piece safe? (Defended)
        # isPieceSafe(board, square, color)
        # Note: TS calls isPieceSafe with `flipPieceColour` because it checks if the CAPTURED piece was safe.
        if not is_piece_safe(board_before, move.to_square, captured_piece.color):
             # It was hanging (unsafe). Taking a hanging piece is not Critical.
             return False
             
    # 4. Compare with Second Best
    if not second_best_eval:
        return False
    
    # Calculate loss between board eval and second best move eval    
    loss = get_expected_points_loss(prev_eval, second_best_eval, color)
    
    # 5. Threshold
    # 10% loss = middle between inaccuracy and mistake
    return loss >= 0.1
