# accuracy_calculator.py
import math
from typing import Dict, Any, List
from src.analysis.expected_points import get_expected_points_loss
import chess

# --- Legacy Functions (For Backwards Compatibility with game_controller.py) ---

WINNING_CHANCES_MATE_THRESHOLD = 10000
WINNING_CHANCES_MULTIPLIER = -0.004

def winning_chances_percent(cp_eval: int) -> float:
    """Calculate winning chances percentage from centipawn evaluation."""
    if cp_eval >= WINNING_CHANCES_MATE_THRESHOLD:
        return 100.0
    if cp_eval <= -WINNING_CHANCES_MATE_THRESHOLD:
        return 0.0
    
    chances = 2 / (1 + math.exp(WINNING_CHANCES_MULTIPLIER * cp_eval)) - 1
    return 50 + 50 * max(min(chances, 1), -1)

def move_accuracy_percent(win_before: float, win_after: float) -> float:
    """Calculate move accuracy percentage from win chances before and after."""
    if win_after >= win_before:
        return 100.0
    
    win_diff = win_before - win_after
    # Formula: A * exp(B * diff) + C
    raw = 103.16 * math.exp(-4 * win_diff / 100) + (-3.16)
    return max(min(raw + 1, 100), 0)

# --- New Functions (Wintrchess Port) ---

def get_move_accuracy(prev_eval: Dict[str, Any], curr_eval: Dict[str, Any], move_color: chess.Color) -> float:
    """
    Calculate single move accuracy based on Expected Points Loss.
    Matches wintrchess accuracy.ts
    Formula: 103.16 * exp(-4 * pointLoss) - 3.17
    """
    point_loss = get_expected_points_loss(prev_eval, curr_eval, move_color)
    
    accuracy = 103.16 * math.exp(-4 * point_loss) - 3.17
    return max(0.0, min(100.0, accuracy)) # Clamp to [0, 100]

def get_game_accuracy(move_accuracies_white: List[float], move_accuracies_black: List[float]) -> Dict[str, float]:
    """
    Calculate game accuracy (average of move accuracies per side).
    Matches getGameAccuracy in wintrchess accuracy.ts
    """
    white_avg = sum(move_accuracies_white) / len(move_accuracies_white) if move_accuracies_white else 0.0
    black_avg = sum(move_accuracies_black) / len(move_accuracies_black) if move_accuracies_black else 0.0
    
    return {
        'white': white_avg,
        'black': black_avg
    }
