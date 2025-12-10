# critical_moves.py
import chess
from typing import Dict, Any
from src.analysis.analysis_config import CRITICAL_EVAL_THRESHOLD

def is_move_critical_candidate(previous_eval: Dict[str, Any], current_eval: Dict[str, Any], 
                              board_before: chess.Board) -> bool:
    
    # If previously winning > +7, not critical
    if previous_eval.get('type') == 'cp':
        if previous_eval.get('value', 0) >= CRITICAL_EVAL_THRESHOLD:
            return False
    elif current_eval.get('type') == 'cp':
        if current_eval.get('value', 0) >= CRITICAL_EVAL_THRESHOLD:
            return False
    
    # Losing positions not critical
    if current_eval.get('type') == 'cp' and current_eval.get('value', 0) < 0:
        return False
    
    if board_before.is_check():
        return False
    
    return True
