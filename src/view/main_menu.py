from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QComboBox, QGroupBox, QSpacerItem, QSizePolicy, QSlider, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal

class MainMenu(QWidget):
    pvp_clicked = pyqtSignal()
    pve_clicked = pyqtSignal(str, int) # color ("White"/"Black"), level (1-8)
    eve_clicked = pyqtSignal(int, int) # level_white, level_black
    theme_selected = pyqtSignal(str) # New signal
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("CHESS")
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: #f0f0f0; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Cards Container
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # === PvP Card ===
        pvp_group = self.create_group_box("Player vs Player")
        pvp_layout = QHBoxLayout(pvp_group)
        
        lbl_pvp = QLabel("Classic Match")
        lbl_pvp.setStyleSheet("font-size: 18px; color: #ccc; border: none; background: transparent;")
        lbl_pvp.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        pvp_layout.addWidget(lbl_pvp)
        
        pvp_layout.addStretch()
        
        btn_pvp = QPushButton("Start PvP")
        btn_pvp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pvp.clicked.connect(self.pvp_clicked)
        self.style_button(btn_pvp)
        pvp_layout.addWidget(btn_pvp)
        
        cards_layout.addWidget(pvp_group)
        
        # === PvE Card ===
        pve_group = self.create_group_box("Player vs Computer")
        pve_layout = QHBoxLayout(pve_group)
        
        # Settings Container
        pve_settings = QWidget()
        pve_settings.setStyleSheet("background: transparent; border: none;")
        pve_layout.addWidget(pve_settings)
        pve_settings_layout = QHBoxLayout(pve_settings)
        pve_settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # Color Selection (Toggle)
        lbl_color = QLabel("Color:")
        pve_settings_layout.addWidget(lbl_color)
        
        self.btn_group_color = QButtonGroup(self)
        self.radio_white = QRadioButton("White")
        self.radio_black = QRadioButton("Black")
        self.radio_white.setChecked(True)
        self.style_radio(self.radio_white)
        self.style_radio(self.radio_black)
        
        self.btn_group_color.addButton(self.radio_white)
        self.btn_group_color.addButton(self.radio_black)
        
        pve_settings_layout.addWidget(self.radio_white)
        pve_settings_layout.addWidget(self.radio_black)
        
        pve_settings_layout.addSpacing(20)
        
        # Level Slider
        lbl_level_txt = QLabel("Level:")
        pve_settings_layout.addWidget(lbl_level_txt)
        
        self.slider_pve_level = QSlider(Qt.Orientation.Horizontal)
        self.slider_pve_level.setRange(1, 8)
        self.slider_pve_level.setValue(1)
        self.slider_pve_level.setFixedWidth(100)
        self.style_slider(self.slider_pve_level)
        
        self.lbl_pve_val = QLabel("1")
        self.lbl_pve_val.setFixedWidth(20)
        self.lbl_pve_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.slider_pve_level.valueChanged.connect(lambda v: self.lbl_pve_val.setText(str(v)))
        
        pve_settings_layout.addWidget(self.slider_pve_level)
        pve_settings_layout.addWidget(self.lbl_pve_val)
        
        pve_layout.addStretch()
        
        btn_pve = QPushButton("Start PvE")
        btn_pve.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pve.clicked.connect(self.on_pve_clicked)
        self.style_button(btn_pve)
        pve_layout.addWidget(btn_pve)
        
        cards_layout.addWidget(pve_group)
        
        # === EvE Card ===
        eve_group = self.create_group_box("Computer vs Computer")
        eve_layout = QHBoxLayout(eve_group)
        
         # Settings Container
        eve_settings = QWidget()
        eve_settings.setStyleSheet("background: transparent; border: none;")
        eve_layout.addWidget(eve_settings)
        eve_settings_layout = QHBoxLayout(eve_settings)
        eve_settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # White Level
        eve_settings_layout.addWidget(QLabel("White Lvl:"))
        self.slider_eve_white = QSlider(Qt.Orientation.Horizontal)
        self.slider_eve_white.setRange(1, 8)
        self.slider_eve_white.setValue(1)
        self.slider_eve_white.setFixedWidth(80)
        self.style_slider(self.slider_eve_white)
        
        self.lbl_eve_w_val = QLabel("1")
        self.lbl_eve_w_val.setFixedWidth(20)
        self.slider_eve_white.valueChanged.connect(lambda v: self.lbl_eve_w_val.setText(str(v)))
        
        eve_settings_layout.addWidget(self.slider_eve_white)
        eve_settings_layout.addWidget(self.lbl_eve_w_val)
        
        eve_settings_layout.addSpacing(15)
        
        # Black Level
        eve_settings_layout.addWidget(QLabel("Black Lvl:"))
        self.slider_eve_black = QSlider(Qt.Orientation.Horizontal)
        self.slider_eve_black.setRange(1, 8)
        self.slider_eve_black.setValue(1)
        self.slider_eve_black.setFixedWidth(80)
        self.style_slider(self.slider_eve_black)
        
        self.lbl_eve_b_val = QLabel("1")
        self.lbl_eve_b_val.setFixedWidth(20)
        self.slider_eve_black.valueChanged.connect(lambda v: self.lbl_eve_b_val.setText(str(v)))
        
        eve_settings_layout.addWidget(self.slider_eve_black)
        eve_settings_layout.addWidget(self.lbl_eve_b_val)
        
        eve_layout.addStretch()
        
        btn_eve = QPushButton("Start EvE")
        btn_eve.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eve.clicked.connect(self.on_eve_clicked)
        self.style_button(btn_eve)
        eve_layout.addWidget(btn_eve)
        
        cards_layout.addWidget(eve_group)
        
        # === Theme Selection ===
        theme_group = self.create_group_box("Board Theme")
        theme_group.setFixedHeight(220) # Taller for preview
        theme_layout = QHBoxLayout(theme_group)
        
        theme_layout.addStretch() # Center alignment
        
        # Preview Widget
        self.theme_preview = ThemePreviewWidget()
        theme_layout.addWidget(self.theme_preview)
        
        # Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        lbl_theme = QLabel("Select Style:")
        controls_layout.addWidget(lbl_theme)
        
        from src.utils.styles import Styles
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(list(Styles.THEMES.keys()))
        self.combo_theme.setCurrentText("Green")
        
        # Style ComboBox
        self.combo_theme.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: #f0f0f0;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                color: #f0f0f0;
                selection-background-color: #2b5b84;
            }
        """)
        
        self.combo_theme.currentTextChanged.connect(self.on_theme_changed)
        controls_layout.addWidget(self.combo_theme)
        controls_layout.addStretch()
        
        theme_layout.addWidget(controls_widget)
        theme_layout.addStretch()
        
        cards_layout.addWidget(theme_group)
        
        layout.addLayout(cards_layout)
        

    def create_group_box(self, title):
        group = QGroupBox(title)
        group.setFixedWidth(650)
        group.setFixedHeight(110)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 24px; /* Space for title */
                background-color: #2b2b2b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: #f0f0f0;
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ccc;
                background: transparent;
                border: none;
                font-size: 14px;
            }
        """)
        return group

    def style_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b5b84;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a7cae;
            }
            QPushButton:pressed {
                background-color: #1f4260;
            }
        """)

    def style_radio(self, radio):
         # Removed override to use global stylesheet
         pass

    def style_slider(self, slider):
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #3e3e3e;
                height: 6px;
                background: #202020;
                margin: 0px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4a90e2;
                border: 1px solid #4a90e2;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #5aa0f2;
            }
        """)

    def on_pve_clicked(self):
        color = "White" if self.radio_white.isChecked() else "Black"
        level = self.slider_pve_level.value()
        self.pve_clicked.emit(color, level)

    def on_eve_clicked(self):
        w_level = self.slider_eve_white.value()
        b_level = self.slider_eve_black.value()
        self.eve_clicked.emit(w_level, b_level)

    def on_theme_changed(self, theme_name):
        self.theme_preview.set_theme(theme_name)
        self.theme_selected.emit(theme_name)

class ThemePreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(150, 150)
        self.theme_name = "Green"
        self.wn_pixmap = None
        self.bn_pixmap = None
        self._load_assets()

    def _load_assets(self):
        from PyQt6.QtGui import QPixmap
        # Load pieces (reusing existing assets)
        self.wn_pixmap = QPixmap("assets/pieces/wN.png")
        self.bn_pixmap = QPixmap("assets/pieces/bN.png")

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        from src.utils.styles import Styles
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        theme = Styles.THEMES.get(self.theme_name, Styles.THEMES["Green"])
        c_light = QColor(theme["light"])
        c_dark = QColor(theme["dark"])
        
        # Draw 2x2 Board
        # Top-Left (White), Top-Right (Black), Bottom-Left (Black), Bottom-Right (White)
        sq_w = self.width() / 2
        sq_h = self.height() / 2
        
        # 0,0 (Top Left) -> Light
        painter.fillRect(0, 0, int(sq_w), int(sq_h), c_light)
        # 1,0 (Top Right) -> Dark
        painter.fillRect(int(sq_w), 0, int(sq_w), int(sq_h), c_dark)
        # 0,1 (Bottom Left) -> Dark
        painter.fillRect(0, int(sq_h), int(sq_w), int(sq_h), c_dark)
        # 1,1 (Bottom Right) -> Light
        painter.fillRect(int(sq_w), int(sq_h), int(sq_w), int(sq_h), c_light)
        
        # Draw Pieces (Knights in corners as requested)
        # White Knight at Top-Left (Light)
        # Black Knight at Bottom-Right (Light)
        # Or "Corners"? User said "One white in a corner, one black in the other".
        # Let's put White Knight at Top-Left, Black Knight at Bottom-Right.
        
        if self.wn_pixmap and not self.wn_pixmap.isNull():
            margin = 5
            rect = QRect(margin, margin, int(sq_w - 2*margin), int(sq_h - 2*margin))
            painter.drawPixmap(rect, self.wn_pixmap)
            
        if self.bn_pixmap and not self.bn_pixmap.isNull():
            margin = 5
            rect = QRect(int(sq_w + margin), int(sq_h + margin), int(sq_w - 2*margin), int(sq_h - 2*margin))
            painter.drawPixmap(rect, self.bn_pixmap)

from PyQt6.QtCore import QRect # Import needed for paintEvent

