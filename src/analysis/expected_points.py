import math
import chess
from typing import Dict, Any, Optional

def get_expected_points(evaluation: Dict[str, Any], move_color: chess.Color, centipawn_gradient: float = 0.0035) -> float:
    """
    Calculate expected points (win probability) from an evaluation.
    evaluation: Dict with 'type' ('cp' or 'mate') and 'value'.
    move_color: Color of the side whose perspective we want (WHITE=True, BLACK=False).
    """
    if evaluation['type'] == 'mate':
        if evaluation['value'] == 0:
            return 1.0 if move_color == chess.WHITE else 0.0
        return 1.0 if evaluation['value'] > 0 else 0.0
    else:
        # Sigmoid function for centipawns
        # Note: 'value' is usually from white's perspective in many engines, 
        # but here we assume standard UCI convention: positive = good for side to move? 
        # actually, standard UCI 'score cp' is usually white-centric or side-to-move-centric depending on engine.
        # reporter/expectedPoints.ts uses simple formula implying 'value' is absolute (white-centric?) or adjusted?
        # looking at ts: return 1 / (1 + Math.exp(-opts.centipawnGradient * evaluation.value));
        # This implies 'value' is favorable if positive. 
        # We will assume 'value' is from white's perspective, so we need to negate if we want black's prob?
        # No, the sigmoid gives P(Win). If eval is +100 (white adv), 1/(1+exp(-0.35)) > 0.5.
        
        # If we just want the "score", we use the raw value.
        return 1.0 / (1.0 + math.exp(-centipawn_gradient * evaluation['value']))

def get_expected_points_loss(prev_eval: Dict[str, Any], curr_eval: Dict[str, Any], move_color: chess.Color) -> float:
    """
    Calculate loss in expected points.
    positive outcome means the move was worse than optimal (loss of potential points).
    """
    # Previous prob for the player who IS ABOUT TO MOVE (move_color).
    # wait, prev node: it was 'move_color's turn. 
    # reporter/expectedPoints.ts:
    # getExpectedPoints(previousEvaluation, { moveColour: flipPieceColour(moveColour) }) - ...
    # Wait, 'moveColour' in ts seems to be the color of the player who played the move in 'current'.
    # In 'previous', it was that player's turn? No. 
    # If I am White. Previous state: Black just moved. It is My (White) turn.
    # I play 'current' move.
    
    # Actually, let's look at `reporter/classification/pointLoss.ts`:
    # previousSubjectiveValue = previous.evaluation.value * ((current.playedMove.color == WHITE ? 1 : -1));
    # This implies evaluation.value is White-Centric.
    
    # In `getExpectedPointsLoss`:
    # getExpectedPoints(prev, { moveColour: flip(color) }) - getExpectedPoints(curr, { moveColour: color })
    # This is slightly confusing. Let's trace.
    # Player A makes move M.
    # Prev state: A's turn to move.
    # Curr state: B's turn to move (after M).
    
    # We want to measure how much A hurt their own chances.
    # A's winning chances BEFORE move (Position Eval) - A's winning chances AFTER move (New Position Eval).
    
    # ts: getExpectedPoints(prev, flip(color)) ... why flip?
    # Maybe 'prev' eval is from perspective of side to move?
    # If eval is always White-Centric:
    # P(White Win) = sigmoid(eval).
    # If I am White: Loss = P(White Win @ Prev) - P(White Win @ Curr).
    # If I am Black: Loss = P(Black Win @ Prev) - P(Black Win @ Curr).
    # P(Black Win) = 1 - P(White Win).
    
    # Let's trust the TS logic if we can map it.
    # The TS implementation of `getExpectedPoints` doesn't use `moveColour` unless it's Mate 0.
    # Otherwise it just does `1/(1+exp(-grad * eval))`.
    # This implies `eval` is White-Centric. +100 -> >50% win for White.
    
    # So if I am White:
    # Loss = Sigmoid(Prev) - Sigmoid(Curr).
    # If I am Black:
    # Loss = (1 - Sigmoid(Prev)) - (1 - Sigmoid(Curr)) 
    #      = -Sigmoid(Prev) + Sigmoid(Curr) 
    #      = -(Sigmoid(Prev) - Sigmoid(Curr))
    
    # TS `getExpectedPointsLoss`:
    # ( getExp(prev, flip(color)) - getExp(curr, color) ) * (color == WHITE ? 1 : -1)
    # This is weird. 
    # If color=WHITE (flip=BLACK):
    # ( getExp(prev) - getExp(curr) ) * 1.
    # Wait, the `moveColour` arg in `getExpectedPoints` is ONLY used for mate=0.
    
    # So effectively:
    # Loss = (Sigmoid(Prev) - Sigmoid(Curr)) * (1 if White else -1).
    # This matches my derivation above:
    # If White: Loss = Sigmoid(Prev) - Sigmoid(Curr)
    # If Black: Loss = (Sigmoid(Prev) - Sigmoid(Curr)) * -1
    
    prev_points = get_expected_points(prev_eval, not move_color) # color arg irrelevant unless mate=0
    curr_points = get_expected_points(curr_eval, move_color)
    
    diff = prev_points - curr_points
    
    return max(0.0, diff * (1 if move_color == chess.WHITE else -1))
