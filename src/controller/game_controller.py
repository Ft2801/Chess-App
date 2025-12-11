import chess
import chess.pgn
from PyQt6.QtCore import QObject, QTimer, pyqtSlot, Qt
from PyQt6.QtWidgets import QInputDialog

from src.model.chess_model import ChessModel
from src.model.engine_thread import EngineThread
from src.view.main_window import MainWindow
from src.analysis.move_classifier import AdvancedMoveClassifier

class GameController(QObject):
    def __init__(self):
        super().__init__()
        self.model = ChessModel()
        self.view = MainWindow()
        
        # Engine
        self.engine = EngineThread()
        self.engine.start_engine()
        
        # Game State
        self.mode = "PvP" # PvP, PvE, EvE
        self.player_color = chess.WHITE # for PvE
        self.engine_level = 1
        self.seeking_move = False # Flag: are we waiting for a move to play?
        self.is_analyzing_only = False # Flag: just updating arrow/eval
        
        # EvE State
        self.eve_paused = False
        self.eve_timer = QTimer()
        self.eve_timer.timeout.connect(self.make_engine_move)
        
        # History State
        self.history_index = None
        self.auto_rotate = False
        
        # Post-Game Analysis State
        self.classifier = AdvancedMoveClassifier()
        self.analysis_results = {} # { move_index (int): classification_type (str) }
        self.is_analyzing_game = False
        self.analysis_index = 0
        self.current_analysis_board = None
        
        # Connect Signals
        self.connect_signals()
        
        # Start at Menu
        self.view.show_menu()
        self.view.show()
        
        # Initial Analysis
        if not self.model.is_game_over():
             self.analyze_position()

    def connect_signals(self):
        # View -> Controller
        self.view.board_widget.move_made.connect(self.handle_human_move)
        
        # Info Panel Control
        self.view.info_panel.undo_clicked.connect(self.undo_move)
        self.view.info_panel.flip_clicked.connect(self.flip_board)
        self.view.info_panel.theme_clicked.connect(self.select_theme)
        self.view.info_panel.pause_clicked.connect(self.toggle_pause)
        self.view.info_panel.back_clicked.connect(self.view.show_menu)
        
        # Signals
        self.view.info_panel.exit_analysis_clicked.connect(self.exit_post_game_analysis)
        
        # Direct Connection (Fixing missing signal emission)
        self.view.info_panel.btn_analyze.clicked.connect(self.start_post_game_analysis)
        
        self.view.info_panel.start_clicked.connect(lambda: self.navigate_history("start"))
        self.view.info_panel.prev_clicked.connect(lambda: self.navigate_history("prev"))
        self.view.info_panel.next_clicked.connect(lambda: self.navigate_history("next"))
        self.view.info_panel.end_clicked.connect(lambda: self.navigate_history("end"))
        
        # Toggles
        self.view.info_panel.toggle_eval_clicked.connect(self.view.eval_bar.setVisible)
        self.view.info_panel.toggle_arrows_clicked.connect(self.toggle_arrows)
        self.view.info_panel.toggle_auto_rotate_clicked.connect(self.toggle_auto_rotate)

        # Main Menu Actions
        self.view.main_menu.pvp_clicked.connect(lambda: self.start_new_game("PvP"))
        self.view.main_menu.pve_clicked.connect(self.start_pve_game)
        self.view.main_menu.eve_clicked.connect(self.start_eve_game)
        
        # Engine -> Controller
        self.engine.best_move_found.connect(self.handle_engine_move)
        self.engine.eval_updated.connect(self.handle_eval_update)
        self.engine.analysis_complete.connect(self.handle_analysis_complete)

    @pyqtSlot(str, str)
    def handle_eval_update(self, score, pv_move):
        # Normalize Score to White's Perspective
        # Stockfish returns score for "Side to Move".
        # We want "Positive = White Adv, Negative = Black Adv".
        # So if Side to Move is Black, we negate the score.
        
        normalized_score = score
        try:
            is_black_turn = (self.model.get_turn() == chess.BLACK)
            
            if score.startswith("#"):
                # Mate
                # "#3" (Mate in 3 for side to play)
                # If Black to play and "#3" -> Black wins in 3.
                # White perspective: Black winning is Negative. -> "#-3"
                val = int(score.replace("#", ""))
                if is_black_turn:
                    val = -val
                normalized_score = f"#{val}"
            else:
                # CP
                # "+1.5" (Side to play is up 1.5)
                # If Black to play and "+1.5" -> Black is up.
                # White perspective: -1.5.
                val = float(score)
                if is_black_turn:
                    val = -val
                normalized_score = f"{val:+.2f}"
        except ValueError:
            pass

        # Update Eval Bar & Label
        if normalized_score:
            self.view.eval_bar.set_eval(normalized_score)
            self.view.info_panel.update_eval(normalized_score, pv_move) 
            
        # Update Arrow (Live!)
        if pv_move and not self.is_analyzing_game: # Block arrows during full analysis
            try:
                move = chess.Move.from_uci(pv_move)
                self.view.board_widget.set_best_move(move)
            except ValueError:
                pass

    def start_new_game(self, mode):
        self.view.show_game()
        self.mode = mode
        self.model.reset_game()
        self.eve_timer.stop()
        self.eve_paused = False
        self.engine.stop_search() 
        
        self.view.info_panel.btn_pause.setChecked(False)
        self.view.info_panel.btn_pause.setVisible(False) # Default hidden
        self.seeking_move = False
        self.is_analyzing_only = False
        self.history_index = None
        self.analysis_results = {} # Clear previous analysis
        
        # Reset View
        self.view.board_widget.set_flipped(False)
        self.update_view()
        self.view.info_panel.set_status(f"Mode: {mode}")
        
        # Analyze initial position
        QTimer.singleShot(200, self.analyze_position)

    def start_pve_game(self, color_str, level):
        self.start_new_game("PvE")
        
        if color_str == "White":
            self.player_color = chess.WHITE
            self.view.board_widget.set_flipped(False)
        else:
            self.player_color = chess.BLACK
            self.view.board_widget.set_flipped(True)
            self.view.info_panel.chk_auto_rotate.setChecked(False)
        
        self.engine_level = level
        self.engine.set_difficulty(level)
        
        if self.player_color == chess.BLACK:
             # Start engine immediately so eval updates
             self.make_engine_move()

    def start_eve_game(self, white_level, black_level):
        self.start_new_game("EvE")
        self.eve_level_white = white_level
        self.eve_level_white = white_level
        self.eve_level_black = black_level
        self.engine.set_difficulty(white_level)
        
        self.view.info_panel.btn_pause.setVisible(True) # Show for EvE
        self.eve_timer.start(2000) 
        self.make_engine_move()

    def update_view(self):
        # Handle history view
        board_to_show = self.model.board
        
        if self.history_index is not None:
            board_to_show = chess.Board()
            stack = self.model.board.move_stack
            limit = min(len(stack), self.history_index)
            for i in range(limit):
                board_to_show.push(stack[i])
        
        # Update Board & Annotations
        self.update_board_visuals(board_to_show)
        
        # Update Move List
        self.view.info_panel.update_moves(str(chess.pgn.Game.from_board(self.model.board).mainline_moves()))

        # Status update & Game Over Check
        if self.model.is_game_over():
             self.view.info_panel.set_status(f"Game Over: {self.model.get_outcome().result()}")
             self.view.info_panel.btn_analyze.setVisible(True)
        else:
             self.view.info_panel.btn_analyze.setVisible(False)
        
        # Auto-Rotate
        if self.mode == "PvP" and self.auto_rotate and self.history_index is None:
             self.view.board_widget.set_flipped(board_to_show.turn == chess.BLACK)

    def handle_human_move(self, move):
        if self.history_index is not None:
             return 

        if self.mode == "EvE": return
        if self.mode == "PvE" and self.model.get_turn() != self.player_color: return

        if self.model.make_move(move):
            self.history_index = None # Snap to live
            self.is_analyzing_only = False
            self.seeking_move = False
            self.update_view()
            
            if self.mode == "PvP":
                self.analyze_position()
            elif self.mode == "PvE":
                # Start engine immediately so eval updates
                self.make_engine_move()

    def make_engine_move(self):
        if self.model.is_game_over() or self.eve_paused:
            if self.model.is_game_over(): self.eve_timer.stop()
            return
            
        if self.mode == "EvE":
            if self.model.get_turn() == chess.WHITE:
                self.engine.set_difficulty(getattr(self, 'eve_level_white', 8))
            else:
                self.engine.set_difficulty(getattr(self, 'eve_level_black', 8))
        elif self.mode == "PvE":
            # Ensure difficulty is reset to user setting, 
            # because analyze_position sets it to Max (20).
            self.engine.set_difficulty(self.engine_level)
        
        self.engine.set_position(self.model.get_fen())
        self.seeking_move = True
        self.is_analyzing_only = False 
        
        import time
        self.engine_start_time = time.time()
        self.engine.go() 

    @pyqtSlot(str)
    def handle_engine_move(self, best_move_str):
        if not self.seeking_move:
             return
        
        self.seeking_move = False
        try:
            move = chess.Move.from_uci(best_move_str)
            
            if self.is_analyzing_only:
                self.is_analyzing_only = False 
                return 
            
            # Real Move found.
            import time
            elapsed = (time.time() - getattr(self, 'engine_start_time', 0)) * 1000 # ms
            delay = max(0, 1000 - int(elapsed))
            
            if delay > 0:
                 QTimer.singleShot(delay, lambda: self.finish_engine_move(move))
            else:
                 self.finish_engine_move(move)

        except ValueError:
            pass
            
    def finish_engine_move(self, move):
        if self.model.make_move(move):
            self.update_view()
            if self.mode == "PvP":
                self.analyze_position()
            elif self.mode == "PvE":
                self.analyze_position()

    def analyze_position(self):
        if not self.model.is_game_over():
             self.engine.stop_search() 
             self.engine.set_position(self.model.get_fen())
             self.seeking_move = True 
             self.is_analyzing_only = True 
             # Force Engine to Max Strength for Analysis
             # This ensures arrows/eval are accurate even if Bot is Level 1.
             self.engine.send_command("setoption name Skill Level value 20")
             self.engine.go(depth=14) 

    def navigate_history(self, direction):
        # Hide promotion dialog when navigating
        self.view.board_widget.hide_promotion_dialog()
        
        self.engine.stop_search() 
        self.seeking_move = False
        
        stack_len = len(self.model.board.move_stack)
        
        current = self.history_index if self.history_index is not None else stack_len
        
        if direction == "start": 
            current = 0
        elif direction == "prev": 
            current = max(0, current - 1)
        elif direction == "next": 
            current = min(stack_len, current + 1)
        elif direction == "end": 
            current = stack_len
            
        if current == stack_len:
            self.history_index = None
        else:
            self.history_index = current
            
        self.update_view()

    def undo_move(self):
        if self.mode == "EvE": return
        
        # Hide promotion dialog if visible
        self.view.board_widget.hide_promotion_dialog()
        
        # Stop Analysis if running
        if self.is_analyzing_game:
            self.is_analyzing_game = False
            self.view.info_panel.btn_analyze.setText("Analyze Game")
            self.view.info_panel.btn_analyze.setEnabled(True)
            self.view.info_panel.set_status("Analysis Cancelled")

        self.engine.stop_search() 
        self.seeking_move = False
        
        # Invalidate analysis results anyway since history changed
        self.analysis_results = {}
        self.history_index = None # Snap to live
        
        if self.mode == "PvE":
             if self.model.get_turn() == self.player_color:
                 self.model.undo_move(); self.model.undo_move()
             else:
                 self.model.undo_move()
        else:
             self.model.undo_move()
             
        self.update_view()
        
        # If game not over, analyze live
        if not self.model.is_game_over():
            self.analyze_position()

    def toggle_arrows(self, checked):
        self.view.board_widget.show_arrows = checked
        self.view.board_widget.update()

    def toggle_auto_rotate(self, checked):
        self.auto_rotate = checked
        self.update_view()

    def flip_board(self):
        flipped = not self.view.board_widget.flipped
        self.view.board_widget.set_flipped(flipped)
        # Update captured pieces widget to reflect the flip
        self.view.captured_pieces_top.set_board_flipped(flipped)
        self.view.captured_pieces_bottom.set_board_flipped(flipped)
        self.update_board_visuals()

    def start_post_game_analysis(self):
        from PyQt6.QtWidgets import QMessageBox
        # Debugging: Confirm click
        # QMessageBox.information(self.view, "Analysis", "Starting Analysis...")
        print(f"DEBUG: Start Analysis triggered. History len: {len(self.model.move_history)}")
        
        if not self.model.move_history:
             QMessageBox.warning(self.view, "Analysis", "No game history to analyze!")
             print("DEBUG: No history.")
             return
            
        self.is_analyzing_game = True
        self.analysis_results = {}
        self.analysis_index = 0
        
        # UI Feedback
        self.view.info_panel.btn_analyze.setEnabled(False)
        self.view.info_panel.btn_analyze.setText("Analyzing...")
        self.view.info_panel.set_status("Analyzing game...")
        
        # Stop any background analysis
        self.engine.stop_search()
        self.seeking_move = False
        self.is_analyzing_only = False
        
        # Clear outdated visuals
        self.view.board_widget.set_best_move(None)
        self.view.board_widget.set_annotation(None)
        
        # Start Loop
        # Small delay to ensure engine stopped?
        QTimer.singleShot(100, self.analyze_next_step)

    def analyze_next_step(self):
        print(f"DEBUG: Analyzing step {self.analysis_index}")
        # Check if done
        # We need to go up to index == len(history) (State after last move)
        if self.analysis_index > len(self.model.move_history):
            self.finish_analysis()
            return

        # Update progress text
        self.view.info_panel.btn_analyze.setText(f"Analyzing {self.analysis_index + 1}/{len(self.model.move_history) + 1}")
        
        # Get board state BEFORE the move (Wait, Board State FOR step i)
        # Step i corresponds to board *after* i moves.
        # i=0: Start. i=N: End.
        board = chess.Board()
        for i in range(self.analysis_index):
            board.push(self.model.move_history[i])
            
        self.current_analysis_board = board 
        
        # Send position to engine
        self.engine.set_position(board.fen())
        
        # Start Analysis
        self.engine.go(depth=16) 
        
        # Safety Timeout: If engine hangs for > 10 seconds, force next step
        QTimer.singleShot(10000, lambda: self.force_next_analysis_step(self.analysis_index))

    def force_next_analysis_step(self, expected_index):
        if self.is_analyzing_game and self.analysis_index == expected_index:
            # Verify engine is running, maybe restart it? 
            # For now, just pretend we got empty results
            self.handle_analysis_complete({}) 

    def handle_analysis_complete(self, pvs):
        """
        Called when engine finishes analyzing a step during Post-Game Analysis.
        """
        if not self.is_analyzing_game:
            return
            
        try:
            # Extract Score / Best Move / Second Best Score
            cp = 0.0
            best_move_uci = ""
            second_best_cp = None
            
            if pvs:
                # Top Move
                if 1 in pvs:
                    info = pvs[1]
                    if info.get('mate') is not None:
                        m = info['mate']
                        # Normalized Mate Score (High value) - preserve sign later
                        if m > 0: cp = 30000 - (m * 100)
                        else: cp = -30000 - (m * 100)
                    else:
                        cp = info.get('cp', 0)
                    best_move_uci = info.get('pv_move', '')
                
                # Second Best (for Great Move detection)
                if 2 in pvs:
                    info2 = pvs[2]
                    if info2.get('mate') is None:
                        second_best_cp = info2.get('cp', 0)
            
            # NORMALIZE to White Perspective
            # analysis_index 0 = Start (White to move). cp is White's eval.
            # analysis_index 1 = After White Move (Black to move). cp is Black's eval.
            is_white_turn = (self.analysis_index % 2 == 0)
            white_cp = cp if is_white_turn else -cp
            
            # Store data for Current State
            self.analysis_results[self.analysis_index] = {
                'cp': white_cp, # Store ALWAYS as White Perspective
                'best_move': best_move_uci,
                'second_best_cp': second_best_cp, # Note: this is raw side-to-move, careful
                'is_white_turn': is_white_turn,
                'type': 'pending' 
            }
            
            # --- DELAYED CLASSIFICATION (Classify Move index-1) ---
            if self.analysis_index > 0:
                prev_idx = self.analysis_index - 1
                prev_data = self.analysis_results[prev_idx]
                
                # Identify Move Played
                played_move_obj = self.model.move_history[prev_idx]
                played_uci = played_move_obj.uci()
                
                # Reconstruct Board State BEFORE the move
                prev_board = chess.Board()
                for i in range(prev_idx):
                    prev_board.push(self.model.move_history[i])
                    
                # 1. Check Forced
                if prev_board.legal_moves.count() == 1:
                    prev_data['type'] = 'forced'
                
                # 2. Check Best Move
                elif played_uci == prev_data['best_move']:
                    # Check Sacrifice (Brilliant)
                    if self.classifier._is_sacrifice(prev_board, played_move_obj):
                         prev_data['type'] = 'brilliant'
                    # Check Great (Unique good move)
                    elif prev_data.get('second_best_cp') is not None:
                         # Use Side-Specific Logic for Raw CP comparison or Normalized?
                         # prev_data['cp'] is WHITE perspective.
                         # prev_data['second_best_cp'] is RAW side-to-move perspective (from prev step logic).
                         # WAIT. We didn't normalize second_best_cp in storage above.
                         # Let's re-extract raw best CP for diff calculation.
                         # If prev_data['is_white_turn']: raw_best = prev_data['cp']
                         # Else: raw_best = -prev_data['cp']
                         
                         raw_best = prev_data['cp'] if prev_data['is_white_turn'] else -prev_data['cp']
                         raw_second = prev_data['second_best_cp']
                         
                         diff = raw_best - raw_second # Side-to-move perspective: Best is always higher.
                         
                         if diff > 150:
                             prev_data['type'] = 'great'
                         else:
                             prev_data['type'] = 'best'
                    else:
                         prev_data['type'] = 'best'
                else:
                    # 3. Calculate Loss from Sub-optimal move
                    # prev_cp is White Persp (Before Move)
                    # current cp (white_cp) is White Persp (After Move)
                    # We need Loss from Side-To-Move perspective.
                    
                    if prev_data['is_white_turn']: # White Moved
                        # Expected (Best): prev_cp
                        # Actual (Played): white_cp (Eval of resulting pos)
                        # Wait, Eval of resulting pos is same frame of reference (White Persp).
                        # Loss = Best - Actual
                        loss = prev_data['cp'] - white_cp
                    else: # Black Moved
                        # Black wants NEGATIVE White CP.
                        # Best for Black: prev_cp (Negative)
                        # Actual for Black: white_cp (from resulting pos)
                        # Loss = Actual - Best (since lower is better for Black)
                        loss = white_cp - prev_data['cp']

                    prev_data['type'] = self.classifier.classify_from_loss(max(0, int(loss)))
                
                # Update Storage
                self.analysis_results[prev_idx] = prev_data
            
            # Next Step
            self.analysis_index += 1
            self.analyze_next_step()
            
        except Exception as e:
            print(f"Error in Analysis Loop: {e}")
            self.view.info_panel.set_status(f"Error: {str(e)}")
            self.finish_analysis()

    def finish_analysis(self):
        from src.analysis.accuracy_calculator import winning_chances_percent, move_accuracy_percent
        import chess
        
        self.is_analyzing_game = False
        self.view.info_panel.btn_analyze.setText("Analyze Game") 
        self.view.info_panel.btn_analyze.setEnabled(True)
        self.view.info_panel.set_status("Analysis Complete")
        
        # Calculate Stats & Accuracy
        counts = {}
        white_acc_sum = 0
        white_moves = 0
        black_acc_sum = 0
        black_moves = 0
        
        # We need an initial evaluation for the start of the game (0.0 usually)
        prev_cp = 0.0 # Start position
        
        # Only iterate up to the number of actual moves played
        # analysis_results contains N+1 entries (0 to N). Entry N is the final position eval.
        for idx in range(len(self.model.move_history)):
            if idx not in self.analysis_results:
                continue
                
            data = self.analysis_results[idx]
            if data['type'] == 'pending':
                data['type'] = 'excellent' # Assume innocence
                
            classification = data['type']
            
            # 1. Counts
            counts[classification] = counts.get(classification, 0) + 1
            
            # 2. Accuracy
            current_cp = data['cp'] # This is eval from Engine side (Side to move)
            
            # Win chances before move (previous position eval)
            # Note: stored 'cp' is from perspective of side to move at that step.
            # So prev_cp (from step i-1) was for Opponent.
            # We need to flip prev_cp to current side's perspective.
            
            if idx == 0:
                win_before = winning_chances_percent(0) # Standard start
            else:
                # Previous step stored eval for Opponent.
                # So for us, it is -prev_cp.
                # BUT wait. `finish_analysis` loop:
                # Let's say White moves (idx 0). Engine says +50 (White adv).
                # Next Black moves (idx 1). Engine says -50 (Black disadv, i.e. White +50).
                # Accuracy is how much did we drop from Best Eval?
                pass

            # SIMPLIFIED ACCURACY:
            # We reuse the logic that 'Accuracy' is determined by how close we are to Best Move.
            # If classification is 'best'/'great'/'brilliant' -> 100%.
            # 'excellent' -> 95%.
            # 'good' -> 80%.
            # 'inaccuracy' -> 60%.
            # 'mistake' -> 30%.
            # 'blunder' -> 0%.
            # This is robust and consistent with labels without fragile CP math.
            
            acc_map = {
                'brilliant': 100, 'great': 100, 'best': 100, 'book': 100,
                'excellent': 98, 'good': 90, 'inaccuracy': 60, 'mistake': 30, 'blunder': 0, 'forced': 100
            }
            score = acc_map.get(classification, 90)
            
            is_white = (idx % 2 == 0) # 0 is White's first move
            if is_white:
                white_acc_sum += score
                white_moves += 1
            else:
                black_acc_sum += score
                black_moves += 1

        accuracy = {
            'white': (white_acc_sum / white_moves) if white_moves > 0 else 0,
            'black': (black_acc_sum / black_moves) if black_moves > 0 else 0
        }
        
        # Switch to New Interface
        self.view.info_panel.show_analysis()
        self.view.info_panel.analysis_dashboard.update_stats(counts, accuracy)
        
        # Refresh board
        self.update_board_visuals()

    def exit_post_game_analysis(self):
        self.view.info_panel.show_game()
        # User requested explicit reset of analysis artifacts when closing
        self.analysis_results = {} 
        self.view.board_widget.set_annotation(None)
        self.view.board_widget.set_best_move(None)
        self.update_board_visuals()

    def update_board_visuals(self, board_to_show=None):
        if board_to_show is None:
            # Determine which board we are showing
            if self.history_index is not None:
                board_to_show = chess.Board()
                for i in range(self.history_index):
                    board_to_show.push(self.model.move_history[i])
            else:
                board_to_show = self.model.board

        # 1. Sync Board Widget pieces
        self.view.board_widget.update_board(board_to_show)
        
        # 2. Update Captured Pieces Display
        self.view.captured_pieces_top.update_captured_pieces(board_to_show)
        self.view.captured_pieces_bottom.update_captured_pieces(board_to_show)
        
        # 3. Analysis Overlays (Eval, Arrow, Annotation)
        current_idx = self.history_index if self.history_index is not None else len(self.model.move_history)
        
        # Clear defaults
        self.view.board_widget.set_annotation(None)
        self.view.board_widget.set_best_move(None)
        
        if current_idx in self.analysis_results:
            data = self.analysis_results[current_idx]
            
            # A. Update Eval Bar (Using Normalized CP)
            try:
                cp = data['cp']
                score_str = ""
                # MATE DETECTION
                # CP > 20000 means White winning. < -20000 means Black winning.
                if abs(cp) > 20000:
                    mate_dist = (30000 - abs(cp)) / 100
                    # If CP positive -> +M3. If negative -> -M3.
                    sign = "+" if cp > 0 else "-"
                    score_str = f"{sign}M{int(mate_dist)}"
                else:
                    # Normal CP
                    sign = "+" if cp > 0 else ""
                    score_str = f"{sign}{cp/100:.2f}"
                    
                # Direct Update - Bypass handle_eval_update to avoid re-normalization errors
                self.view.eval_bar.set_eval(score_str)
                self.view.info_panel.update_eval(score_str, "")
            except: pass
            
            # B. Best Move Arrow
            if data['best_move']:
                try:
                    move = chess.Move.from_uci(data['best_move'])
                    self.view.board_widget.set_best_move(move)
                except: pass
                
        # C. Annotation for Last Played Move (The move that created this position)
        if current_idx > 0:
            last_move_idx = current_idx - 1
            if last_move_idx in self.analysis_results:
                data = self.analysis_results[last_move_idx]
                annot_type = data['type'] if isinstance(data, dict) else data
                
                if annot_type != 'pending':
                    move = self.model.move_history[last_move_idx]
                    self.view.board_widget.set_annotation({
                        'square': move.to_square,
                        'type': annot_type
                    })

    def select_theme(self):
        from src.utils.styles import Styles
        themes = list(Styles.THEMES.keys())
        current = self.view.board_widget.theme_name
        try:
             current_idx = themes.index(current)
        except ValueError:
             current_idx = 0
             
        # Import internally or ensure top-level import covers it. 
        # Styles is needed. I'll use strings hardcoded or cleaner import.
        # Actually, let's just use the strings, or better, import Styles properly.
        from src.utils.styles import Styles
        themes = list(Styles.THEMES.keys())
        
        item, ok = QInputDialog.getItem(self.view, "Select Theme", "Choose Board Theme:", themes, current_idx, False)
        
        if ok and item:
            self.view.board_widget.set_theme(item)

    def toggle_pause(self):
        self.eve_paused = not self.eve_paused
        self.view.info_panel.set_status("Paused" if self.eve_paused else "Running")
        if not self.eve_paused and self.mode == "EvE":
             self.make_engine_move()

    def close(self):
        self.engine.stop_engine()
