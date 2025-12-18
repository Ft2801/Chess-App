from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QFrame, QGridLayout, QCheckBox, QGroupBox, QStackedLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from src.view.fading_widget import FadingStackedWidget

class AnalysisDashboard(QWidget):
    exit_clicked = pyqtSignal()
    start_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    end_clicked = pyqtSignal()
    toggle_best_move = pyqtSignal(bool)
    toggle_eval = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Post-Game Analysis")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00B4D8;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Accuracy Stats
        stats_group = QGroupBox("Accuracy")
        stats_layout = QGridLayout(stats_group)
        
        self.lbl_white_acc = QLabel("White: --%")
        self.lbl_black_acc = QLabel("Black: --%")
        self.lbl_white_acc.setStyleSheet("color: #E8EAED; font-size: 14px;")
        self.lbl_black_acc.setStyleSheet("color: #E8EAED; font-size: 14px;")
        
        stats_layout.addWidget(self.lbl_white_acc, 0, 0)
        stats_layout.addWidget(self.lbl_black_acc, 0, 1)
        layout.addWidget(stats_group)
        
        # Classification Count
        class_group = QGroupBox("Move Quality")
        self.class_layout = QGridLayout(class_group) # Dynamic
        layout.addWidget(class_group)
        
        # Current Move Classification Label
        self.lbl_current_move = QLabel("-")
        self.lbl_current_move.setStyleSheet("font-size: 16px; font-weight: bold; color: #F1C40F; margin: 5px;")
        self.lbl_current_move.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_current_move)
        
        # Opening Name Label (NEW)
        self.lbl_opening = QLabel("")
        self.lbl_opening.setStyleSheet("font-size: 13px; color: #FFFFFF; font-style: italic; margin: 5px;")
        self.lbl_opening.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_opening.setWordWrap(True)
        layout.addWidget(self.lbl_opening)
        
        layout.addStretch()
        
        # Navigation Analysis
        nav_group = QGroupBox("Review Moves")
        nav_layout = QHBoxLayout(nav_group)
        
        self.btn_start = QPushButton("<<")
        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")
        self.btn_end = QPushButton(">>")
        
        self.btn_start.clicked.connect(self.start_clicked)
        self.btn_prev.clicked.connect(self.prev_clicked)
        self.btn_next.clicked.connect(self.next_clicked)
        self.btn_end.clicked.connect(self.end_clicked)
        
        nav_layout.addWidget(self.btn_start)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.btn_end)
        
        layout.addWidget(nav_group)

        # Settings Group (New)
        settings_group = QGroupBox("Analysis Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Eval Bar Toggle
        self.chk_eval = QCheckBox("Show Eval Bar")
        self.chk_eval.setChecked(False) # Default hidden
        self.chk_eval.toggled.connect(self.toggle_eval)
        settings_layout.addWidget(self.chk_eval)
        
        self.chk_best_move = QCheckBox("Show Best Move Arrow")
        self.chk_best_move.toggled.connect(self.toggle_best_move)
        settings_layout.addWidget(self.chk_best_move)
        
        layout.addWidget(settings_group)
        
        # Exit Button
        self.btn_exit = QPushButton("Back to Menu")
        self.btn_exit.clicked.connect(self.exit_clicked)
        self.btn_exit.setStyleSheet("background-color: #34495e; padding: 10px;")
        layout.addWidget(self.btn_exit)

    def set_current_move_classification(self, text):
        # Map text to colors
        colors = {
            "brilliant": "#1ABCDE", # Light blue
            "critical": "#0E86D4",  # Darker blue than brilliant
            "great": "#3498DB",     # Blue
            "best": "#2ECC71",      # Green
            "excellent": "#27AE60",
            "good": "#BDC3C7",      # Grey
            "inaccuracy": "#F39C12",# Orange
            "mistake": "#E67E22",   # Dark Orange
            "blunder": "#C0392B",   # Red
            "forced": "#7F8C8D",
            "theory": "#CD9575"
        }
        color = colors.get(text.lower(), "#ECF0F1")
        
        # Format Text
        display_text = text.replace("_", " ").title()
        if text.lower() == "brilliant": display_text += " !!"
        elif text.lower() == "great": display_text += " !"
        elif text.lower() == "blunder": display_text += " ??"
        elif text.lower() == "mistake": display_text += " ?"
        
        self.lbl_current_move.setText(display_text)
        self.lbl_current_move.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color}; margin: 5px;")

    def set_opening(self, opening_name: str):
        """Set the opening name display."""
        if opening_name:
            self.lbl_opening.setText(f"📖 {opening_name}")
            self.lbl_opening.setVisible(True)
        else:
            self.lbl_opening.setText("")
            self.lbl_opening.setVisible(False)

    def update_stats(self, counts, accuracy):
        from PyQt6.QtGui import QPixmap
        import os
        
        # Update Accuracy
        self.lbl_white_acc.setText(f"White: {accuracy.get('white', 0):.1f}%")
        self.lbl_black_acc.setText(f"Black: {accuracy.get('black', 0):.1f}%")
        
        # Clear previous stats
        while self.class_layout.count():
            child = self.class_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Populate new stats
        row = 0
        for label, count in counts.items():
            # Icon
            icon_lbl = QLabel()
            
            icon_map = {'great': 'critical', 'good': 'okay', 'book': 'best'}
            filename = icon_map.get(label, label)
            icon_path = f"assets/classifications/{filename}.png"
            
            if os.path.exists(icon_path):
                pix = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon_lbl.setPixmap(pix)
            
            # Text
            text_lbl = QLabel(f"{label.capitalize()}: {count}")
            text_lbl.setStyleSheet("font-size: 13px; color: #BDC3C7;")
            
            self.class_layout.addWidget(icon_lbl, row, 0)
            self.class_layout.addWidget(text_lbl, row, 1)
            row += 1

class InfoPanel(QWidget):
    undo_clicked = pyqtSignal()
    flip_clicked = pyqtSignal()
    start_clicked = pyqtSignal()
    end_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    theme_clicked = pyqtSignal()
    analyze_clicked = pyqtSignal()
    analyze_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    resign_clicked = pyqtSignal()
    
    # Toggles
    toggle_eval_clicked = pyqtSignal(bool)
    toggle_arrows_clicked = pyqtSignal(bool)
    toggle_auto_rotate_clicked = pyqtSignal(bool)
    
    # Analysis Signals
    exit_analysis_clicked = pyqtSignal()
    
    def set_classification(self, text):
        """
        Updates the move classification label.
        Delegates to the active view (AnalysisDashboard or GameControls).
        """
        # Update Analysis Dashboard
        if hasattr(self, 'analysis_dashboard'):
             self.analysis_dashboard.set_current_move_classification(text)
             
        # Optional: could update GameControls if we wanted "Brilliant" to show there too.
        # For now, just fix the AttributeError.

    def __init__(self):
        super().__init__()
        
        # Use a layout to hold the FadingStackedWidget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = FadingStackedWidget()
        main_layout.addWidget(self.stack)
        
        # --- Page 1: Game Controls ---
        self.game_controls_widget = QWidget()
        self.init_game_controls()
        self.stack.addWidget(self.game_controls_widget)
        
        # --- Page 2: Analysis Dashboard ---
        self.analysis_dashboard = AnalysisDashboard()
        self.analysis_dashboard.exit_clicked.connect(self.exit_analysis_clicked)
        
        # Connect Navigation Signals
        self.analysis_dashboard.start_clicked.connect(self.start_clicked)
        self.analysis_dashboard.prev_clicked.connect(self.prev_clicked)
        self.analysis_dashboard.next_clicked.connect(self.next_clicked)
        self.analysis_dashboard.end_clicked.connect(self.end_clicked)
        self.analysis_dashboard.toggle_best_move.connect(self.toggle_arrows_clicked) 
        self.analysis_dashboard.toggle_eval.connect(self.toggle_eval_clicked)
        
        self.stack.addWidget(self.analysis_dashboard)
        
    def init_game_controls(self):
        layout = QVBoxLayout(self.game_controls_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        self.btn_back = QPushButton("Menu")
        self.btn_back.setFixedWidth(60)
        self.btn_back.clicked.connect(self.back_clicked)
        header_layout.addWidget(self.btn_back)
        
        self.status_label = QLabel("Welcome")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

        # --- Move List ---
        self.move_list = QTextEdit()
        self.move_list.setReadOnly(True)
        self.move_list.setPlaceholderText("Moves...")
        layout.addWidget(self.move_list)
        
        # --- Eval Label ---
        self.eval_label = QLabel("Eval: 0.00")
        self.eval_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eval_label.setStyleSheet("font-family: Monospace; font-size: 14px; color: #4a90e2;")
        layout.addWidget(self.eval_label)

        # --- Controls Area ---
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(10)
        
        # Navigation Grid
        nav_grid = QGridLayout()
        self.btn_start = QPushButton("<<")
        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")
        self.btn_end = QPushButton(">>")
        
        self.btn_start.clicked.connect(self.start_clicked)
        self.btn_prev.clicked.connect(self.prev_clicked)
        self.btn_next.clicked.connect(self.next_clicked)
        self.btn_end.clicked.connect(self.end_clicked)
        
        nav_grid.addWidget(self.btn_start, 0, 0)
        nav_grid.addWidget(self.btn_prev, 0, 1)
        nav_grid.addWidget(self.btn_next, 0, 2)
        nav_grid.addWidget(self.btn_end, 0, 3)
        controls_layout.addLayout(nav_grid)
        
        # Game Actions (Row 1)
        actions_layout = QHBoxLayout()
        self.btn_undo = QPushButton("Undo")
        self.btn_undo.clicked.connect(self.undo_clicked)
        self.btn_flip = QPushButton("Flip")
        self.btn_flip.clicked.connect(self.flip_clicked)
        self.btn_theme = QPushButton("Theme")
        self.btn_theme.clicked.connect(self.theme_clicked)
        self.btn_pause = QPushButton("Pause") # For EvE
        self.btn_pause.setCheckable(True)
        self.btn_pause.clicked.connect(self.pause_clicked)
        
        actions_layout.addWidget(self.btn_undo)
        actions_layout.addWidget(self.btn_flip)
        actions_layout.addWidget(self.btn_theme)
        actions_layout.addWidget(self.btn_pause)
        
        # Resign Button
        self.btn_resign = QPushButton("End Game")
        self.btn_resign.clicked.connect(self.resign_clicked)
        self.btn_resign.setStyleSheet("background-color: #c0392b; color: white;")
        actions_layout.addWidget(self.btn_resign)
        
        controls_layout.addLayout(actions_layout)
        
        # Analysis Actions (Row 2 - Dedicated)
        self.btn_analyze = QPushButton("Analyze Game")
        self.btn_analyze.clicked.connect(self.analyze_clicked)
        self.btn_analyze.setVisible(False)
        self.btn_analyze.setStyleSheet("background-color: #2c3e50; border-color: #34495e; padding: 8px;") 
        controls_layout.addWidget(self.btn_analyze)
        
        layout.addWidget(controls_group)
        
        # --- Settings Area ---
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        self.chk_eval = QCheckBox("Show Eval Bar")
        self.chk_eval.setChecked(False)
        self.chk_eval.toggled.connect(self.toggle_eval_clicked)
        # Hide Eval Label if Bar is hidden (User Request)
        self.chk_eval.toggled.connect(self.eval_label.setVisible)
        self.eval_label.setVisible(False) # Initial state off
        
        self.chk_arrows = QCheckBox("Show Best Move Arrow")
        self.chk_arrows.setChecked(False) 
        self.chk_arrows.toggled.connect(self.toggle_arrows_clicked)
        
        self.chk_auto_rotate = QCheckBox("Auto-Rotate Board")
        self.chk_auto_rotate.setChecked(False)
        self.chk_auto_rotate.toggled.connect(self.toggle_auto_rotate_clicked)
        
        settings_layout.addWidget(self.chk_eval)
        settings_layout.addWidget(self.chk_arrows)
        settings_layout.addWidget(self.chk_auto_rotate)
        
        layout.addWidget(settings_group)

    def update_moves(self, pgn_text):
        self.move_list.setText(pgn_text)
        sb = self.move_list.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_eval(self, score_str, pv_move=""):
        text = f"Eval: {score_str}"
        if pv_move:
             text += f" (Best: {pv_move})"
        self.eval_label.setText(text)

    def set_status(self, text):
        self.status_label.setText(text)
        
    def show_analysis(self):
        self.analysis_dashboard.chk_best_move.setChecked(self.chk_arrows.isChecked())
        # Sync Eval Visibility state
        self.analysis_dashboard.chk_eval.setChecked(self.chk_eval.isChecked())
        
        self.stack.setCurrentWidget(self.analysis_dashboard)
        
    def show_game(self):
        self.stack.setCurrentWidget(self.game_controls_widget)
