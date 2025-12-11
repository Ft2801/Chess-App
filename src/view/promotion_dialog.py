import chess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal


class PromotionDialog(QWidget):
    """
    Dialog for selecting the piece to promote a pawn to.
    Shows as a vertical column of piece options on the promotion square.
    """
    
    piece_selected = pyqtSignal(chess.PieceType)  # Emits the promotion piece type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pieces = {}
        self.selected_piece = None
        self._load_pieces()
        
        # Style as dialog
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(
            "background-color: rgba(30, 30, 30, 250); "
            "border: 2px solid #4a90e2; "
            "border-radius: 4px;"
        )
        
        # Start hidden
        self.setVisible(False)
        
        self.init_ui()
    
    def _load_pieces(self):
        """Load piece images."""
        piece_types = ['N', 'B', 'R', 'Q']
        colors = ['w', 'b']
        for color in colors:
            for p_type in piece_types:
                filename = f"assets/pieces/{color}{p_type}.png"
                pixmap = QPixmap(filename)
                if not pixmap.isNull():
                    self.pieces[f"{color}{p_type}"] = pixmap
    
    def init_ui(self):
        """Initialize the UI with 4 piece options in vertical layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        # Promotion pieces: Queen, Rook, Bishop, Knight (top to bottom)
        self.piece_buttons = {}
        promotion_pieces = [
            (chess.QUEEN, 'Q'),
            (chess.ROOK, 'R'),
            (chess.BISHOP, 'B'),
            (chess.KNIGHT, 'N'),
        ]
        
        for piece_type, symbol in promotion_pieces:
            button = PromotionPieceButton(piece_type, symbol, self.pieces)
            button.clicked.connect(lambda checked=False, pt=piece_type: self.on_piece_selected(pt))
            self.piece_buttons[piece_type] = button
            layout.addWidget(button)
    
    def on_piece_selected(self, piece_type: chess.PieceType):
        """Handle piece selection."""
        self.selected_piece = piece_type
        self.piece_selected.emit(piece_type)
        self.hide()
    
    def show_for_color(self, color: bool):
        """Show the dialog with the appropriate piece color."""
        # Store color for drawing pieces
        self.piece_color = 'w' if color == chess.WHITE else 'b'
        
        # Update piece buttons with correct color
        for piece_type, button in self.piece_buttons.items():
            button.set_color(self.piece_color)
        
        self.show()


class PromotionPieceButton(QLabel):
    """
    A clickable piece option in the promotion dialog.
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, piece_type: chess.PieceType, symbol: str, pieces_dict: dict, parent=None):
        super().__init__(parent)
        self.piece_type = piece_type
        self.symbol = symbol
        self.pieces_dict = pieces_dict
        self.piece_color = 'w'  # Default white
        
        self.setFixedSize(48, 48)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "QLabel { "
            "border: 1px solid #666666; "
            "border-radius: 4px; "
            "background-color: rgba(50, 50, 50, 200); "
            "} "
            "QLabel:hover { "
            "background-color: rgba(80, 80, 80, 255); "
            "border: 2px solid #4a90e2; "
            "}"
        )
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def set_color(self, color: str):
        """Set the color of the piece to display ('w' or 'b')."""
        self.piece_color = color
        self.update_pixmap()
    
    def update_pixmap(self):
        """Update the displayed piece pixmap."""
        piece_key = f"{self.piece_color}{self.symbol}"
        if piece_key in self.pieces_dict:
            pixmap = self.pieces_dict[piece_key].scaledToHeight(
                40,
                mode=Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(pixmap)
    
    def mousePressEvent(self, ev):
        """Handle mouse click."""
        self.clicked.emit()
