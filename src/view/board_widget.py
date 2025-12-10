import chess
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap, QPen, QBrush
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPoint

from src.utils.styles import Styles

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
        self.update()

    def set_flipped(self, flipped):
        self.flipped = flipped
        self.update()

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
        if event.button() == Qt.MouseButton.LeftButton:
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
            piece = self.board.piece_at(square)
            
            # Click logic
            if self.selected_square is not None:
                # Attempt move
                move = chess.Move(self.selected_square, square)
                
                # Check for promotion (auto-promote to Queen for simplicity in MVP, or try all promos)
                # Actually, python-chess moves usually need promotion flag.
                # If pawn moves to last rank, it's a promotion.
                p = self.board.piece_at(self.selected_square)
                if p and p.piece_type == chess.PAWN:
                    if (p.color == chess.WHITE and rank == 7) or (p.color == chess.BLACK and rank == 0):
                        move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

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
                self.selected_square = None # Clicked empty square or enemy piece (without valid capture)
                self.potential_moves = []
                self.update()

                
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.update()
            
    def mouseReleaseEvent(self, event):
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
                    move = chess.Move(self.selected_square, target_sq)
                    
                    # Promotion check
                    p = self.board.piece_at(self.selected_square)
                    if p and p.piece_type == chess.PAWN:
                         if (p.color == chess.WHITE and rank == 7) or (p.color == chess.BLACK and rank == 0):
                             move = chess.Move(self.selected_square, target_sq, promotion=chess.QUEEN)

                    if move in self.board.legal_moves:
                        self.move_made.emit(move)
                        self.selected_square = None
                        self.potential_moves = []
            
            self.update()

