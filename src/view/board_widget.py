import chess
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap, QPen, QBrush
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPoint, QLine
import math

from src.utils.styles import Styles
from src.view.promotion_dialog import PromotionDialog

class BoardWidget(QWidget):
    move_made = pyqtSignal(chess.Move)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board() # Internal state for display, sync with model
        self.flipped = False
        self.square_size = 64
        self.pieces = {}
        self.theme_name = "Green"
        self._load_pieces()
        
        # Interaction state
        self.selected_square = None
        self.is_dragging = False
        self.dragged_piece = None # dict with 'piece', 'pos': QPoint (pixel)
        self.potential_moves = [] # list of chess.Move
        self.potential_moves = [] # list of chess.Move
        self.best_move = None
        self.current_annotation = None # {'square': sq, 'type': str}
        self.show_arrows = False # Default disabled as requested
        
        # Promotion dialog
        self.promotion_dialog = PromotionDialog(self)
        self.promotion_dialog.piece_selected.connect(self.on_promotion_selected)
        self.pending_promotion_move = None  # Store the move awaiting promotion choice
        
        # Annotation system (arrows and highlights)
        self.arrows = []  # List of {'from': square, 'to': square, 'color': QColor}
        self.highlighted_squares = {}  # Dict of {square: color_name}
        self.right_click_start = None  # Track right-click drag start
        self.right_click_modifier = None  # Track which modifier was pressed
        
        # Color scheme for annotations
        self.annotation_colors = {
            'default': QColor(255, 255, 0, 60),      # Yellow
            'shift': QColor(255, 0, 0, 60),          # Red
            'ctrl': QColor(0, 0, 255, 60),           # Blue
            'alt': QColor(0, 255, 0, 60),            # Green
        }
        
        self.arrow_colors = {
            'default': QColor(100, 200, 100, 180),   # Green
            'shift': QColor(200, 100, 100, 180),     # Red-ish
            'ctrl': QColor(100, 100, 200, 180),      # Blue-ish
            'alt': QColor(100, 200, 150, 180),       # Light green-ish
        }
        
    def set_theme(self, theme_name):
        if theme_name in Styles.THEMES:
            self.theme_name = theme_name
            self.update()

    def _load_pieces(self):
        # Load PNGs from assets/pieces
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

    def update_board(self, board: chess.Board):
        self.board = board
        self.best_move = None # Clear arrow on board update (new position)
        # Clear annotations when board changes
        self.arrows = []
        self.highlighted_squares = {}
        self.update()

    def set_flipped(self, flipped):
        self.flipped = flipped
        self.update()
    
    def clear_annotations(self):
        """Clear all arrows and highlighted squares."""
        self.arrows = []
        self.highlighted_squares = {}
        self.update()
    
    def _get_modifier_key(self, event) -> str:
        """Determine which modifier key is pressed."""
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            return 'shift'
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            return 'ctrl'
        elif modifiers & Qt.KeyboardModifier.AltModifier:
            return 'alt'
        return 'default'

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Explicitly set font to avoid potential "size <= 0" error from Qt internals
        # Explicitly set font to avoid potential "size <= 0" error from Qt internals
        from PyQt6.QtGui import QFont
        f = QFont("Segoe UI", 12)
        painter.setFont(f)

        # Calculate square size
        min_dim = min(self.width(), self.height())
        self.square_size = min_dim / 8
        
        # Offset to center board
        x_offset = (self.width() - min_dim) / 2
        y_offset = (self.height() - min_dim) / 2
        
        painter.translate(x_offset, y_offset)

        # Get Theme Colors
        theme = Styles.THEMES.get(self.theme_name, Styles.THEMES["Green"])
        color_light = QColor(theme["light"])
        color_dark = QColor(theme["dark"])

        # Draw Squares
        for r in range(8):
            for c in range(8):
                if self.flipped:
                    rank = r
                    file = 7 - c
                else:
                    rank = 7 - r
                    file = c
                
                is_light = (rank + file) % 2 != 0
                color = color_light if is_light else color_dark
                
                # Highlight Selected
                square_idx = chess.square(file, rank)
                if self.selected_square == square_idx:
                    color = QColor(Styles.HIGHLIGHT_SELECTED)
                # Highlight Last Move
                elif len(self.board.move_stack) > 0:
                    last_move = self.board.peek()
                    if square_idx == last_move.from_square or square_idx == last_move.to_square:
                         color = QColor(Styles.HIGHLIGHT_LAST_MOVE)

                painter.fillRect(QRectF(c * self.square_size, r * self.square_size, self.square_size, self.square_size), color)
                
                # Draw Coordinates (on edges)
                if file == 0 and not self.flipped: # Draw ranks on left
                     painter.setPen(Qt.GlobalColor.black if is_light else Qt.GlobalColor.white)
                     painter.drawText(QRectF(c * self.square_size + 2, r * self.square_size + 2, 25, 25), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, str(rank + 1))
                if rank == 0 and not self.flipped: # Draw files on bottom
                     painter.setPen(Qt.GlobalColor.black if is_light else Qt.GlobalColor.white)
                     painter.drawText(QRectF(c * self.square_size + self.square_size - 22, r * self.square_size + self.square_size - 22, 20, 20), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, chess.FILE_NAMES[file])

        # Draw Highlighted Squares
        for square, color_name in self.highlighted_squares.items():
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            
            if self.flipped:
                c = 7 - file
                r = rank
            else:
                c = file
                r = 7 - rank
            
            highlight_color = self.annotation_colors.get(color_name, self.annotation_colors['default'])
            painter.fillRect(QRectF(c * self.square_size, r * self.square_size, self.square_size, self.square_size), highlight_color)

        # Draw Arrows
        for arrow in self.arrows:
            self.draw_custom_arrow(painter, arrow['from'], arrow['to'], arrow.get('color', QColor(100, 200, 100, 180)))



        # Draw Legal Move Hints
        if self.selected_square is not None:
             for move in self.potential_moves:
                 to_sq = move.to_square
                 
                 # Map sq to r/c
                 to_file = chess.square_file(to_sq)
                 to_rank = chess.square_rank(to_sq)
                 
                 if self.flipped:
                     c_draw = 7 - to_file
                     r_draw = to_rank
                 else:
                     c_draw = to_file
                     r_draw = 7 - to_rank

                 center_x = c_draw * self.square_size + self.square_size / 2
                 center_y = r_draw * self.square_size + self.square_size / 2
                 
                 # if capture
                 if self.board.piece_at(to_sq):
                     # Draw Ring
                     painter.setPen(QPen(QColor(Styles.HIGHLIGHT_CAPTURE), 4))
                     painter.setBrush(Qt.BrushStyle.NoBrush)
                     painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(self.square_size/2.2), int(self.square_size/2.2))
                 else:
                     # Draw Dot
                     painter.setPen(Qt.PenStyle.NoPen)
                     painter.setBrush(QColor(0, 0, 0, 40)) # Semi-transparent black dot
                     painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(self.square_size/6), int(self.square_size/6))


        # Draw Best Move Arrow
        if self.show_arrows and self.best_move:
            self.draw_arrow(painter, self.best_move)

        # Draw Pieces (After Arrow, so arrow is behind pieces? Or On Top?)
        # User requested "delicate", usually arrows are On Top or slightly transparent.
        # But if it blocks drag/drop, it might be interaction logic.
        # Draw Pieces LAST to ensure they are on top of everything except drag.
        piece_map = self.board.piece_map()
        for square, piece in piece_map.items():
            # Skip dragged piece (draw it last at mouse pos)
            if self.is_dragging and square == self.selected_square:
                continue

            file = chess.square_file(square)
            rank = chess.square_rank(square)
            
            if self.flipped:
                c_draw = 7 - file
                r_draw = rank
            else:
                c_draw = file
                r_draw = 7 - rank
                
            p_key = f"{'w' if piece.color else 'b'}{piece.symbol().upper()}"
            if p_key in self.pieces:
                pix = self.pieces[p_key]
                target_rect = QRectF(c_draw * self.square_size, r_draw * self.square_size, self.square_size, self.square_size)
                # Padding slightly
                margin = self.square_size * 0.1
                painter.drawPixmap(target_rect.adjusted(margin, margin, -margin, -margin).toRect(), pix)

        # Draw Dragged Piece
        if self.is_dragging and self.dragged_piece:
             pix = self.dragged_piece['pixmap']
             pos = self.mapFromGlobal(self.cursor().pos())
             # Adjust for painter translate (ensure int for QPoint)
             pos.setX(int(pos.x() - x_offset))
             pos.setY(int(pos.y() - y_offset))
             
             # Center piece on mouse
             painter.drawPixmap(int(pos.x() - self.square_size/2), int(pos.y() - self.square_size/2), 
                                int(self.square_size), int(self.square_size), pix)

        # Draw Classification Annotation
        self.draw_annotation(painter)

    def set_best_move(self, move):
        self.best_move = move
        self.update()

    def draw_custom_arrow(self, painter, from_square: int, to_square: int, color: QColor):
        """Draw an arrow from one square to another."""
        s_file = chess.square_file(from_square)
        s_rank = chess.square_rank(from_square)
        e_file = chess.square_file(to_square)
        e_rank = chess.square_rank(to_square)
        
        if self.flipped:
            x1 = (7 - s_file) * self.square_size + self.square_size / 2
            y1 = s_rank * self.square_size + self.square_size / 2
            x2 = (7 - e_file) * self.square_size + self.square_size / 2
            y2 = e_rank * self.square_size + self.square_size / 2
        else:
            x1 = s_file * self.square_size + self.square_size / 2
            y1 = (7 - s_rank) * self.square_size + self.square_size / 2
            x2 = e_file * self.square_size + self.square_size / 2
            y2 = (7 - e_rank) * self.square_size + self.square_size / 2
        
        dx = x2 - x1
        dy = y2 - y1
        length = (dx**2 + dy**2)**0.5
        
        head_len = self.square_size * 0.4
        
        pen = QPen(color)
        pen.setWidth(int(self.square_size * 0.15))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw line
        if length > head_len:
            ratio = (length - head_len + 5) / length
            x_end_line = x1 + dx * ratio
            y_end_line = y1 + dy * ratio
            painter.drawLine(int(x1), int(y1), int(x_end_line), int(y_end_line))
        else:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw head
        angle = math.atan2(dy, dx)
        p1 = QPoint(int(x2), int(y2))
        p2 = QPoint(
            int(x2 - head_len * math.cos(angle - math.pi / 5)),
            int(y2 - head_len * math.sin(angle - math.pi / 5))
        )
        p3 = QPoint(
            int(x2 - head_len * math.cos(angle + math.pi / 5)),
            int(y2 - head_len * math.sin(angle + math.pi / 5))
        )
        
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        from PyQt6.QtGui import QPolygon
        painter.drawPolygon(QPolygon([p1, p2, p3]))

    def draw_arrow(self, painter, move):

        # Coordinates
        start_sq = move.from_square
        end_sq = move.to_square
        
        s_file = chess.square_file(start_sq)
        s_rank = chess.square_rank(start_sq)
        e_file = chess.square_file(end_sq)
        e_rank = chess.square_rank(end_sq)
        
        if self.flipped:
            x1 = (7 - s_file) * self.square_size + self.square_size / 2
            y1 = s_rank * self.square_size + self.square_size / 2
            x2 = (7 - e_file) * self.square_size + self.square_size / 2
            y2 = e_rank * self.square_size + self.square_size / 2
        else:
            x1 = s_file * self.square_size + self.square_size / 2
            y1 = (7 - s_rank) * self.square_size + self.square_size / 2
            x2 = e_file * self.square_size + self.square_size / 2
            y2 = (7 - e_rank) * self.square_size + self.square_size / 2
            
        start = QPoint(int(x1), int(y1))
        end = QPoint(int(x2), int(y2))
        
        # Draw Arrow
        # Color: Standard Greenish with transparency
        c = QColor(100, 200, 100, 180) # Nice Green
        
        pen = QPen(c)
        pen.setWidth(int(self.square_size * 0.15)) # 15% width
        pen.setCapStyle(Qt.PenCapStyle.RoundCap) # Round cap for start
        painter.setPen(pen)
        
        # Shorten line so it doesn't poke through head
        # Vector math
        dx = x2 - x1
        dy = y2 - y1
        length = (dx**2 + dy**2)**0.5
        
        head_len = self.square_size * 0.4
        
        # If arrow too short, just draw line
        if length > head_len:
             ratio = (length - head_len + 5) / length
             x_end_line = x1 + dx * ratio
             y_end_line = y1 + dy * ratio
             painter.drawLine(start, QPoint(int(x_end_line), int(y_end_line)))
        else:
             painter.drawLine(start, end)
        
        # Draw Head
        import math
        angle = math.atan2(dy, dx)
        
        p1 = end
        p2 = QPoint(
            int(x2 - head_len * math.cos(angle - math.pi / 5)),
            int(y2 - head_len * math.sin(angle - math.pi / 5))
        )
        p3 = QPoint(
            int(x2 - head_len * math.cos(angle + math.pi / 5)),
            int(y2 - head_len * math.sin(angle + math.pi / 5))
        )
        
        painter.setBrush(c)
        painter.setPen(Qt.PenStyle.NoPen)
        from PyQt6.QtGui import QPolygon
        painter.drawPolygon(QPolygon([p1, p2, p3]))

    def set_annotation(self, annotation):
        """
        Set valid annotation dict: {'square': chess.Square, 'type': 'brilliant'|'blunder'|...}
        or None to clear.
        """
        self.current_annotation = annotation
        self.update()

    def draw_annotation(self, painter):
        if not self.current_annotation: return
        
        square = self.current_annotation['square']
        atype = self.current_annotation['type']
        
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        if self.flipped:
            c = 7 - file
            r = rank
        else:
            c = file
            r = 7 - rank
            
        # Draw top-right corner of square
        size = self.square_size * 0.45
        x = c * self.square_size + self.square_size - size
        y = r * self.square_size
        
        rect = QRectF(x, y, size, size)
        
        # Load Icon
        import os
        
        # Map classifier types to available filenames
        # Files: best, blunder, brilliant, critical, excellent, forced, inaccuracy, mistake, okay
        icon_map = {
            'great': 'critical',  # "!" usually
            'good': 'okay',       # "Good" -> "Okay"
            'book': 'best',       # Book moves are best
        }
        
        filename = icon_map.get(atype, atype)
        icon_path = f"assets/classifications/{filename}.png"
        
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            painter.drawPixmap(rect.toRect(), pix)
        else:
            # Fallback: Colored Circle (Retained for safety)
            # ...
            # Fallback: Colored Circle
            colors = {
                'brilliant': "#00BFFF",   'great': "#1E90FF",
                'best': "#32CD32",        'excellent': "#90EE90",
                'good': "#006400",        'inaccuracy': "#F4D03F",
                'mistake': "#E67E22",     'blunder': "#E74C3C",
                'forced': "#8E44AD"
            }
            bg_color = QColor(colors.get(atype, "#888888"))
            painter.setBrush(QBrush(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)

    def mousePressEvent(self, event):
        pos = event.pos()
        # Calculate square
        min_dim = min(self.width(), self.height())
        x_offset = (self.width() - min_dim) / 2
        y_offset = (self.height() - min_dim) / 2
        
        rel_x = pos.x() - x_offset
        rel_y = pos.y() - y_offset
        
        if rel_x < 0 or rel_y < 0 or rel_x > min_dim or rel_y > min_dim:
            return # Clicked outside board area
            
        col = int(rel_x / self.square_size)
        row = int(rel_y / self.square_size)
        
        if self.flipped:
             file = 7 - col
             rank = row
        else:
             file = col
             rank = 7 - row
             
        square = chess.square(file, rank)
        
        # Right Click: Highlight or start arrow
        if event.button() == Qt.MouseButton.RightButton:
            # Get the modifier key
            modifier = self._get_modifier_key(event)
            
            # Toggle highlight on this square
            if square in self.highlighted_squares:
                self.highlighted_squares.pop(square)
            else:
                self.highlighted_squares[square] = modifier
            
            # Also start tracking for arrow
            self.right_click_start = square
            self.right_click_modifier = modifier
            self.update()
            return
        
        # Left Click: Normal gameplay
        if event.button() == Qt.MouseButton.LeftButton:
            piece = self.board.piece_at(square)
            
            # Click logic
            if self.selected_square is not None:
                # Hide promotion dialog if visible
                self.promotion_dialog.hide()
                
                # Attempt move
                move = chess.Move(self.selected_square, square)
                
                # Check for promotion
                p = self.board.piece_at(self.selected_square)
                if p and p.piece_type == chess.PAWN:
                    if (p.color == chess.WHITE and rank == 7) or (p.color == chess.BLACK and rank == 0):
                        # Promotion move - show dialog
                        self.show_promotion_dialog(self.selected_square, square, p.color)
                        return

                if move in self.board.legal_moves:
                    self.move_made.emit(move)
                    self.selected_square = None
                    self.potential_moves = []
                    self.best_move = None # Clear arrow on move
                    self.update()
                    return
                # If not legal move, maybe selecting a different piece?
            
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.potential_moves = [m for m in self.board.legal_moves if m.from_square == square]
                self.is_dragging = True
                
                p_key = f"{'w' if piece.color else 'b'}{piece.symbol().upper()}"
                self.dragged_piece = {'pixmap': self.pieces.get(p_key)}
                
                self.update()
            else:
                # Hide promotion dialog when clicking elsewhere
                self.promotion_dialog.hide()
                
                self.selected_square = None # Clicked empty square or enemy piece (without valid capture)
                self.potential_moves = []
                self.update()

                
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.update()
            
    def mouseReleaseEvent(self, event):
        # Right Click Release: Arrow drag completion
        if event.button() == Qt.MouseButton.RightButton and self.right_click_start is not None:
            pos = event.pos()
            min_dim = min(self.width(), self.height())
            x_offset = (self.width() - min_dim) / 2
            y_offset = (self.height() - min_dim) / 2
            
            rel_x = pos.x() - x_offset
            rel_y = pos.y() - y_offset
            
            if 0 <= rel_x <= min_dim and 0 <= rel_y <= min_dim:
                col = int(rel_x / self.square_size)
                row = int(rel_y / self.square_size)
                
                if self.flipped:
                     file = 7 - col
                     rank = row
                else:
                     file = col
                     rank = 7 - row
                
                end_square = chess.square(file, rank)
                
                # If dragged to different square, add arrow
                if end_square != self.right_click_start:
                    # Check if arrow already exists and remove it (toggle)
                    arrow_exists = False
                    for arrow in self.arrows:
                        if arrow['from'] == self.right_click_start and arrow['to'] == end_square:
                            self.arrows.remove(arrow)
                            arrow_exists = True
                            break
                    
                    # If arrow didn't exist, add it
                    if not arrow_exists:
                        arrow_color = self.arrow_colors.get(self.right_click_modifier, self.arrow_colors['default'])
                        self.arrows.append({
                            'from': self.right_click_start,
                            'to': end_square,
                            'color': arrow_color
                        })
            
            self.right_click_start = None
            self.right_click_modifier = None
            self.update()
            return
        
        # Left Click Release: Piece drag completion
        if self.is_dragging:
            self.is_dragging = False
            self.dragged_piece = None
            
            # Check drop
            pos = event.pos()
            min_dim = min(self.width(), self.height())
            x_offset = (self.width() - min_dim) / 2
            y_offset = (self.height() - min_dim) / 2
            
            rel_x = pos.x() - x_offset
            rel_y = pos.y() - y_offset
            
            if 0 <= rel_x <= min_dim and 0 <= rel_y <= min_dim:
                col = int(rel_x / self.square_size)
                row = int(rel_y / self.square_size)
                
                if self.flipped:
                     file = 7 - col
                     rank = row
                else:
                     file = col
                     rank = 7 - row
                
                target_sq = chess.square(file, rank)
                if target_sq != self.selected_square:
                    # Attempt move
                    p = self.board.piece_at(self.selected_square)
                    
                    # Promotion check
                    if p and p.piece_type == chess.PAWN:
                         if (p.color == chess.WHITE and rank == 7) or (p.color == chess.BLACK and rank == 0):
                             # Promotion move - show dialog
                             self.show_promotion_dialog(self.selected_square, target_sq, p.color)
                             return
                    
                    # Regular move
                    move = chess.Move(self.selected_square, target_sq)
                    if move in self.board.legal_moves:
                        self.move_made.emit(move)
                        self.selected_square = None
                        self.potential_moves = []
            
            self.update()

    def show_promotion_dialog(self, from_square: int, to_square: int, color: bool):
        """
        Show the promotion dialog on the promotion square.
        Dialog stays within the board widget bounds.
        
        Args:
            from_square: Source square of the pawn
            to_square: Destination square (promotion square)
            color: Color of the pawn (chess.WHITE or chess.BLACK)
        """
        # Store the move info
        self.pending_promotion_move = (from_square, to_square)
        
        # Position the dialog on the promotion square
        file = chess.square_file(to_square)
        rank = chess.square_rank(to_square)
        
        # Convert to screen coordinates
        if self.flipped:
            col_draw = 7 - file
            row_draw = rank
        else:
            col_draw = file
            row_draw = 7 - rank
        
        # Calculate square dimensions and position
        min_dim = min(self.width(), self.height())
        square_size = min_dim / 8
        x_offset = (self.width() - min_dim) / 2
        y_offset = (self.height() - min_dim) / 2
        
        # Dialog dimensions
        dialog_width = 54
        dialog_height = 212
        
        # Position dialog centered on the square
        dialog_x = int(x_offset + col_draw * square_size + square_size / 2 - dialog_width / 2)
        dialog_y = int(y_offset + row_draw * square_size + square_size / 2 - dialog_height / 2)
        
        # Keep dialog within board bounds
        min_x = int(x_offset)
        max_x = int(x_offset + min_dim - dialog_width)
        min_y = int(y_offset)
        max_y = int(y_offset + min_dim - dialog_height)
        
        dialog_x = max(min_x, min(dialog_x, max_x))
        dialog_y = max(min_y, min(dialog_y, max_y))
        
        self.promotion_dialog.move(dialog_x, dialog_y)
        self.promotion_dialog.show_for_color(color)
    
    def on_promotion_selected(self, piece_type: chess.PieceType):
        """
        Handle the promotion piece selection from the dialog.
        
        Args:
            piece_type: The chess.PieceType selected (KNIGHT, BISHOP, ROOK, QUEEN)
        """
        if self.pending_promotion_move:
            from_square, to_square = self.pending_promotion_move
            move = chess.Move(from_square, to_square, promotion=piece_type)
            
            if move in self.board.legal_moves:
                self.move_made.emit(move)
            
            # Clean up
            self.selected_square = None
            self.potential_moves = []
            self.pending_promotion_move = None
            self.update()    
    def hide_promotion_dialog(self):
        """Hide the promotion dialog if it's visible."""
        self.promotion_dialog.hide()
        self.pending_promotion_move = None