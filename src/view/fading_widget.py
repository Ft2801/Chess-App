from PyQt6.QtWidgets import (
    QWidget, QStackedWidget, QStackedLayout, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QAbstractAnimation

class FadingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fade_anim = None
        # We use Normal stacking mode now because the overlay handles the transition visually
        if self.layout() is not None and isinstance(self.layout(), QStackedLayout):
             self.layout().setStackingMode(QStackedLayout.StackingMode.StackOne)

        # Overlay Widget for Fading
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: #2b2b2b;") # Match Main Window Background
        
        # Add Logo to Overlay
        from PyQt6.QtWidgets import QLabel, QVBoxLayout
        layout = QVBoxLayout(self.overlay)
        self.logo_label = QLabel()
        from PyQt6.QtGui import QPixmap
        # Assuming assets/logo.png exists
        self.logo_pixmap = QPixmap("assets/logo.png")
        if not self.logo_pixmap.isNull():
            # Initial Scale
            self.logo_label.setPixmap(self.logo_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.overlay.hide()
        
        # Effect for Opacity
        self.effect = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self.effect)
        
        # Animations
        self.anim_fade_in = QPropertyAnimation(self.effect, b"opacity")
        self.anim_fade_in.setDuration(400) 
        self.anim_fade_in.setStartValue(0)
        self.anim_fade_in.setEndValue(1)
        self.anim_fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.anim_fade_out = QPropertyAnimation(self.effect, b"opacity")
        self.anim_fade_out.setDuration(400)
        self.anim_fade_out.setStartValue(1)
        self.anim_fade_out.setEndValue(0)
        self.anim_fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.anim_fade_in.finished.connect(self.on_fade_in_finished)
        self.anim_fade_out.finished.connect(self.on_fade_out_finished)
        
        self.pending_index = -1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.size())
        
        # Resize Logo to 50% of height
        if hasattr(self, 'logo_label'):
            # Reload pixmap to scale from original if possible, or just scale the one we have?
            # Better to store original pixmap.
            if hasattr(self, 'logo_pixmap') and not self.logo_pixmap.isNull():
                target_h = int(self.height() * 0.5)
                scaled = self.logo_pixmap.scaledToHeight(target_h, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled)

    def setCurrentIndex(self, index):
        if self.currentIndex() == index:
            return
            
        self.pending_index = index
        
        # 1. Start Fade In (Show Overlay)
        self.overlay.resize(self.size())
        self.overlay.raise_()
        self.overlay.show()
        self.anim_fade_in.start()

    def on_fade_in_finished(self):
        # 2. Switch Wrapper
        if self.pending_index != -1:
            super().setCurrentIndex(self.pending_index)
            self.pending_index = -1
            
        # Ensure overlay stays on top of the new widget
        self.overlay.raise_()
            
        # 3. Pause for 500ms at full opacity, then Fade Out
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.anim_fade_out.start)

    def on_fade_out_finished(self):
        # 4. Hide Overlay
        self.overlay.hide()
