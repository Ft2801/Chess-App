from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, 
    QStackedLayout
)
from PyQt6.QtCore import Qt
from src.view.board_widget import BoardWidget
from src.view.info_panel import InfoPanel
from src.view.main_menu import MainMenu
from src.view.eval_bar import EvalBar
from src.utils.styles import Styles

class MainWindow(QMainWindow):
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
        self.stack = QStackedLayout(central)
        
        # --- Screen 1: Main Menu ---
        self.main_menu = MainMenu()
        self.stack.addWidget(self.main_menu)
        
        # --- Screen 2: Game Interface ---
        self.game_widget = QWidget()
        game_layout = QHBoxLayout(self.game_widget)
        game_layout.setContentsMargins(10, 10, 10, 10)
        game_layout.setSpacing(10)
        
        # Splitter to hold [Board, Eval, Info]
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 1. Board
        self.board_widget = BoardWidget()
        
        # 2. Eval Bar (Vertical)
        self.eval_bar = EvalBar()
        self.eval_bar.setVisible(True) # Default visible
        
        # 3. Info Panel
        self.info_panel = InfoPanel()
        
        self.splitter.addWidget(self.board_widget)
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
