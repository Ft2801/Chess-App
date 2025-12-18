from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, 
    QStackedLayout, QVBoxLayout, QStackedWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QAbstractAnimation
from src.view.fading_widget import FadingStackedWidget
from src.view.board_widget import BoardWidget
from src.view.info_panel import InfoPanel
from src.view.main_menu import MainMenu
from src.view.eval_bar import EvalBar
from src.view.captured_pieces import CapturedPiecesWidget
from src.utils.styles import Styles

class MainWindow(QMainWindow):
    def toggle_eval_visibility(self, visible):
        # We manipulate opacity instead of visibility to maintain layout size
        effect = QGraphicsOpacityEffect(self.eval_bar)
        effect.setOpacity(1.0 if visible else 0.0)
        self.eval_bar.setGraphicsEffect(effect)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Chess App")
        self.resize(1100, 750)
        
        # Apply Styles
        self.setStyleSheet(Styles.DARK_THEME)

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Stacked Layout: Index 0 = Menu, Index 1 = Game
        # Replaced QStackedLayout with FadingStackedWidget for smooth transitions
        self.stack = FadingStackedWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        
        # --- Screen 1: Main Menu ---
        self.main_menu = MainMenu()
        self.stack.addWidget(self.main_menu)
        
        # --- Screen 2: Game Interface ---
        self.game_widget = QWidget()
        game_layout = QHBoxLayout(self.game_widget)
        game_layout.setContentsMargins(10, 10, 10, 10)
        game_layout.setSpacing(10)
        
        # Left side: Board + Captured Pieces (stacked vertically)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        
        # 1. Top Captured Pieces (White captured = Black's pieces)
        self.captured_pieces_top = CapturedPiecesWidget(is_top=True)
        left_layout.addWidget(self.captured_pieces_top, stretch=0)
        
        # 2. Board
        self.board_widget = BoardWidget()
        left_layout.addWidget(self.board_widget, stretch=7)
        
        # 3. Bottom Captured Pieces (Black captured = White's pieces)
        self.captured_pieces_bottom = CapturedPiecesWidget(is_top=False)
        left_layout.addWidget(self.captured_pieces_bottom, stretch=0)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        
        # Splitter to hold [Board+Captured, Eval, Info]
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 4. Eval Bar (Vertical)
        self.eval_bar = EvalBar()
        self.eval_bar.setFixedWidth(20)
        
        # Retention Policy
        sp = self.eval_bar.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.eval_bar.setSizePolicy(sp)
        
        # Default Hidden (Opacity 0)
        self.toggle_eval_visibility(False)
        
        # 5. Info Panel
        self.info_panel = InfoPanel()
        
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.eval_bar)
        self.splitter.addWidget(self.info_panel)
        
        self.splitter.setStretchFactor(0, 7) # Board bigger
        self.splitter.setStretchFactor(1, 0) # Eval fixed
        self.splitter.setStretchFactor(2, 3) # Panel (30%)
        self.splitter.setCollapsible(1, False)
        
        game_layout.addWidget(self.splitter)
        self.stack.addWidget(self.game_widget)
        
        # Initially show Menu
        self.show_menu()

    def show_menu(self):
        self.stack.setCurrentIndex(0)

    def show_game(self):
        self.stack.setCurrentIndex(1)
