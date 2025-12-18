import sys
import time
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QIcon
from src.controller.game_controller import GameController

def main():
    app = QApplication(sys.argv)
    
    # Set App Icon
    app.setWindowIcon(QIcon("assets/logo.png"))
    
    # Custom Loading Screen
    from src.view.loading_screen import LoadingScreen
    splash = LoadingScreen("assets/logo.png")
    splash.show()
    
    # Process events to render splash immediately
    app.processEvents()
    
    # Simulate Loading Steps
    steps = [
        (10, "Initializing Core Systems..."),
        (30, "Loading Engine..."),
        (50, "Loading Assets..."),
        (70, "Preparing User Interface..."),
        (90, "Starting Application..."),
        (100, "Ready!")
    ]
    
    for val, msg in steps:
        splash.update_progress(val, msg)
        time.sleep(0.3) # Simulate work
    
    # Initialize Controller (which initializes Model and View)
    # The controller's __init__ shows the main window.
    controller = GameController()
    
    # Close splash when main window is ready
    splash.finish(controller.view)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
