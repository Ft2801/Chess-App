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
        self.view.info_panel.resign_clicked.connect(self.handle_resign)
        
        # Direct Connection (Fixing missing signal emission)
        self.view.info_panel.btn_analyze.clicked.connect(self.start_post_game_analysis)
        
        self.view.info_panel.start_clicked.connect(lambda: self.navigate_history("start"))
        self.view.info_panel.prev_clicked.connect(lambda: self.navigate_history("prev"))
        self.view.info_panel.next_clicked.connect(lambda: self.navigate_history("next"))
        self.view.info_panel.end_clicked.connect(lambda: self.navigate_history("end"))
        
        # Toggles
        self.view.info_panel.toggle_eval_clicked.connect(self.view.toggle_eval_visibility)
        self.view.info_panel.toggle_arrows_clicked.connect(self.toggle_arrows)
        self.view.info_panel.toggle_auto_rotate_clicked.connect(self.toggle_auto_rotate)

        # Main Menu Actions
        self.view.main_menu.pvp_clicked.connect(lambda: self.start_new_game("PvP"))
        self.view.main_menu.pve_clicked.connect(self.start_pve_game)
        self.view.main_menu.eve_clicked.connect(self.start_eve_game)
        self.view.main_menu.theme_selected.connect(self.apply_theme)
        
        # Engine -> Controller
        self.engine.best_move_found.connect(self.handle_engine_move)
        self.engine.eval_updated.connect(self.handle_eval_update)
        self.engine.analysis_complete.connect(self.handle_analysis_complete)

    @pyqtSlot(str, str)
    def handle_eval_update(self, score, pv_move):
        # 1. PRIORITY: Check actual Board State for Checkmate
        # Stockfish can be slightly delayed or weird with "#0".
        # If the board says Mate, we show Mate/Result immediately and ignore Stockfish score.
        is_mate_on_board = False
        final_text = ""
        
        if self.model.is_checkmate():
            is_mate_on_board = True
            turn = self.model.get_turn()
            
            # LOGIC:
            # If Turn is WHITE -> White has no moves -> White is Mated -> Black Wins.
            # Winner: Black. Eval should be 0.0 (Full Black). Text "0-1".
            
            # If Turn is BLACK -> Black has no moves -> Black is Mated -> White Wins.
            # Winner: White. Eval should be 1.0 (Full White). Text "1-0".
            
            if turn == chess.WHITE:
                 final_text = "0-1"
            else:
                 final_text = "1-0"
            
            # Force update and RETURN to stop processing stockfish output
            self.view.eval_bar.set_eval(final_text)
            self.view.info_panel.update_eval(final_text, "")
            self.engine.stop_search() # Stop engine on mate
            return 

        # 2. Normalize Stockfish Score (if game continues)
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
                
                if val == 0:
                    # Checkmate (M0). 
                    # If it's Black's turn and they have M0 -> Black is mated -> White WON.
                    # If it's White's turn and they have M0 -> White is mated -> Black WON.
                    # Wait. Engine usually reports positive mate for Side to Move?
                    # "Mate in 0" is usually reported as Checkmate.
                    # Actually, if we are here, we trust the engine's output.
                    # If Engine says "Mate 0", it means current side is Checkmated.
                    if is_black_turn: # Black is mated
                         normalized_score = "1-0"
                    else: # White is mated
                         normalized_score = "0-1"
                else:
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
        if pv_move and not self.is_analyzing_game and not is_mate_on_board: 
            try:
                move = chess.Move.from_uci(pv_move)
                self.view.board_widget.set_best_move(move)
            except ValueError:
                pass

    def handle_resign(self):
        if self.model.is_game_over(): return
        
        # Stop Engine
        self.engine.stop_search()
        self.seeking_move = False
        self.eve_timer.stop()
        self.eve_paused = False
        
        # Set Status
        self.view.info_panel.set_status("Game Abandoned")
        
        # Enable Analysis (Treat as finished)
        self.view.info_panel.btn_analyze.setVisible(True)
        self.view.info_panel.btn_analyze.setEnabled(True)
        self.view.info_panel.btn_analyze.setText("Analyze Game")
        
        # Disable controls that shouldn't work post-game
        self.view.info_panel.btn_pause.setVisible(False)

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
             # Start engine after Transition Delay (1.8s)
             # Transition: 400 In + 500 Hold + 400 Out = ~1.3s. +0.5s buffer = 1.8s.
             QTimer.singleShot(1800, self.make_engine_move)

    def start_eve_game(self, white_level, black_level):
        self.start_new_game("EvE")
        self.eve_level_white = white_level
        self.eve_level_white = white_level
        self.eve_level_black = black_level
        self.engine.set_difficulty(white_level)
        
        self.view.info_panel.btn_pause.setVisible(True) # Show for EvE
        self.eve_timer.start(2000) 
        QTimer.singleShot(1800, self.make_engine_move)

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
             
        # Analysis Eval Sync
        # Use current history index OR the latest index if live
        current_idx = self.history_index if self.history_index is not None else len(self.model.move_history)
        
        if current_idx in self.analysis_results:
            data = self.analysis_results[current_idx]
            cp_val = data.get('cp', 0.0) # White's Eval
            
            # Convert to text
            text_score = ""
            if abs(cp_val) > 29000: # Mate
                moves_to_mate = int((30000 - abs(cp_val)) / 100)
                
                if moves_to_mate == 0:
                     # Checkmate has occurred on board (or engine sees it immediately)
                     if cp_val > 0: text_score = "1-0"
                     else: text_score = "0-1"
                else:
                    if cp_val > 0: text_score = f"M{moves_to_mate}"
                    else: text_score = f"M{-moves_to_mate}"
            else:
                # CP
                text_score = f"{cp_val / 100.0:+.2f}"
            
            self.view.eval_bar.set_eval(text_score)
            self.view.info_panel.update_eval(text_score, data.get('best_move', ''))
            
            # Update Move Classification Label
            # Classification applies to the move that CAUSED this position.
            # That move is at index: current_idx - 1.
            move_type = ""
            if current_idx > 0:
                prev_idx = current_idx - 1
                if prev_idx in self.analysis_results:
                    move_type = self.analysis_results[prev_idx].get('type', '')
            
            self.view.info_panel.set_classification(move_type)
        else:
             # If no analysis data available for this step, clear interactions?
             # For now, keep previous or clear? Clearing might flash.
             pass

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
            
        # CRITICAL: Stop any existing search (e.g. analysis) before starting turn
        self.engine.stop_search()
            
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
        
        try:
            move = chess.Move.from_uci(best_move_str)
            
            # GHOST MOVE FILTER:
            # If we interrupted a previous search (e.g. analysis), the engine sends a 'bestmove'.
            # This move might be for the WRONG position (the one being analyzed previously).
            # If so, it will likely be illegal for the current board state.
            # We must IGNORE it and keep 'seeking_move = True' for the real move coming next.
            if move not in self.model.board.legal_moves:
                # print(f"DEBUG: Ignored ghost/illegal move {best_move_str}. Still seeking.")
                return 

            # Move is Valid!
            self.seeking_move = False
            
            if self.is_analyzing_only:
                self.is_analyzing_only = False 
                # If just analyzing, we don't make the move? 
                # Wait, analyze_position sets checking_move=True?
                # analyze_position sets is_analyzing_only=True.
                # If is_analyzing_only, we usually just update arrows (via eval update) and ignore bestmove?
                # Actually, analyze_position stops searching when bestmove arrives?
                # No, we usually let it run until we stop it.
                # If we received bestmove while analyzing, it means it finished depth or time.
                return 
            
            # Real Move found for Bot
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
        # RACE CONDITION CHECK:
        # Since we use a QTimer delay, the board might have changed (e.g. user New Game, Undo).
        # We must re-verify legality before executing.
        if move not in self.model.board.legal_moves:
             # This is expected during fast UI interactions or analysis interrupts.
             # Silently ignore.
             return

        if self.model.make_move(move):
            self.update_view()
            if self.mode == "PvP":
                self.analyze_position()
            elif self.mode == "PvE":
                self.analyze_position()
        else:
             # Should be unreachable due to check above, but keeping safety.
             pass

    def analyze_position(self):
        if not self.model.is_game_over():
             self.engine.stop_search() 
             self.engine.set_position(self.model.get_fen())
             self.seeking_move = True 
             self.is_analyzing_only = True 
             # Force Engine to Max Strength for Analysis
             # This ensures arrows/eval are accurate even if Bot is Level 1.
             self.engine.send_command("setoption name Skill Level value 20")
             self.engine.go(depth=20) 

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
            
        if not self.model.move_history:
             QMessageBox.warning(self.view, "Analysis", "No game history to analyze!")
             print("DEBUG: No history.")
             return
            
        # Stop any background analysis first
        self.engine.stop_search()
        self.seeking_move = False
        self.is_analyzing_only = False
        
        # Clear outdated visuals
        self.view.board_widget.set_best_move(None)
        self.view.board_widget.set_annotation(None)
        
        # UI Feedback
        self.view.info_panel.btn_analyze.setEnabled(False)
        self.view.info_panel.btn_analyze.setText("Initializing...")
        
        # Critical: Delay setting state to TRUE until we are sure previous engine output is flushed.
        QTimer.singleShot(200, self.begin_analysis_loop)

    def begin_analysis_loop(self):
        self.is_analyzing_game = True
        self.analysis_results = {}
        self.analysis_index = 0
        self.view.info_panel.set_status("Analyzing game...")
        self.analyze_next_step()

    def analyze_next_step(self):
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
        
        # TERMINAL STATE HANDLING:
        # If the game is over, the engine might give weird results or just "mate 0".
        # We handle it explicitly to ensure correct "Loss" calculation for the final move.
        if board.is_game_over():
            # Determine Score from Side-To-Move perspective
            # If Checked -> Checkmate -> -30000 (We lost)
            # Else -> Stalemate/Draw -> 0
            
            cp = 0
            if board.is_checkmate():
                 cp = -30000 # Side to move is mated
            
            # Simulate Engine Result
            # pvs[1] = {'cp': cp, 'pv_move': ''}
            pvs = { 1: {'cp': cp, 'pv_move': ''} }
            
            # Proceed immediately
            self.handle_analysis_complete(pvs)
            return

        # Send position to engine
        self.engine.set_position(board.fen())
        
        # Start Analysis
        # Enable MultiPV to allow "Great Move" detection (comparing best vs second best)
        self.engine.go(depth=20, multipv=3) 
        
        # Safety Timeout: If engine hangs for > 10 seconds, force next step
        QTimer.singleShot(10000, lambda: self.force_next_analysis_step(self.analysis_index))

    def force_next_analysis_step(self, expected_index):
        if self.is_analyzing_game and self.analysis_index == expected_index:
            # Engine stuck? Stop it to force output flush (which we'll ignore/handle)
            # print(f"DEBUG: Timeout at step {expected_index}. Sending STOP to force progress.")
            self.engine.stop_search()
            # Do NOT call handle_analysis_complete manually. 
            # The 'stop' command will trigger 'bestmove' from engine, 
            # which will trigger handle_analysis_complete via signal. 

    def handle_analysis_complete(self, pvs):
        """
        Called when engine finishes analyzing a step during Post-Game Analysis.
        """
        if not self.is_analyzing_game:
            return
            
        try:
            # 0. Sync Check: Validate Move against Current Analysis Board
            # Reconstruct board state for current index to verify move legality
            # self.current_analysis_board SHOULD match self.analysis_index
            # But let's rely on reconstruction to be 100% safe
            check_board = chess.Board()
            for i in range(self.analysis_index):
                check_board.push(self.model.move_history[i])
            
            # Extract Best Move
            best_move_uci = ""
            cp = 0.0
            second_best_cp = None
            
            if pvs and 1 in pvs:
                info = pvs[1]
                best_move_uci = info.get('pv_move', '')
                
                # VALIDATION: Check if move is legal
                if best_move_uci:
                    try:
                        move = chess.Move.from_uci(best_move_uci)
                        if move not in check_board.legal_moves:
                            print(f"WARNING: Illegal move {best_move_uci} suggested for step {self.analysis_index}. Discarding.")
                            # Discard this result? Or just the move? 
                            # If move is illegal, result is probably garbage.
                            pvs = {} 
                            best_move_uci = ""
                    except:
                        best_move_uci = ""
            
            # Extract Score / Second Best Score (from validated pvs)
            if pvs:
                # DEBUG: Check what PVs we have
                print(f"DEBUG Engine PVs: keys={list(pvs.keys())}, content={pvs}")
                
                # Top Move (re-extract)
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
                    
                # Construct top_moves for classifier
                # IMPORTANT: Classifier expects WHITE-CENTRIC evals and handles perspective internally
                turn_color = prev_board.turn # Side that moved
                
                # 1. Best Move Eval (from prev_data) - WHITE-CENTRIC as stored
                best_cp = prev_data['cp']  # Already white-centric
                
                # 2. Played Move Eval (from white_cp - which is eval of position AFTER move)
                # white_cp is already white-centric
                played_cp = white_cp  # Already white-centric
                
                fake_top_moves = {
                    1: {'pv_move': prev_data['best_move'], 'cp': int(best_cp)}
                }
                
                # Add Second Best if available
                # second_best_cp is stored as RAW side-to-move from engine
                # We need to convert it to white-centric
                if prev_data.get('second_best_cp') is not None:
                    second_cp = prev_data['second_best_cp']
                    # second_best_cp is side-to-move, convert to white-centric
                    if turn_color == chess.BLACK:
                        second_cp = -second_cp  # Flip to white-centric
                    fake_top_moves[2] = {'cp': int(second_cp)}
                     
                # Add Played Move as a "fake" rank
                if played_uci != prev_data['best_move']:
                    fake_top_moves[99] = {'pv_move': played_uci, 'cp': int(played_cp)}
                else:
                    pass
                    
                # Call Classifier
                classification = self.classifier.classify_move(prev_board, played_move_obj, fake_top_moves)
                prev_data['type'] = classification
                
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
        
        # Find and display the opening name
        from src.analysis.opening_book import get_opening_name
        last_opening = None
        temp_board = chess.Board()
        for move in self.model.move_history:
            temp_board.push(move)
            opening = get_opening_name(temp_board.fen())
            if opening:
                last_opening = opening
        self.view.info_panel.analysis_dashboard.set_opening(last_opening)
        
        # Reset to first move so user starts from beginning
        self.history_index = 0
        
        # Refresh board
        self.update_board_visuals()

    def exit_post_game_analysis(self):
        print("DEBUG: exit_post_game_analysis triggered")
        # 1. Transition to Main Menu immediately (Starts Fade Out)
        self.view.show_menu()
        print("DEBUG: show_menu called (Transition Start)")
        
        # 2. Reset InfoPanel to Game Controls *during* the transition hold.
        # Transition: 400ms fade in -> 500ms hold -> 400ms fade out.
        # We trigger the switch at 600ms so it happens safely while screen is black.
        # Make the lambda explicit to debug if needed
        QTimer.singleShot(600, lambda: (print("DEBUG: Switching InfoPanel to Game now"), self.view.info_panel.show_game()))
        
        # 3. Clear Analysis Artifacts
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
             
        item, ok = QInputDialog.getItem(self.view, "Select Theme", "Theme:", themes, current_idx, False)
        if ok and item:
            self.apply_theme(item)

    @pyqtSlot(str)
    def apply_theme(self, theme_name):
        self.view.board_widget.set_theme(theme_name)
        # Also update Menu Preview just in case (though it updates itself locally)
        self.view.main_menu.theme_preview.set_theme(theme_name) 
        # Update combo in menu if changed from InfoPanel
        self.view.main_menu.combo_theme.setCurrentText(theme_name)


    def toggle_pause(self):
        self.eve_paused = not self.eve_paused
        self.view.info_panel.set_status("Paused" if self.eve_paused else "Running")
        if not self.eve_paused and self.mode == "EvE":
             self.make_engine_move()

    def close(self):
        self.engine.stop_engine()
