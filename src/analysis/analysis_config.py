class Classification:
    BRILLIANT = "brilliant"
    CRITICAL = "critical" # great/best
    BEST = "best"
    EXCELLENT = "excellent"
    OKAY = "good" # Use "good" or "okay"? TS uses "okay". App might use "good".
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"
    BOOK = "theory"
    FORCED = "forced"
    
CLASSIFICATION_THRESHOLDS = {
    "best": 0.01,
    "excellent": 0.045,
    "good": 0.08,
    "inaccuracy": 0.12,
    "mistake": 0.22,
    "blunder": float('inf')
}

PIECE_VALUES = {
    1: 1,    # Pawn
    2: 3,    # Knight
    3: 3,    # Bishop
    4: 5,    # Rook
    5: 9,    # Queen
    6: float('inf') # King
}
