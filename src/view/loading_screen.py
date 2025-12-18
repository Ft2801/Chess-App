from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout,  QWidget
from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QFont, QPalette
from PyQt6.QtCore import Qt

class LoadingScreen(QSplashScreen):
    def __init__(self, pixmap_path):
        # Load pixmap
        self.original_pixmap = QPixmap(pixmap_path)
        # We will draw on a copy of the pixmap to add the gradient
        self.final_pixmap = self.original_pixmap.copy()
        
        # Apply Gradient Overlay directly to the pixmap (or we can do it in paintEvent)
        # Doing it once here is efficient if the image doesn't resize.
        self.apply_gradient()
        
        super().__init__(self.final_pixmap)
        
        # UI Setup
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        
        # Layout container to hold progress bar at bottom
        # Since QSplashScreen is a QWidget, we can use layouts, 
        # but usually it's just a pixmap. 
        # To add widgets, we need to be careful with positioning.
        
        # Calculate dimensions
        w = self.final_pixmap.width()
        h = self.final_pixmap.height()
        
        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, h - 60, w - 60, 20)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(30, 30, 30, 150);
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #00B4D8, stop:1 #0077B6);
                border-radius: 4px;
            }
        """)
        
        # Label
        self.status_label = QLabel("Loading...", self)
        self.status_label.setGeometry(30, h - 90, w - 60, 25)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background: transparent;")
        
    def apply_gradient(self):
        painter = QPainter(self.final_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.final_pixmap.width()
        h = self.final_pixmap.height()
        
        # Create Gradient (Transparent -> Black)
        gradient = QLinearGradient(0, h * 0.6, 0, h)
        gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 240))
        
        painter.fillRect(0, 0, w, h, gradient)
        painter.end()

    def update_progress(self, val, message):
        self.progress_bar.setValue(val)
        self.status_label.setText(message)
        # Force update to ensure repainting during main thread busy-wait
        self.repaint()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
