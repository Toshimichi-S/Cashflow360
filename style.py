APP_NAME = "キャッシュフロー管理"
APP_VERSION = "1.0.0"

# ── カラーパレット ────────────────────────────────────
COLORS = {
    "bg":           "#1e1e2e",
    "surface":      "#27273a",
    "card":         "#2f2f45",
    "border":       "#3d3d56",
    "text":         "#e0e0f0",
    "text_sub":     "#9090b0",
    "text_dim":     "#606080",
    "purple":       "#7f77dd",
    "purple_light": "#a09ae8",
    "purple_bg":    "#35304a",
    "green":        "#639922",
    "green_light":  "#85c42a",
    "green_bg":     "#2a3520",
    "blue":         "#378add",
    "blue_light":   "#5ea3e8",
    "blue_bg":      "#1e2e42",
    "teal":         "#1d9e75",
    "teal_bg":      "#1a3028",
    "amber":        "#ba7517",
    "amber_light":  "#e09020",
    "amber_bg":     "#3a2a10",
    "coral":        "#d85a30",
    "coral_bg":     "#3a2018",
    "red":          "#e24b4a",
    "red_bg":       "#3a1a1a",
}

# ── バッジ色 ─────────────────────────────────────────
BADGE = {
    "personal":     ("#3a2a10", "#e09020"),
    "corporate":    ("#1e2e42", "#5ea3e8"),
    "confirmed":    ("#2a3520", "#85c42a"),
    "planned":      ("#35304a", "#a09ae8"),
    "pending":      ("#3a2a10", "#e09020"),
    "sinking":      ("#1a3028", "#1d9e75"),
    "fixed_auto":   ("#35304a", "#a09ae8"),
    "variable":     ("#1e2e42", "#5ea3e8"),
}

# ── スタイルシート ────────────────────────────────────
def get_stylesheet():
    c = COLORS
    return f"""
    QMainWindow, QDialog {{
        background-color: {c['bg']};
    }}
    QWidget {{
        background-color: {c['bg']};
        color: {c['text']};
        font-family: "Yu Gothic UI", "Meiryo UI", "MS Gothic", sans-serif;
        font-size: 13px;
    }}
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-top: none;
        background-color: {c['bg']};
    }}
    QTabBar::tab {{
        background-color: {c['surface']};
        color: {c['text_sub']};
        padding: 8px 18px;
        border: 1px solid {c['border']};
        border-bottom: none;
        margin-right: 2px;
        font-size: 12px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['bg']};
        color: {c['text']};
        border-bottom: 2px solid {c['purple']};
    }}
    QTabBar::tab:hover {{
        color: {c['text']};
    }}
    QFrame#card {{
        background-color: {c['card']};
        border: 1px solid {c['border']};
        border-radius: 8px;
    }}
    QPushButton {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 5px;
        padding: 5px 14px;
        font-size: 12px;
    }}
    QPushButton:hover {{
        background-color: {c['card']};
        border-color: {c['purple']};
    }}
    QPushButton:pressed {{
        background-color: {c['purple_bg']};
    }}
    QPushButton#primary {{
        background-color: {c['purple']};
        color: white;
        border: none;
    }}
    QPushButton#primary:hover {{
        background-color: {c['purple_light']};
    }}
    QPushButton#success {{
        background-color: {c['green_bg']};
        color: {c['green_light']};
        border: 1px solid {c['green']};
    }}
    QPushButton#success:hover {{
        background-color: {c['green']};
        color: white;
    }}
    QPushButton#danger {{
        background-color: {c['red_bg']};
        color: {c['red']};
        border: 1px solid {c['red']};
    }}
    QPushButton#danger:hover {{
        background-color: {c['red']};
        color: white;
    }}
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QDateEdit {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 5px;
        padding: 4px 8px;
        selection-background-color: {c['purple']};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
        border-color: {c['purple']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        selection-background-color: {c['purple_bg']};
    }}
    QTableWidget {{
        background-color: {c['card']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        gridline-color: {c['border']};
        alternate-background-color: {c['surface']};
    }}
    QTableWidget::item {{
        padding: 5px 8px;
    }}
    QTableWidget::item:selected {{
        background-color: {c['purple_bg']};
        color: {c['text']};
    }}
    QHeaderView::section {{
        background-color: {c['surface']};
        color: {c['text_sub']};
        border: none;
        border-right: 1px solid {c['border']};
        border-bottom: 1px solid {c['border']};
        padding: 5px 8px;
        font-size: 11px;
    }}
    QScrollBar:vertical {{
        background: {c['surface']};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {c['surface']};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['border']};
        border-radius: 4px;
    }}
    QLabel#heading {{
        font-size: 15px;
        font-weight: bold;
        color: {c['text']};
    }}
    QLabel#subheading {{
        font-size: 12px;
        color: {c['text_sub']};
    }}
    QLabel#section {{
        font-size: 11px;
        color: {c['text_dim']};
        font-weight: bold;
        letter-spacing: 1px;
    }}
    QProgressBar {{
        background-color: {c['surface']};
        border: none;
        border-radius: 3px;
        height: 6px;
        text-align: center;
        font-size: 0px;
    }}
    QProgressBar::chunk {{
        border-radius: 3px;
    }}
    QCheckBox {{
        color: {c['text']};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {c['border']};
        border-radius: 3px;
        background-color: {c['surface']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['green']};
        border-color: {c['green']};
    }}
    QSplitter::handle {{
        background-color: {c['border']};
    }}
    QMessageBox {{
        background-color: {c['surface']};
    }}
    QGroupBox {{
        border: 1px solid {c['border']};
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 6px;
        color: {c['text_sub']};
        font-size: 11px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }}
    """
