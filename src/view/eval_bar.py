from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import pyqtProperty, QPropertyAnimation, QEasingCurve, pyqtSlot, Qt

class EvalBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(24) # Slightly wider for better visibility
        self._percent_black = 0.5 # Internal float for animation
        self.target_percent = 0.5
        self.eval_value = 0.0
        self.is_mate = False
        self.mate_in = 0
        self.result_text = ""
        
        # Animation
        self.anim = QPropertyAnimation(self, b"percent_black")
        self.anim.setDuration(500) # 500ms smooth transition
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    @pyqtProperty(float)
    def percent_black(self):
        return self._percent_black
        
    @percent_black.setter
    def percent_black(self, val):
        self._percent_black = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        h = rect.height()
        w = rect.width()

        y_split = int(h * self._percent_black)
        
        # Draw White part (Top)
        white_rect = QRectF(0, 0, w, y_split)
        painter.fillRect(white_rect, QColor("#e0e0e0"))
        
        # Draw Black part (Bottom)
        black_rect = QRectF(0, y_split, w, h - y_split)
        painter.fillRect(black_rect, QColor("#333333"))
        
        # Draw Value Text
        # If Black Winning (> 50% black height), put text in Black area (at top of it?)
        # Actually standard:
        # If White winning (Top is small), put text in bottom?
        # Let's simple put text based on who is winning.
        
        text = ""
        if self.is_mate:
            text = f"M{abs(self.mate_in)}"
        else:
            text = f"{self.eval_value:.1f}"

        font = painter.font()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        # Determine better position for contrast
        # If eval > 0 (White winning), bar is mostly White (Top part small... wait. 
        # White winning -> val > 0 -> percent_black < 0.5. 
        # So White Part (Top) is LARGER.
        # Wait. formula: percent_black = 0.5 - (val / 10).
        # if val = +5, percent_black = 0. White Part is Top...? 
        # No, y_split = h * percent_black.
        # if percent_black is 0, y_split is 0.
        # drawing White Part from 0 to y_split... so 0 height?
        # Ah! 'White part (Top)' I wrote.
        # correct logic:
        # 0 to y_split is WHITE's domain (or black's?).
        # Usually TOP is BLACK in bar? Or Bottom?
        # Standard: White at Bottom, Black at Top? Or White Top?
        # Let's stick to my colors:
        # Rect 1 (0 to y): "#e0e0e0" (White).
        # Rect 2 (y to h): "#333333" (Black).
        # If val=+5, percent_black=0. y_split=0.
        # Rect1: 0 height. Rect2: Full height (Black). 
        # So Positive Eval = MORE BLACK VISIBLE? That's wrong for "White Advantage".
        # If White has advantage, White bar should be BIG.
        # So if Eval +5, we want Full White.
        # So Rect1 (White) should be Full.
        # So y_split should be h.
        # So percent_white = ... 
        
        # Let's fix the math first!
        # target = 0.5 - (val / 10.0)
        # If val = +5 -> target = 0.
        # y_split = 0.
        # Rect1 (White) = 0.
        # So +5 leads to Full Black. This is REVERSED.
        
        # FIX:
        # If val = +5 (White Adv), we want White Bar (Rect1) to be Full.
        # So y_split -> h.
        # So percent (for y_split) should be 1.0.
        # target = 0.5 + (val / 10.0) ?
        # +5 -> 1.0.
        # -5 -> 0.0.
        # y_split = h * 1.0 = h.
        # Rect1 (White) from 0 to h. Correct.
        pass

    def set_eval(self, score_str):
        try:
            # Handle Game Over
            if score_str == "1-0":
                 target = 1.0 # Full White
                 self.is_mate = False 
                 self.result_text = "1-0"
            elif score_str == "0-1":
                 target = 0.0 # Full Black
                 self.is_mate = False
                 self.result_text = "0-1"
                 
            # Handle Mate (e.g. "M3", "+M3", "#-3")
            elif "M" in score_str or "#" in score_str:
                self.is_mate = True
                self.result_text = ""
                clean_str = score_str.replace("M", "").replace("#", "")
                self.mate_in = int(clean_str)
                
                # +Mate -> 1.0 (Full White)
                # -Mate -> 0.0 (Full Black)
                if self.mate_in > 0: target = 1.0
                else: target = 0.0
            else:
                self.is_mate = False
                self.result_text = ""
                val = float(score_str)
                self.eval_value = val
                val = max(-5.0, min(5.0, val))
                target = 0.5 + (val / 10.0)
        except ValueError:
            target = 0.5

        self.anim.stop()
        self.anim.setStartValue(self._percent_black)
        self.anim.setEndValue(target)
        self.anim.start()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        h = rect.height()
        w = rect.width()

        # _percent_black here actually represents "Percent White" based on my logic above
        # distinct name would help, but let's use the value.
        pct = self._percent_black 
        y_split = int(h * (1.0 - pct)) # Qt coords: 0 is top.
        # We want White at Bottom usually? Or White at Top?
        # Standard Chess.com: White is Bottom.
        # So if Full White (pct=1.0), White Rect should be Full.
        # If White is Bottom, White Rect is (y_split to h).
        # And Black Rect is (0 to y_split).
        
        # Let's implement White at Bottom.
        # pct = 1.0 (White Adv). y_split = 0.
        # Black Rect (0 to 0) -> Empty.
        # White Rect (0 to h) -> Full.
        
        # Black Part (Top)
        painter.fillRect(0, 0, w, y_split, QColor("#333333"))
        
        # White Part (Bottom)
        painter.fillRect(0, y_split, w, h - y_split, QColor("#e0e0e0"))
        
        # Text
        text = ""
        if self.result_text:
             text = self.result_text
        elif self.is_mate:
            text = f"M{abs(self.mate_in)}"
        else:
            text = f"{abs(self.eval_value):.1f}"
            
        from PyQt6.QtGui import QFont
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        painter.setFont(font)
        
        # Position text
        # If White Adv (>0.5), text in Black part (Top) to be visible?
        # Or just put it at bottom/top edge.
        
        if pct > 0.5: # White Advantage (White bar bigger, at bottom)
            # Put text in White part (Bottom), but clear, use Black text
            painter.setPen(QColor("#333333"))
            painter.drawText(rect.adjusted(0, 0, 0, -5), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, text)
        else: # Black Advantage (Black bar bigger, at top)
             # Put text in Black part (Top), use White text
             painter.setPen(QColor("#e0e0e0"))
             painter.drawText(rect.adjusted(0, 5, 0, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, text)
