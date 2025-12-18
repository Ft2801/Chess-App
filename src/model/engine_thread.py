import subprocess
import threading
import time
from PyQt6.QtCore import QThread, pyqtSignal

class EngineThread(QThread):
    """
    Handles communication with the Stockfish engine in a separate thread.
    """
    best_move_found = pyqtSignal(str)
    eval_updated = pyqtSignal(str, str) # evaluation (e.g. "+1.5", "#-3"), best_move
    analysis_complete = pyqtSignal(object) # Emit dict of PVs when bestmove received
    
    def __init__(self, engine_path="engine/stockfish.exe"):
        super().__init__()
        self.engine_path = engine_path
        self.process = None
        self.running = False
        self.command_queue = []
        self.lock = threading.Lock()
        
        # Analysis State
        self.current_pvs = {} # { multipv_id: { 'score': ..., 'pv': ... } }
        
        # Difficulty Settings
        self.difficulty_skill = 20
        self.difficulty_depth = 22
        self.difficulty_movetime = 1000

    def start_engine(self):
        try:
            # Create subprocess with pipes
            self.process = subprocess.Popen(
                self.engine_path,
                universal_newlines=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.send_command("uci")
            self.send_command("isready")
            self.running = True
            self.start() # Start the QThread run loop for reading output
        except FileNotFoundError:
            print(f"Error: Engine not found at {self.engine_path}")

    def stop_search(self):
        """Stops the current search without quitting the engine."""
        if self.process:
            self.send_command("stop")
            self.send_command("isready") # Sync

    def stop_engine(self):
        self.running = False
        if self.process:
            self.send_command("stop") # Ensure search stops
            self.send_command("quit")
            self.process.communicate() # Wait for it to exit
            self.process = None
        self.quit() # Stop QThread
        self.wait()

    def send_command(self, command):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(f"{command}\n")
                self.process.stdin.flush()
                
                # Reset PVs on new search command
                if command.startswith("go") or command.startswith("position"):
                    # We accept that analysis accumulates until a new command or completion.
                    pass 
            except OSError as e:
                print(f"Error sending command: {e}")

    def set_position(self, fen):
        self.send_command(f"position fen {fen}")

    def go(self, depth=None, movetime=None, multipv=1):
        # Reset analysis data for new search
        self.current_pvs = {}
        
        # Ensure multipv option is set
        self.send_command(f"setoption name MultiPV value {multipv}")
        
        cmd = "go"
        
        # If arguments provided, use them (overrides difficulty)
        if depth is not None or movetime is not None:
             if depth: cmd += f" depth {depth}"
             if movetime: cmd += f" movetime {movetime}"
        else:
             # Use difficulty settings
             # Combine both as requested
             cmd += f" depth {self.difficulty_depth} movetime {self.difficulty_movetime}"
             
        self.send_command(cmd)

    def set_difficulty(self, level):
        """
        Sets engine difficulty based on defined levels (1-8).
        """
        # Disable Elo limiting to use raw Skill Level
        self.send_command("setoption name UCI_LimitStrength value false")
        
        levels = {
            1: {"skill": -9, "depth": 1, "time": 50},
            2: {"skill": -5, "depth": 2, "time": 100},
            3: {"skill": -1, "depth": 3, "time": 150},
            4: {"skill": 3, "depth": 5, "time": 200},
            5: {"skill": 7, "depth": 5, "time": 300},
            6: {"skill": 11, "depth": 8, "time": 400},
            7: {"skill": 16, "depth": 13, "time": 500},
            8: {"skill": 20, "depth": 22, "time": 1000}
        }
        
        config = levels.get(level, levels[8]) # Default to max if not found
        
        # Clamp Skill to valid Stockfish range (0-20)
        self.difficulty_skill = max(0, min(20, config["skill"]))
        
        self.difficulty_depth = config["depth"]
        self.difficulty_movetime = config["time"]

        self.send_command(f"setoption name Skill Level value {self.difficulty_skill}")


    def run(self):
        """
        Thread loop to read engine output.
        """
        while self.running and self.process:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                
                # Parse output
                if line.startswith("bestmove"):
                    parts = line.split()
                    if len(parts) >= 2:
                        best_move = parts[1]
                        self.best_move_found.emit(best_move)
                        # Analysis done, emit FULL results
                        self.analysis_complete.emit(self.current_pvs)
                
                elif "info" in line and "score" in line:
                    # Provide eval updates
                    try:
                        parts = line.split()
                        
                        score_val = ""
                        pv_move = ""
                        multipv_id = 1
                        
                        # Extract MultiPV ID
                        if "multipv" in parts:
                            idx = parts.index("multipv")
                            multipv_id = int(parts[idx+1])
                        
                        # Extract Score
                        # We store raw Centipawn value for analysis usage too
                        cp = 0
                        mate = None
                        
                        if "score cp" in line:
                            try:
                                idx = parts.index("cp")
                                val = int(parts[idx+1])
                                cp = val
                                score_val = f"{val/100.0:+.2f}"
                            except: pass
                        elif "score mate" in line:
                            try:
                                idx = parts.index("mate")
                                val = int(parts[idx+1])
                                mate = val
                                score_val = f"#{val}"
                            except: pass
                            
                        # Extract PV (Principal Variation - Best Move)
                        if " pv " in line:
                            try:
                                idx = parts.index("pv")
                                if idx + 1 < len(parts):
                                    pv_move = parts[idx+1] # First move of PV
                            except: pass
                        
                        # Store in current_pvs
                        self.current_pvs[multipv_id] = {
                            "score_str": score_val,
                            "cp": cp,
                            "mate": mate,
                            "pv_move": pv_move,
                            "full_line": line
                        }
                        
                        # Emit regular update ONLY for primary line (MultiPV 1) for UI Live Eval
                        if multipv_id == 1 and (score_val or pv_move):
                             self.eval_updated.emit(score_val, pv_move)
                            
                    except Exception as e:
                        pass # Ignore parsing errors in the loop

            except Exception as e:
                print(f"Engine thread error: {e}")
                break
