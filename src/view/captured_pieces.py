import chess
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtCore import Qt

class CapturedPiecesWidget(QWidget):
    """
    Displays captured pieces in a compact horizontal layout.
    Shows "Color: [pieces with counters]" format.
    """
    
    PIECE_SIZE = 24  # Fixed size for piece icons
    COUNTER_SIZE = 16  # Size for counter text
    
    def __init__(self, is_top: bool = True, parent=None):
        """
        Initialize the captured pieces widget.
        
        Args:
            is_top: True for top position, False for bottom position
            parent: Parent widget
        """
        super().__init__(parent)
        self.is_top = is_top
        self.pieces = {}
        self.board_flipped = False  # Track if board is flipped
        self._load_pieces()
        
        # Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Label for player name
        self.player_label = QLabel()
        self.player_label.setStyleSheet("font-weight: bold; color: #E8EAED; font-size: 11px; margin-right: 8px;")
        self.player_label.setFixedWidth(50)
        main_layout.addWidget(self.player_label)
        
        # Container for pieces (fixed size)
        self.pieces_container = QWidget()
        self.pieces_layout = QHBoxLayout(self.pieces_container)
        self.pieces_layout.setContentsMargins(0, 0, 0, 0)
        self.pieces_layout.setSpacing(2)
        
        # Fixed width to accommodate pieces without resizing
        self.pieces_container.setFixedWidth(220)
        main_layout.addWidget(self.pieces_container)
        
        main_layout.addStretch()
        
        self.setFixedHeight(30)
    
    def _load_pieces(self):
        """Load piece images from assets."""
        piece_types = ['P', 'N', 'B', 'R', 'Q', 'K']
        colors = ['w', 'b']
        for color in colors:
            for p_type in piece_types:
                filename = f"assets/pieces/{color}{p_type}.png"
                pixmap = QPixmap(filename)
                if not pixmap.isNull():
                    self.pieces[f"{color}{p_type}"] = pixmap
                else:
                    print(f"Failed to load {filename}")
    
    def set_board_flipped(self, flipped: bool):
        """
        Update the widget when the board is flipped.
        When flipped, Black is at bottom and White at top (and vice versa).
        """
        self.board_flipped = flipped
    
    def update_captured_pieces(self, board: chess.Board):
        try:
            """
            Update the display of captured pieces based on the board state.
            
            Args:
                board: The chess board to analyze
            """
            # Determine which player is shown at current position (affected by flip)
            # is_top = True means top position widget
            # When not flipped: top shows Black, bottom shows White
            # When flipped: top shows White, bottom shows Black
            if not self.board_flipped:
                player_at_top = "Black" if self.is_top else "White"
                show_white_pieces = self.is_top  # Top shows white pieces captured by black
            else:
                player_at_top = "White" if self.is_top else "Black"
                show_white_pieces = not self.is_top  # Flip is reversed
            
            self.player_label.setText(f"{player_at_top}:")
            
            # Starting piece counts
            starting_white = {'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1}
            starting_black = {'p': 8, 'n': 2, 'b': 2, 'r': 2, 'q': 1}
            
            # Current piece counts
            current_white = {}
            current_black = {}
            
            for piece in board.piece_map().values():
                symbol = piece.symbol()
                if piece.color == chess.WHITE:
                    current_white[symbol.upper()] = current_white.get(symbol.upper(), 0) + 1
                else:
                    current_black[symbol.lower()] = current_black.get(symbol.lower(), 0) + 1
            
            # Calculate captured pieces
            if show_white_pieces:
                # Show white pieces (captured by opponent)
                captured_dict = {}
                for piece_type, start_count in starting_white.items():
                    current_count = current_white.get(piece_type, 0)
                    captured_count = max(0, start_count - current_count) # Ensure non-negative
                    if captured_count > 0:
                        captured_dict[piece_type] = captured_count
                piece_color = 'w'
            else:
                # Show black pieces (captured by opponent)
                captured_dict = {}
                for piece_type, start_count in starting_black.items():
                    current_count = current_black.get(piece_type, 0)
                    captured_count = max(0, start_count - current_count)
                    if captured_count > 0:
                        captured_dict[piece_type] = captured_count
                piece_color = 'b'
            
            # Clear previous layout
            while self.pieces_layout.count():
                child = self.pieces_layout.takeAt(0)
                if child:
                    widget = child.widget()
                    if widget:
                        widget.deleteLater()
            
            # Piece order for display (Pawn, Knight, Bishop, Rook, Queen)
            piece_order = ['P', 'p', 'N', 'n', 'B', 'b', 'R', 'r', 'Q', 'q']
            
            # Add pieces with counters
            has_pieces = False
            for piece_symbol in piece_order:
                if piece_symbol in captured_dict:
                    count = captured_dict[piece_symbol]
                    has_pieces = True
                    
                    # Create a container for piece + counter
                    piece_widget = self._create_piece_widget(piece_color, piece_symbol, count)
                    self.pieces_layout.addWidget(piece_widget)
            
            if not has_pieces:
                # Show empty space
                empty_label = QLabel("-")
                empty_label.setStyleSheet("color: #666666; font-size: 10px;")
                self.pieces_layout.addWidget(empty_label)
            
            self.pieces_layout.addStretch()
            
        except Exception as e:
            print(f"Error in update_captured_pieces: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_piece_widget(self, color: str, piece_type: str, count: int) -> QWidget:
        """
        Create a widget with piece icon and counter.
        
        Args:
            color: 'w' or 'b' for white/black piece
            piece_type: 'P', 'N', 'B', 'R', 'Q', etc.
            count: Number of captured pieces of this type
            
        Returns:
            QWidget containing the piece icon and counter
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Piece icon
        piece_key = f"{color}{piece_type.upper()}"
        if piece_key in self.pieces:
            piece_label = QLabel()
            pixmap = self.pieces[piece_key].scaledToHeight(
                self.PIECE_SIZE,
                mode=Qt.TransformationMode.SmoothTransformation
            )
            piece_label.setPixmap(pixmap)
            piece_label.setFixedSize(self.PIECE_SIZE, self.PIECE_SIZE)
            layout.addWidget(piece_label)
        
        # Counter (if count > 1)
        if count > 1:
            counter_label = QLabel(str(count))
            counter_label.setStyleSheet(
                "color: #FFD700; font-weight: bold; font-size: 10px; "
                "background-color: rgba(0, 0, 0, 150); border-radius: 2px; "
                "padding: 1px 2px;"
            )
            counter_label.setFixedSize(14, 14)
            counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(counter_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        container.setFixedHeight(self.PIECE_SIZE)
        return container
