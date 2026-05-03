from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QComboBox, QDialogButtonBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
import database as db
from style import COLORS
from ui.widgets.common import make_card, section_label, fmt_yen, badge_label


class MemoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("備忘・TODO")
        lbl.setObjectName("heading")
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_add = QPushButton("+ 追加")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self._add_memo)
        hdr.addWidget(btn_add)
        root.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self.vl = QVBoxLayout(content)
        self.vl.setSpacing(12)
        self.vl.setContentsMargins(0, 0, 0, 0)

        col_layout = QHBoxLayout()
        col_layout.setSpacing(12)
        col_layout.setAlignment(Qt.AlignTop)

        # 左列
        left = QVBoxLayout()
        left.setSpacing(10)
        left.setAlignment(Qt.AlignTop)

        left.addWidget(section_label("支払い予定"))
        self.card_payment = make_card()
        self.vl_payment = QVBoxLayout(self.card_payment)
        self.vl_payment.setContentsMargins(0, 0, 0, 0)
        self.vl_payment.setSpacing(0)
        left.addWidget(self.card_payment)

        left.addWidget(section_label("収入予定"))
        self.card_income = make_card()
        self.vl_income = QVBoxLayout(self.card_income)
        self.vl_income.setContentsMargins(0, 0, 0, 0)
        self.vl_income.setSpacing(0)
        left.addWidget(self.card_income)

        # 右列
        right = QVBoxLayout()
        right.setSpacing(10)
        right.setAlignment(Qt.AlignTop)

        right.addWidget(section_label("チェックリスト（TODO）"))
        self.card_todo = make_card()
        self.vl_todo = QVBoxLayout(self.card_todo)
        self.vl_todo.setContentsMargins(0, 0, 0, 0)
        self.vl_todo.setSpacing(0)
        right.addWidget(self.card_todo)

        lw = QWidget()
        lw.setLayout(left)
        rw = QWidget()
        rw.setLayout(right)

        col_layout.addWidget(lw, 1)
        col_layout.addWidget(rw, 1)

        wrapper = QWidget()
        wrapper.setLayout(col_layout)
        self.vl.addWidget(wrapper)
        self.vl.addStretch()

    def refresh(self, year_month: str = None):
        self._refresh_section("payment",  self.vl_payment)
        self._refresh_section("income",   self.vl_income)
        self._refresh_section("todo",     self.vl_todo)

    def _refresh_section(self, memo_type: str, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        memos = db.get_memos(done=False)
        items = [m for m in memos if m["memo_type"] == memo_type]
        done_items = [m for m in db.get_memos(done=True) if m["memo_type"] == memo_type]

        if not items and not done_items:
            lb = QLabel("項目なし")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:10px;")
            layout.addWidget(lb)
            return

        for m in items:
            row = _MemoRow(m)
            row.toggled.connect(lambda: self.refresh())
            row.deleted.connect(lambda: self.refresh())
            layout.addWidget(row)

        for m in done_items:
            row = _MemoRow(m)
            row.toggled.connect(lambda: self.refresh())
            row.deleted.connect(lambda: self.refresh())
            layout.addWidget(row)

    def _add_memo(self):
        dlg = AddMemoDialog(self)
        if dlg.exec():
            self.refresh()


class _MemoRow(QWidget):
    toggled = Signal()
    deleted = Signal()

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(48)
        done = data.get("is_done", 0)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};"
            f"background:{COLORS['surface'] if done else 'transparent'};"
        )

        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 4, 8, 4)
        hl.setSpacing(8)

        cb = QCheckBox()
        cb.setChecked(bool(done))
        cb.stateChanged.connect(self._toggle)
        hl.addWidget(cb)

        cat = data.get("category", "personal")
        cat_badge = badge_label(
            "個人" if cat == "personal" else "法人",
            COLORS["amber_bg"] if cat == "personal" else COLORS["blue_bg"],
            COLORS["amber_light"] if cat == "personal" else COLORS["blue_light"]
        )
        hl.addWidget(cat_badge)

        lb = QLabel(data["title"])
        if done:
            lb.setStyleSheet(
                f"color:{COLORS['text_dim']};text-decoration:line-through;background:transparent;"
            )
        hl.addWidget(lb, 1)

        if data.get("amount", 0) > 0:
            lb_amt = QLabel(fmt_yen(data["amount"]))
            lb_amt.setStyleSheet(
                f"color:{COLORS['amber_light']};font-weight:bold;background:transparent;border:none;"
            )
            lb_amt.setFixedWidth(90)
            lb_amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            hl.addWidget(lb_amt)

        if data.get("due_date"):
            lb_date = QLabel(data["due_date"])
            lb_date.setStyleSheet(
                f"color:{COLORS['text_sub']};font-size:11px;background:transparent;border:none;"
            )
            lb_date.setFixedWidth(70)
            hl.addWidget(lb_date)

        btn_del = QPushButton("✕")
        btn_del.setFixedWidth(30)
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(self._delete)
        hl.addWidget(btn_del)

    def _toggle(self, state):
        done = state == Qt.Checked.value
        db.toggle_memo_done(self.data["id"], done)
        self.toggled.emit()

    def _delete(self):
        db.delete_memo(self.data["id"])
        self.deleted.emit()


class AddMemoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("備忘・TODOを追加")
        self.setMinimumWidth(360)
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.memo_type = QComboBox()
        self.memo_type.addItem("支払い予定", "payment")
        self.memo_type.addItem("収入予定",   "income")
        self.memo_type.addItem("チェックリスト（TODO）", "todo")
        layout.addRow("種別", self.memo_type)

        self.category = QComboBox()
        self.category.addItem("個人", "personal")
        self.category.addItem("法人", "corporate")
        layout.addRow("区分", self.category)

        self.title = QLineEdit()
        self.title.setPlaceholderText("例: 法人税 中間納付、請求書送付")
        layout.addRow("タイトル *", self.title)

        self.amount = QSpinBox()
        self.amount.setRange(0, 99999999)
        self.amount.setSingleStep(1000)
        _w = QWidget()
        _hl = QHBoxLayout(_w)
        _hl.setContentsMargins(0,0,0,0)
        _hl.setSpacing(6)
        _hl.addWidget(self.amount)
        _hl.addWidget(QLabel("円"))
        layout.addRow("金額（任意）", _w)

        self.due_date = QLineEdit()
        self.due_date.setPlaceholderText("例: 5/31  または  月末")
        layout.addRow("期日", self.due_date)

        self.note = QLineEdit()
        layout.addRow("メモ", self.note)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        if not self.title.text().strip():
            QMessageBox.warning(self, "入力エラー", "タイトルを入力してください")
            return
        db.add_memo(
            self.title.text().strip(),
            self.memo_type.currentData(),
            self.category.currentData(),
            self.amount.value(),
            self.due_date.text().strip(),
            self.note.text().strip()
        )
        self.accept()
