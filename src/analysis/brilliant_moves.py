import chess
from chess import Square
from typing import Dict, Any, List
from src.analysis.piece_safety import get_unsafe_pieces
from src.analysis.danger_levels import has_danger_levels
from src.analysis.attackers import get_attacking_moves
from src.analysis.piece_trapped import is_piece_trapped
from src.analysis.critical_moves import is_move_critical_candidate, to_subjective_eval

def consider_brilliant_classification(
    board_before: chess.Board,
    move: chess.Move,
    prev_eval: Dict[str, Any],  # WHITE-CENTRIC
    curr_eval: Dict[str, Any]   # WHITE-CENTRIC
) -> bool:
    """
    Check if a move is Brilliant (Sacrifice + Good).
    Matches wintrchess/shared/src/lib/reporter/classification/brilliant.ts
    """
    color = board_before.turn
    
    # Convert to subjective for the candidate check
    subj_curr = to_subjective_eval(curr_eval, color)
    subj_prev = to_subjective_eval(prev_eval, color)
    
    # 1. Critical Candidate Check
    if not is_move_critical_candidate(board_before, subj_curr, subj_prev):
        print(f"    BRILLIANT FAIL: Not a critical candidate")
        return False
        
    # 2. Promotions cannot be brilliant
    if move.promotion:
        print(f"    BRILLIANT FAIL: Is a promotion")
        return False
    
    # 3. Unsafe Pieces Comparison (Sacrifice Check)
    prev_unsafe = get_unsafe_pieces(board_before, color)
    
    board_after = board_before.copy()
    board_after.push(move)
    curr_unsafe = get_unsafe_pieces(board_after, color, move)
    
    print(f"    BRILLIANT: prev_unsafe={[chess.square_name(sq) for sq in prev_unsafe]}, curr_unsafe={[chess.square_name(sq) for sq in curr_unsafe]}")
    
    # Moving a piece to safety (reducing unsafe count) is not brilliant
    if not board_after.is_check() and len(curr_unsafe) < len(prev_unsafe):
        print(f"    BRILLIANT FAIL: Reduced unsafe pieces (saving, not sacrificing)")
        return False
        
    # 4. Danger Levels (Counter-threats)
    danger_protected = True
    for sq in curr_unsafe:
        attackers = get_attacking_moves(board_after, sq, color, False)
        if not has_danger_levels(board_after, sq, attackers):
            danger_protected = False
            break
            
    if danger_protected and curr_unsafe:
        print(f"    BRILLIANT FAIL: All unsafe pieces are danger-protected (tactical trap, not sacrifice)")
        return False
        
    # 5. Trapped Pieces logic
    # Only block brilliant if we're freeing an already-trapped piece (not a real sacrifice)
    # OR if the piece being moved was trapped before (escape, not sacrifice)
    prev_trapped = [sq for sq in prev_unsafe if is_piece_trapped(board_before, sq)]
    
    moved_piece_trapped = any(sq == move.from_square for sq in prev_trapped)
    
    # If we moved a trapped piece to "sacrifice" it - not brilliant, just freeing
    if moved_piece_trapped:
        print(f"    BRILLIANT FAIL: Moving a trapped piece")
        return False
    
    # REMOVED: "freed trapped piece" check was too strict for genuine sacrifices
        
    # Final check: Must have unsafe pieces (Material offered)
    if len(curr_unsafe) == 0:
        print(f"    BRILLIANT FAIL: No unsafe pieces (no sacrifice)")
        return False
        
    print(f"    BRILLIANT PASS: Sacrifice detected!")
    return True

