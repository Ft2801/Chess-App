# move_classifier.py
import chess
from typing import Dict, Any, List, Optional
from src.analysis.analysis_config import (
    PIECE_VALUES, SACRIFICE_MIN_VALUE, BRILLIANT_MAX_LOSS,
    GREAT_MOVE_GAP, GREAT_MOVE_ADVANTAGE, GREAT_MOVE_TACTICAL_ADVANTAGE,
    GREAT_MOVE_LOSS_THRESHOLD, CRITICAL_THRESHOLD, ALTERNATIVE_BAD_THRESHOLD,
    EVAL_CLASSIFICATIONS
)
from src.analysis.piece_safety import is_piece_safe
from src.analysis.critical_moves import is_move_critical_candidate
from src.analysis.accuracy_calculator import winning_chances_percent

class AdvancedMoveClassifier:
    def __init__(self):
        pass

    def classify_move(self, board_before: chess.Board, move: chess.Move, 
                     top_moves: Dict[int, Any]) -> str:
        """
        Classify move using top_moves dict (keyed by MultiPV rank 1, 2, 3...)
        Expects top_moves[1] to be the Best Move.
        """
        # Critical: Forced Move Check
        if board_before.legal_moves.count() == 1:
            return "forced"

        if not top_moves or 1 not in top_moves:
            return "book" 
            
        best_eval = top_moves[1]
        played_uci = move.uci()
        best_uci = best_eval.get('pv_move', '')
        
        # 1. Player found Best Move
        if played_uci == best_uci:
            # Brilliant: Sacrifice leading to advantage
            if self._is_sacrifice(board_before, move):
                return "brilliant"
            
            # Great: Unique good move (others are bad)
            # We need MultiPV to be > 1 to judge this.
            if len(top_moves) > 1 and 2 in top_moves:
                second_best = top_moves[2]
                cp1 = best_eval.get('cp', 0)
                cp2 = second_best.get('cp', 0)
                
                # If White to move, Best is High. Second Best is Low. Diff = cp1 - cp2.
                # If Black to move, Best is Low. Second Best is High. Diff = cp2 - cp1.
                diff = 0
                if board_before.turn == chess.WHITE:
                    diff = cp1 - cp2
                else:
                    diff = cp2 - cp1 # e.g. -50 - (-200) = 150
                    
                if diff > 150: # Configurable threshold (GREAT_MOVE_GAP)
                    return "great"
                    
            return "best"
        
        # 2. Player played sub-optimal
        played_eval = None
        for rank, info in top_moves.items():
            if info.get('pv_move') == played_uci:
                played_eval = info
                break
        
        # If we have info for the played move (because it was in top_moves)
        if played_eval:
             best_cp = best_eval.get('cp', 0)
             played_cp = played_eval.get('cp', 0)
             
             turn = board_before.turn
             if turn == chess.WHITE:
                 loss = best_cp - played_cp
             else:
                 loss = played_cp - best_cp
             
             return self.classify_from_loss(max(0, loss))

        # Fallback if played move wasn't in MultiPV but looks like it loses a lot?
        # Without exact eval, we can't be sure, but it wasn't valid enough to be in top X.
        # Assume innacuracy
        return "inaccuracy"

    def classify_from_loss(self, loss: int) -> str:
        if loss <= 20: return "excellent"
        if loss <= 50: return "good"
        if loss <= 100: return "inaccuracy"
        if loss <= 300: return "mistake"
        return "blunder"

    def _is_sacrifice(self, board: chess.Board, move: chess.Move) -> bool:
        """
        Check if move is a sacrifice (giving up material for positional gain).
        Simplified check: Piece moves to square where it can be taken by less valuable piece,
        OR piece captures less valuable piece while being taken.
        """
        moved_piece = board.piece_at(move.from_square)
        if not moved_piece: return False
        
        # 1. Capture Check (Exchange is not sacrifice)
        captured_piece = board.piece_at(move.to_square)
        moved_val = PIECE_VALUES.get(moved_piece.piece_type, 0)
        
        # If we capture something more valuable, unlikely a sacrifice (unless we lose queen for rook)
        if captured_piece:
             cap_val = PIECE_VALUES.get(captured_piece.piece_type, 0)
             if cap_val >= moved_val: return False 
        
        # 2. Check if we are moving into danger (Defended square)
        # Simulate move
        board.push(move)
        attackers = board.attackers(not moved_piece.color, move.to_square)
        
        is_sac = False
        if attackers:
            # We moved into fire.
            # Are we defended?
            # Even if defended, if we lose Q for N, it's a sac.
            
            # Lowest value attacker
            min_attacker_val = 9999
            for sq in attackers:
                p = board.piece_at(sq)
                if p:
                    v = PIECE_VALUES.get(p.piece_type, 0)
                    min_attacker_val = min(min_attacker_val, v)
            
            # If we are attacked by something cheaper than us -> Sacrifice risk
            if min_attacker_val < moved_val:
                is_sac = True
                
        board.pop()
        return is_sac
