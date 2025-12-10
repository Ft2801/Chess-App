from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QFrame, QGridLayout, QCheckBox, QGroupBox, QStackedLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class AnalysisDashboard(QWidget):
    exit_clicked = pyqtSignal()
    start_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    end_clicked = pyqtSignal()
    
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
        
        # Exit Button
        self.btn_exit = QPushButton("Back to Game View")
        self.btn_exit.clicked.connect(self.exit_clicked)
        self.btn_exit.setStyleSheet("background-color: #34495e; padding: 10px;")
        layout.addWidget(self.btn_exit)

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
    back_clicked = pyqtSignal()
    
    # Toggles
    toggle_eval_clicked = pyqtSignal(bool)
    toggle_arrows_clicked = pyqtSignal(bool)
    toggle_auto_rotate_clicked = pyqtSignal(bool)
    
    # Analysis Signals
    exit_analysis_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.stack_layout = QStackedLayout(self)
        
        # --- Page 1: Game Controls ---
        self.game_controls_widget = QWidget()
        self.init_game_controls()
        self.stack_layout.addWidget(self.game_controls_widget)
        
        # --- Page 2: Analysis Dashboard ---
        self.analysis_dashboard = AnalysisDashboard()
        self.analysis_dashboard.exit_clicked.connect(self.exit_analysis_clicked)
        
        # Connect Navigation Signals
        self.analysis_dashboard.start_clicked.connect(self.start_clicked)
        self.analysis_dashboard.prev_clicked.connect(self.prev_clicked)
        self.analysis_dashboard.next_clicked.connect(self.next_clicked)
        self.analysis_dashboard.end_clicked.connect(self.end_clicked)
        
        self.stack_layout.addWidget(self.analysis_dashboard)
        
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
        self.chk_eval.setChecked(True)
        self.chk_eval.toggled.connect(self.toggle_eval_clicked)
        
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
        self.stack_layout.setCurrentWidget(self.analysis_dashboard)
        
    def show_game(self):
        self.stack_layout.setCurrentWidget(self.game_controls_widget)
