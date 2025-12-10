# analysis_config.py
"""
Configuration constants for the analysis modules.
Extracted from Scacchi-main/src/config.py
"""
import chess

# --- PIECE VALUES ---
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# --- EVALUATION THRESHOLDS ---
EVAL_THRESHOLDS = {
    'brilliant': -200,
    'great': -100,
    'best': 5,
    'excellent': 20,
    'good': 50,
    'inaccuracy': 100,
    'mistake': 200,
}

# --- CLASSIFICATION LABELS ---
EVAL_CLASSIFICATIONS = {
    'brilliant': "Brilliant (!!)",
    'great': "Great Move (!)",
    'best': "Best (=)",
    'excellent': "Excellent",
    'good': "Good",
    'inaccuracy': "Inaccuracy (?!)",
    'mistake': "Mistake (?)",
    'blunder': "Blunder (??)",
    'forced': "Forced",
    'theory': "Theory"
}

# --- CLASSIFICATION CONSTANTS ---
SACRIFICE_MIN_VALUE = 100
BRILLIANT_MAX_LOSS = 150
GREAT_MOVE_GAP = 50
GREAT_MOVE_ADVANTAGE = 100
GREAT_MOVE_TACTICAL_ADVANTAGE = 150
GREAT_MOVE_LOSS_THRESHOLD = 30
CRITICAL_THRESHOLD = 100
ALTERNATIVE_BAD_THRESHOLD = -100
CRITICAL_EVAL_THRESHOLD = 700

# --- ACCURACY CONSTANTS ---
WINNING_CHANCES_MATE_THRESHOLD = 32000
WINNING_CHANCES_MULTIPLIER = -0.00368208
ACCURACY_FORMULA_A = 103.1668100711649
ACCURACY_FORMULA_B = -0.04354415386753951
ACCURACY_FORMULA_C = -3.166924740191411
VOLATILITY_MAX_WEIGHT = 12
VOLATILITY_MIN_WEIGHT = 0.5
VOLATILITY_WINDOW_SIZE = 2

# --- CONVERSION CONSTANTS ---
MATE_VALUE_BASE = 30000
MATE_VALUE_DECREMENT = 100
