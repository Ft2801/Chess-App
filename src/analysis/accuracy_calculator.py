# accuracy_calculator.py
import math
from typing import List, Tuple
from src.analysis.analysis_config import (
    WINNING_CHANCES_MATE_THRESHOLD, WINNING_CHANCES_MULTIPLIER,
    ACCURACY_FORMULA_A, ACCURACY_FORMULA_B, ACCURACY_FORMULA_C,
    VOLATILITY_MAX_WEIGHT, VOLATILITY_MIN_WEIGHT, VOLATILITY_WINDOW_SIZE
)

def winning_chances_percent(cp_eval: int) -> float:
    if cp_eval >= WINNING_CHANCES_MATE_THRESHOLD:
        return 100.0
    if cp_eval <= -WINNING_CHANCES_MATE_THRESHOLD:
        return 0.0
    
    chances = 2 / (1 + math.exp(WINNING_CHANCES_MULTIPLIER * cp_eval)) - 1
    return 50 + 50 * max(min(chances, 1), -1)

def move_accuracy_percent(win_before: float, win_after: float) -> float:
    if win_after >= win_before:
        return 100.0
    
    win_diff = win_before - win_after
    raw = ACCURACY_FORMULA_A * math.exp(ACCURACY_FORMULA_B * win_diff) + ACCURACY_FORMULA_C
    return max(min(raw + 1, 100), 0)

# Note: Advanced volatility functions omitted for MVP specific needs, 
# but could be added if full session analysis is implemented.
