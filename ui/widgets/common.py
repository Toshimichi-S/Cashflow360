from PySide6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QVBoxLayout,
    QProgressBar, QPushButton, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt
from style import COLORS


def fmt_yen(amount: int) -> str:
    return f"¥{amount:,}"


def make_card(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setObjectName("card")
    f.setFrameShape(QFrame.StyledPanel)
    return f


def section_label(text: str) -> QLabel:
    lb = QLabel(text.upper())
    lb.setObjectName("section")
    return lb


def heading_label(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setObjectName("heading")
    return lb


def sub_label(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setObjectName("subheading")
    return lb


def spacer_h() -> QWidget:
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return w


def badge_label(text: str, bg: str, fg: str) -> QLabel:
    lb = QLabel(text)
    lb.setStyleSheet(
        f"background:{bg};color:{fg};border-radius:3px;"
        f"padding:1px 7px;font-size:10px;font-weight:bold;"
    )
    lb.setAlignment(Qt.AlignCenter)
    lb.setFixedHeight(18)
    return lb


def category_badge(category: str) -> QLabel:
    if category == "personal":
        return badge_label("個人", COLORS["amber_bg"], COLORS["amber_light"])
    else:
        return badge_label("法人", COLORS["blue_bg"], COLORS["blue_light"])


def status_badge(status: str) -> QLabel:
    labels = {
        "confirmed": ("確認済", COLORS["green_bg"], COLORS["green_light"]),
        "planned":   ("予定",   COLORS["purple_bg"], COLORS["purple_light"]),
        "pending":   ("入金待", COLORS["amber_bg"],  COLORS["amber_light"]),
    }
    text, bg, fg = labels.get(status, (status, COLORS["border"], COLORS["text_sub"]))
    return badge_label(text, bg, fg)


class MetricCard(QFrame):
    """数値を表示するカード（ダッシュボード用）"""

    def __init__(self, label: str, value: str = "¥0",
                 sub: str = "", color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.lbl = QLabel(label)
        self.lbl.setObjectName("section")
        layout.addWidget(self.lbl)

        self.val = QLabel(value)
        self.val.setStyleSheet(
            f"font-size:20px;font-weight:bold;"
            f"color:{color or COLORS['text']};"
        )
        layout.addWidget(self.val)

        self.sub_lbl = QLabel(sub)
        self.sub_lbl.setObjectName("subheading")
        layout.addWidget(self.sub_lbl)

        self.bar = QProgressBar()
        self.bar.setFixedHeight(5)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.hide()
        layout.addWidget(self.bar)

    def update(self, value: str, sub: str = "", progress: int = None,
               bar_color: str = None):
        self.val.setText(value)
        self.sub_lbl.setText(sub)
        if progress is not None:
            self.bar.show()
            self.bar.setValue(min(progress, 100))
            col = bar_color or COLORS["purple"]
            self.bar.setStyleSheet(
                f"QProgressBar::chunk{{background-color:{col};}}"
            )
        else:
            self.bar.hide()


class BudgetRow(QFrame):
    """予実の1行（ラベル＋バー＋予算・実績・差異）"""

    def __init__(self, item_name: str, item_type: str,
                 budget: int, actual: int, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};"
            f"background:transparent;"
        )

        hl = QHBoxLayout(self)
        hl.setContentsMargins(8, 4, 8, 4)
        hl.setSpacing(8)

        type_colors = {
            "fixed_auto": (COLORS["purple_bg"], COLORS["purple_light"]),
            "sinking":    (COLORS["teal_bg"],   COLORS["teal"]),
            "variable":   (COLORS["blue_bg"],   COLORS["blue_light"]),
        }
        bg, fg = type_colors.get(item_type, (COLORS["surface"], COLORS["text_sub"]))
        type_names = {
            "fixed_auto": "自動",
            "sinking":    "積立",
            "variable":   "変動",
        }
        tag = badge_label(type_names.get(item_type, ""), bg, fg)
        hl.addWidget(tag)

        name_lbl = QLabel(item_name)
        name_lbl.setMinimumWidth(150)
        hl.addWidget(name_lbl)

        bar = QProgressBar()
        bar.setFixedHeight(5)
        bar.setRange(0, 100)
        pct = int(actual / budget * 100) if budget > 0 else 0
        bar.setValue(min(pct, 100))
        col = (COLORS["red"] if pct > 100 else
               COLORS["amber"] if pct > 85 else
               COLORS["teal"] if item_type == "sinking" else
               COLORS["blue"])
        bar.setStyleSheet(f"QProgressBar::chunk{{background-color:{col};}}")
        hl.addWidget(bar, 1)

        for text, color in [
            (fmt_yen(budget), COLORS["text_sub"]),
            (fmt_yen(actual), COLORS["text"]),
        ]:
            lb = QLabel(text)
            lb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lb.setFixedWidth(80)
            lb.setStyleSheet(f"color:{color};background:transparent;border:none;")
            hl.addWidget(lb)

        diff = budget - actual
        diff_text = f"+{fmt_yen(diff)}" if diff >= 0 else fmt_yen(diff)
        diff_color = COLORS["green"] if diff >= 0 else COLORS["red"]
        diff_lbl = QLabel(diff_text)
        diff_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        diff_lbl.setFixedWidth(90)
        diff_lbl.setStyleSheet(
            f"color:{diff_color};background:transparent;border:none;"
        )
        hl.addWidget(diff_lbl)
