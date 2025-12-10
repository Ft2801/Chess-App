import sys
import time
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QIcon
from src.controller.game_controller import GameController

def main():
    app = QApplication(sys.argv)
    
    # Set App Icon
    app.setWindowIcon(QIcon("assets/logo.png"))
    
    # Splash Screen
    splash_pix = QPixmap("assets/logo.png")
    # Optional: Scale if too big? 
    # splash_pix = splash_pix.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio)
    
    splash = QSplashScreen(splash_pix)
    splash.show()
    
    # Process events to render splash immediately
    app.processEvents()
    
    # Wait 2 seconds
    time.sleep(1)
    
    # Initialize Controller (which initializes Model and View)
    # The controller's __init__ shows the main window.
    controller = GameController()
    
    # Close splash when main window is ready
    splash.finish(controller.view)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
