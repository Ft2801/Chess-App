import chess
from typing import Dict, Any, List, Optional
from src.analysis.analysis_config import CLASSIFICATION_THRESHOLDS, Classification
from src.analysis.expected_points import get_expected_points_loss
from src.analysis.opening_book import get_opening_name
from src.analysis.brilliant_moves import consider_brilliant_classification
from src.analysis.critical_moves import consider_critical_classification

class AdvancedMoveClassifier:
    def __init__(self):
        pass

    def classify_move(self, board_before: chess.Board, move: chess.Move, 
                     top_moves: Dict[int, Any]) -> str:
        """
        Classify move using wintrchess logic.
        """
        # Data preparation
        best_eval_info = top_moves.get(1)
        if not best_eval_info:
            return Classification.BOOK # Fallback
            
        # Find played move eval
        played_eval_info = None
        for rank, info in top_moves.items():
            if info.get('pv_move') == move.uci():
                played_eval_info = info
                break
        
        # Helper to standardize eval
        def to_std_eval(info):
            if info.get('mate') is not None:
                return {'type': 'mate', 'value': info['mate']}
            return {'type': 'cp', 'value': info.get('cp', 0)}

        prev_eval = to_std_eval(best_eval_info) # Best move eval = Board eval
        
        if played_eval_info:
            curr_eval = to_std_eval(played_eval_info)
        else:
            # Missing eval for played move usually means it's bad (not in top k)
            # We can't do exp-points calc accurately without eval.
            # Assume Mistake/Blunder? 
            return Classification.MISTAKE

        # 1. Forced Check
        if board_before.legal_moves.count() <= 1:
            return Classification.FORCED
            
        # 2. Theory (Book) Check
        # TS: if (opts.includeTheory && getOpeningName(current.fen)) -> THEORY
        # We check if the resulting position is a known opening.
        board_after = board_before.copy()
        board_after.push(move)
        if get_opening_name(board_after.fen()):
             return Classification.BOOK
             
        # 3. Checkmate (Best) Check
        if board_after.is_checkmate():
            return Classification.BEST
            
        top_move_played = (move.uci() == best_eval_info.get('pv_move'))
        
        # DEBUG: Uncomment to trace top move comparison
        print(f"DEBUG Classifier: move={move.uci()}, best_pv={best_eval_info.get('pv_move')}, top_move_played={top_move_played}, prev_eval={prev_eval}, curr_eval={curr_eval}")
        
        # 4. Point Loss Classification
        classification = Classification.BEST
        if top_move_played:
            classification = Classification.BEST
        else:
            classification = self._point_loss_classify(prev_eval, curr_eval, board_before.turn)
            
        # 5. Critical Check
        # Only if top move played
        if top_move_played:
            second_best_info = top_moves.get(2)
            second_eval = to_std_eval(second_best_info) if second_best_info else None
            
            # DEBUG: Uncomment to trace Critical logic
            print(f"  DEBUG Critical: second_best_info={second_best_info}, second_eval={second_eval}")
            
            is_critical = consider_critical_classification(
                board_before, move, prev_eval, curr_eval, second_eval
            )
            print(f"  DEBUG Critical: is_critical={is_critical}")
            if is_critical:
                classification = Classification.CRITICAL
                # Don't return early - need to check for Brilliant too!
        
        # 6. Brilliant Check
        # Only if Best or Critical (classifValues >= BEST)
        # Brilliant can upgrade even a Critical move
        
        if classification in [Classification.BEST, Classification.CRITICAL]:
            print(f"  DEBUG Brilliant: Checking for classification={classification}")
            is_brilliant = consider_brilliant_classification(board_before, move, prev_eval, curr_eval)
            print(f"  DEBUG Brilliant: is_brilliant={is_brilliant}")
            if is_brilliant:
                 return Classification.BRILLIANT
                  
        return classification

    def _point_loss_classify(self, prev_eval, curr_eval, color) -> str:
        """
        Matches pointLoss.ts with improved BLUNDER logic.
        BLUNDER only if resulting position is equal/losing.
        """
        p_type = prev_eval['type']
        c_type = curr_eval['type']
        
        # Convert to subjective (from player's perspective)
        from src.analysis.critical_moves import to_subjective_eval
        subj_curr = to_subjective_eval(curr_eval, color)
        subj_prev = to_subjective_eval(prev_eval, color)
        
        subj_curr_val = subj_curr.get('value', 0)
        subj_prev_val = subj_prev.get('value', 0)
        
        # Mate to mate evaluations
        if p_type == 'mate' and c_type == 'mate':
            # Winning mate to losing mate
            if subj_prev_val > 0 and subj_curr_val < 0:
                return Classification.BLUNDER if subj_curr_val >= -3 else Classification.MISTAKE
            # Delaying mate (bad) or keeping it (good)
            return Classification.BEST
              
        # Mate to CP (losing mate advantage)
        if p_type == 'mate' and c_type == 'cp':
            if subj_curr_val >= 800:
                return Classification.EXCELLENT
            elif subj_curr_val >= 400:
                return Classification.OKAY
            elif subj_curr_val >= 200:
                return Classification.INACCURACY
            elif subj_curr_val >= 0:
                return Classification.MISTAKE
            else:
                return Classification.BLUNDER
                
        # CP to Mate (finding mate or getting mated)
        if p_type == 'cp' and c_type == 'mate':
            if subj_curr_val > 0:  # Found a mate!
                return Classification.BEST
            elif subj_curr_val >= -2:
                return Classification.BLUNDER  # Got mated quickly
            elif subj_curr_val >= -5:
                return Classification.MISTAKE
            else:
                return Classification.INACCURACY
              
        # CP to CP: Use expected points loss
        loss = get_expected_points_loss(prev_eval, curr_eval, color)
        
        # Determine base classification from loss
        if loss < 0.01:
            classification = Classification.BEST
        elif loss < 0.045:
            classification = Classification.EXCELLENT
        elif loss < 0.08:
            classification = Classification.OKAY
        elif loss < 0.12:
            classification = Classification.INACCURACY
        elif loss < 0.22:
            classification = Classification.MISTAKE
        else:
            classification = Classification.BLUNDER
            
        # IMPROVEMENT: Cap classification based on resulting position
        # If still clearly winning (>= +200), BLUNDER becomes MISTAKE at most
        # If still ahead (>= +50), cap at INACCURACY
        if classification == Classification.BLUNDER:
            if subj_curr_val >= 200:
                # Still clearly winning, not a "blunder" - just a mistake
                classification = Classification.MISTAKE
            elif subj_curr_val >= 50:
                # Still slightly ahead
                classification = Classification.MISTAKE
            # If equal or losing (< +50), keep BLUNDER
            
        return classification

