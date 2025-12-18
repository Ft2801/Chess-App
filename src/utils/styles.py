
class Styles:
    DARK_THEME = """
    QMainWindow {
        background-color: #2b2b2b;
        color: #f0f0f0;
    }
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
        font-family: 'Segoe UI', sans-serif;
    }
    QPushButton {
        background-color: #3c3f41;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 6px 12px;
        color: #ddd;
    }
    QPushButton:hover {
        background-color: #4c5052;
    }
    QPushButton:pressed {
        background-color: #252526;
    }
    QLabel {
        color: #f0f0f0;
    }
    QTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #3e3e42;
        color: #d4d4d4;
    }
    QCheckBox {
        background: transparent;
        color: #f0f0f0;
    }
    QCheckBox::indicator {
        border: 1px solid #555;
        border-radius: 2px;
        background: #1e1e1e;
        width: 14px;
        height: 14px;
    }
    QCheckBox::indicator:checked {
        background-color: #00B4D8;
        border: 1px solid #00B4D8;
    }
    /* Simple colored box for checked state if no image */
    QCheckBox::indicator:checked:hover {
        background-color: #0093B2;
    }
    QRadioButton {
        background: transparent;
        color: #f0f0f0;
    }
    QRadioButton::indicator {
        border: 1px solid #555;
        border-radius: 7px;
        background: #1e1e1e;
        width: 14px;
        height: 14px;
    }
    QRadioButton::indicator:checked {
        background-color: #00B4D8;
        border: 1px solid #00B4D8;
    }
    """
    
    # Board Colors
    LIGHT_SQUARE = "#D18B47"
    DARK_SQUARE = "#FFCE9E"
    
    # Custom Theme ("Dark Modern" request)
    # Let's override squares with something cooler for "modern"
    LIGHT_SQUARE_MODERN = "#EEEED2"
    DARK_SQUARE_MODERN = "#769656" # Typical chess.com green style

    THEMES = {
        "Green": {"light": "#EEEED2", "dark": "#769656"},
        "Blue":  {"light": "#E1E1E1", "dark": "#4da1e8"}, # Lichess-like Blue
        "Brown": {"light": "#F0D9B5", "dark": "#B58863"}, # Classic Wood
        "Gray":  {"light": "#E0E0E0", "dark": "#808080"}, # Monochrome
    }
    
    # Highlight Colors
    HIGHLIGHT_LAST_MOVE = "#BBCB2B"  # Yellow-ish transparent usually
    HIGHLIGHT_SELECTED = "#BACA44"
    HIGHLIGHT_LEGAL = "#8014551E" # ~50% opacity Green
    HIGHLIGHT_CAPTURE = "#80C83232" # ~50% opacity Red
