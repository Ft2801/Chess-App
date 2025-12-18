# report.py
# Game Analysis Report Generation
# Matches wintrchess/shared/src/lib/reporter/report.ts

import chess
from typing import Dict, Any, List, Optional
from src.analysis.move_classifier import AdvancedMoveClassifier
from src.analysis.opening_book import get_opening_name
from src.analysis.accuracy_calculator import get_move_accuracy, get_game_accuracy

class GameReport:
    def __init__(self):
        self.classifier = AdvancedMoveClassifier()
        
    def analyze_game(self, moves_with_evals: List[Dict[str, Any]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a full game and generate a report.
        
        moves_with_evals: List of dicts, each containing:
            - 'fen_before': FEN string before the move
            - 'move_uci': UCI string of move played
            - 'top_moves': Dict[int, Any] from engine (rank -> info)
            
        Returns:
            Dict containing classifications, accuracies, opening info per move, 
            and overall game accuracy.
        """
        opts = options or {}
        
        analyzed_moves = []
        white_accuracies = []
        black_accuracies = []
        
        for move_data in moves_with_evals:
            fen_before = move_data.get('fen_before')
            move_uci = move_data.get('move_uci')
            top_moves = move_data.get('top_moves', {})
            
            board = chess.Board(fen_before)
            move = chess.Move.from_uci(move_uci)
            
            # 1. Classification
            classification = self.classifier.classify_move(board, move, top_moves)
            
            # 2. Opening Name
            board_after = board.copy()
            board_after.push(move)
            opening = get_opening_name(board_after.fen())
            
            # 3. Accuracy
            # We need prev_eval and curr_eval in standard format.
            def to_std_eval(info):
                if not info: return {'type': 'cp', 'value': 0}
                if info.get('mate') is not None:
                    return {'type': 'mate', 'value': info['mate']}
                return {'type': 'cp', 'value': info.get('cp', 0)}
            
            prev_eval = to_std_eval(top_moves.get(1))
            
            # Find curr_eval (eval for played move)
            curr_eval_info = None
            for rank, info in top_moves.items():
                if info.get('pv_move') == move_uci:
                    curr_eval_info = info
                    break
            curr_eval = to_std_eval(curr_eval_info) if curr_eval_info else prev_eval
            
            accuracy = get_move_accuracy(prev_eval, curr_eval, board.turn)
            
            # Track per-side accuracy
            if board.turn == chess.WHITE:
                white_accuracies.append(accuracy)
            else:
                black_accuracies.append(accuracy)
            
            analyzed_moves.append({
                'move': move_uci,
                'classification': classification,
                'opening': opening,
                'accuracy': accuracy
            })
            
        # 4. Game Accuracy
        game_accuracy = get_game_accuracy(white_accuracies, black_accuracies)
        
        return {
            'moves': analyzed_moves,
            'game_accuracy': game_accuracy
        }
