from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QComboBox, QDialogButtonBox, QMessageBox, QCheckBox,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal
import database as db
from style import COLORS
from ui.widgets.common import make_card, section_label, fmt_yen, badge_label


class SettingsTab(QWidget):
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.year_month = db.current_ym()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        lbl = QLabel("マスタ設定")
        lbl.setObjectName("heading")
        root.addWidget(lbl)

        inner_tabs = QTabWidget()
        root.addWidget(inner_tabs)

        # 目標設定
        goal_tab = _GoalTab()
        goal_tab.saved.connect(self.data_changed)
        inner_tabs.addTab(goal_tab, "目標設定")

        # 固定費マスタ
        fixed_tab = _FixedExpenseTab()
        fixed_tab.changed.connect(self.data_changed)
        inner_tabs.addTab(fixed_tab, "固定費マスタ")

        # サービスマスタ
        svc_tab = _ServiceTab()
        svc_tab.changed.connect(self.data_changed)
        inner_tabs.addTab(svc_tab, "サービスマスタ")

        self.goal_tab = goal_tab
        self.fixed_tab = fixed_tab
        self.svc_tab = svc_tab

    def refresh(self, year_month: str):
        self.year_month = year_month
        self.goal_tab.refresh(year_month)
        self.fixed_tab.refresh()
        self.svc_tab.refresh()


# ── 目標設定タブ ─────────────────────────────────────
class _GoalTab(QWidget):
    saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.year_month = db.current_ym()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        note = QLabel(
            "毎月、前月の設定を自動で引き継ぎます。変更した分だけ「保存」してください。"
        )
        note.setStyleSheet(
            f"background:{COLORS['surface']};color:{COLORS['text_sub']};"
            f"padding:8px;border-radius:5px;font-size:12px;"
        )
        note.setWordWrap(True)
        root.addWidget(note)

        cols = QHBoxLayout()
        cols.setSpacing(12)

        # 個人
        p_card = make_card()
        p_vl = QVBoxLayout(p_card)
        p_vl.addWidget(section_label("個人"))

        p_form = QFormLayout()
        self.p_income = QSpinBox()
        self.p_income.setRange(0, 99999999)
        self.p_income.setSingleStep(10000)
        self.p_income.setSuffix(" 円")
        p_form.addRow("月収目標", self.p_income)

        self.p_expense = QSpinBox()
        self.p_expense.setRange(0, 99999999)
        self.p_expense.setSingleStep(10000)
        self.p_expense.setSuffix(" 円")
        p_form.addRow("支出上限", self.p_expense)

        p_vl.addLayout(p_form)
        cols.addWidget(p_card)

        # 法人
        c_card = make_card()
        c_vl = QVBoxLayout(c_card)
        c_vl.addWidget(section_label("法人"))

        c_form = QFormLayout()
        self.c_income = QSpinBox()
        self.c_income.setRange(0, 99999999)
        self.c_income.setSingleStep(50000)
        self.c_income.setSuffix(" 円")
        c_form.addRow("月次売上目標", self.c_income)

        self.c_expense = QSpinBox()
        self.c_expense.setRange(0, 99999999)
        self.c_expense.setSingleStep(10000)
        self.c_expense.setSuffix(" 円")
        c_form.addRow("経費上限", self.c_expense)

        self.c_mrr = QSpinBox()
        self.c_mrr.setRange(0, 99999999)
        self.c_mrr.setSingleStep(10000)
        self.c_mrr.setSuffix(" 円")
        c_form.addRow("MRR目標", self.c_mrr)

        c_vl.addLayout(c_form)
        cols.addWidget(c_card)

        root.addLayout(cols)

        btn_save = QPushButton("この月の目標を保存")
        btn_save.setObjectName("primary")
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self._save)
        root.addWidget(btn_save)
        root.addStretch()

    def refresh(self, year_month: str):
        self.year_month = year_month
        p = db.get_goal(year_month, "personal")
        c = db.get_goal(year_month, "corporate")
        if not p.get("income_target"):
            db.copy_goal_from_prev(year_month, "personal")
            p = db.get_goal(year_month, "personal")
        if not c.get("income_target"):
            db.copy_goal_from_prev(year_month, "corporate")
            c = db.get_goal(year_month, "corporate")

        self.p_income.setValue(p.get("income_target", 0))
        self.p_expense.setValue(p.get("expense_limit", 0))
        self.c_income.setValue(c.get("income_target", 0))
        self.c_expense.setValue(c.get("expense_limit", 0))
        self.c_mrr.setValue(c.get("mrr_target", 0))

    def _save(self):
        db.save_goal(self.year_month, "personal",
                     self.p_income.value(), self.p_expense.value())
        db.save_goal(self.year_month, "corporate",
                     self.c_income.value(), self.c_expense.value(),
                     self.c_mrr.value())
        QMessageBox.information(self, "保存完了", "目標を保存しました。")
        self.saved.emit()


# ── 固定費マスタタブ ──────────────────────────────────
class _FixedExpenseTab(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        note = QLabel(
            "ここで登録した固定費は、毎月の予実表に自動で表示されます。"
            "季節変動フラグをつけると、毎月の予実で目標額を変更できます。"
        )
        note.setStyleSheet(
            f"background:{COLORS['surface']};color:{COLORS['text_sub']};"
            f"padding:8px;border-radius:5px;font-size:12px;"
        )
        note.setWordWrap(True)
        root.addWidget(note)

        for category, label in [("personal", "個人"), ("corporate", "法人")]:
            hdr = QHBoxLayout()
            hdr.addWidget(section_label(f"{label}固定費"))
            hdr.addStretch()
            btn = QPushButton(f"+ {label}固定費を追加")
            btn.clicked.connect(lambda _, c=category: self._add(c))
            hdr.addWidget(btn)
            root.addLayout(hdr)

            card = make_card()
            vl = QVBoxLayout(card)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(0)
            setattr(self, f"vl_{category}", vl)
            root.addWidget(card)

        root.addStretch()

    def refresh(self):
        for category in ("personal", "corporate"):
            layout = getattr(self, f"vl_{category}")
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            masters = db.get_fixed_masters(category)
            if not masters:
                lb = QLabel("未登録")
                lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:10px;")
                layout.addWidget(lb)
                continue

            for m in masters:
                row = _FixedMasterRow(m)
                row.edit_requested.connect(self._edit)
                row.delete_requested.connect(self._delete)
                layout.addWidget(row)

    def _add(self, category: str):
        dlg = FixedMasterDialog(category=category, parent=self)
        if dlg.exec():
            self.refresh()
            self.changed.emit()

    def _edit(self, mid: int):
        masters_p = db.get_fixed_masters("personal")
        masters_c = db.get_fixed_masters("corporate")
        data = next((m for m in masters_p + masters_c if m["id"] == mid), None)
        if not data:
            return
        dlg = FixedMasterDialog(data=data, category=data["category"], parent=self)
        if dlg.exec():
            self.refresh()
            self.changed.emit()

    def _delete(self, mid: int):
        reply = QMessageBox.question(self, "確認", "この固定費を削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_fixed_master(mid)
            self.refresh()
            self.changed.emit()


class _FixedMasterRow(QWidget):
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(44)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};background:transparent;"
        )
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 4, 8, 4)
        hl.setSpacing(8)

        if data.get("is_seasonal"):
            season_badge = badge_label("季節変動", COLORS["amber_bg"], COLORS["amber_light"])
            hl.addWidget(season_badge)

        lb = QLabel(data["name"])
        lb.setMinimumWidth(160)
        hl.addWidget(lb, 1)

        amt = QLabel(fmt_yen(data["monthly_amount"]))
        amt.setFixedWidth(100)
        amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amt.setStyleSheet(f"color:{COLORS['text']};background:transparent;border:none;")
        hl.addWidget(amt)

        btn_edit = QPushButton("編集")
        btn_edit.setFixedWidth(50)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.data["id"]))
        hl.addWidget(btn_edit)

        btn_del = QPushButton("✕")
        btn_del.setFixedWidth(30)
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.data["id"]))
        hl.addWidget(btn_del)


class FixedMasterDialog(QDialog):
    def __init__(self, category: str, data: dict = None, parent=None):
        super().__init__(parent)
        self.category = category
        self.data = data
        cat_name = "個人" if category == "personal" else "法人"
        self.setWindowTitle(f"{cat_name}固定費を{'追加' if not data else '編集'}")
        self.setMinimumWidth(320)
        self._build()
        if data:
            self._populate()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("例: 電気代、Notion、外注費")
        layout.addRow("項目名 *", self.name)

        self.amount = QSpinBox()
        self.amount.setRange(0, 9999999)
        self.amount.setSingleStep(500)
        self.amount.setSuffix(" 円/月")
        layout.addRow("月額目標 *", self.amount)

        self.is_seasonal = QCheckBox("季節によって変動する（毎月手動で調整可能にする）")
        layout.addRow("", self.is_seasonal)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self):
        self.name.setText(self.data.get("name", ""))
        self.amount.setValue(self.data.get("monthly_amount", 0))
        self.is_seasonal.setChecked(bool(self.data.get("is_seasonal", 0)))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "入力エラー", "項目名を入力してください")
            return
        if self.data:
            db.update_fixed_master(
                self.data["id"],
                self.name.text().strip(),
                self.amount.value(),
                1 if self.is_seasonal.isChecked() else 0
            )
        else:
            db.add_fixed_master(
                self.category,
                self.name.text().strip(),
                self.amount.value(),
                is_seasonal=1 if self.is_seasonal.isChecked() else 0
            )
        self.accept()


# ── サービスマスタタブ ────────────────────────────────
class _ServiceTab(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.addWidget(section_label("サービスマスタ"))
        hdr.addStretch()
        btn = QPushButton("+ サービスを追加")
        btn.setObjectName("primary")
        btn.clicked.connect(self._add)
        hdr.addWidget(btn)
        root.addLayout(hdr)

        self.card = make_card()
        self.vl = QVBoxLayout(self.card)
        self.vl.setContentsMargins(0, 0, 0, 0)
        self.vl.setSpacing(0)
        root.addWidget(self.card)
        root.addStretch()

    def refresh(self):
        while self.vl.count():
            item = self.vl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        services = db.get_services()
        if not services:
            lb = QLabel("サービスが未登録です。まずサービスを追加してください。")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:12px;")
            self.vl.addWidget(lb)
            return

        for s in services:
            row = _ServiceRow(s)
            row.edit_requested.connect(self._edit)
            self.vl.addWidget(row)

    def _add(self):
        dlg = ServiceDialog(parent=self)
        if dlg.exec():
            self.refresh()
            self.changed.emit()

    def _edit(self, sid: int):
        services = db.get_services()
        data = next((s for s in services if s["id"] == sid), None)
        if not data:
            return
        dlg = ServiceDialog(data=data, parent=self)
        if dlg.exec():
            self.refresh()
            self.changed.emit()


class _ServiceRow(QWidget):
    edit_requested = Signal(int)

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(44)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};background:transparent;"
        )
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 4, 8, 4)
        hl.setSpacing(8)

        type_map = {
            "subscription": ("サブスク", COLORS["teal_bg"], COLORS["teal"]),
            "consulting":   ("コンサル", COLORS["amber_bg"], COLORS["amber_light"]),
            "project":      ("受託",     COLORS["coral_bg"], COLORS["coral"]),
        }
        t = data.get("type", "subscription")
        tname, bg, fg = type_map.get(t, ("", COLORS["surface"], COLORS["text_sub"]))
        hl.addWidget(badge_label(tname, bg, fg))

        lb = QLabel(data["name"])
        lb.setMinimumWidth(160)
        hl.addWidget(lb, 1)

        amt = QLabel(fmt_yen(data["standard_fee"]) + "/月")
        amt.setFixedWidth(100)
        amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amt.setStyleSheet(f"color:{COLORS['text']};background:transparent;border:none;")
        hl.addWidget(amt)

        lb_desc = QLabel(data.get("description", ""))
        lb_desc.setStyleSheet(
            f"color:{COLORS['text_dim']};font-size:11px;background:transparent;border:none;"
        )
        hl.addWidget(lb_desc)

        btn = QPushButton("編集")
        btn.setFixedWidth(50)
        btn.clicked.connect(lambda: self.edit_requested.emit(self.data["id"]))
        hl.addWidget(btn)


class ServiceDialog(QDialog):
    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("サービスを追加" if not data else "サービスを編集")
        self.setMinimumWidth(360)
        self._build()
        if data:
            self._populate()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("例: サービスA、月次コンサル")
        layout.addRow("サービス名 *", self.name)

        self.stype = QComboBox()
        self.stype.addItem("サブスクリプション", "subscription")
        self.stype.addItem("コンサルティング",   "consulting")
        self.stype.addItem("受託開発・制作",       "project")
        layout.addRow("種別", self.stype)

        self.fee = QSpinBox()
        self.fee.setRange(0, 9999999)
        self.fee.setSingleStep(1000)
        self.fee.setSuffix(" 円/月")
        layout.addRow("標準月額", self.fee)

        self.description = QLineEdit()
        layout.addRow("説明（任意）", self.description)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self):
        self.name.setText(self.data.get("name", ""))
        idx = self.stype.findData(self.data.get("type", "subscription"))
        if idx >= 0:
            self.stype.setCurrentIndex(idx)
        self.fee.setValue(self.data.get("standard_fee", 0))
        self.description.setText(self.data.get("description", ""))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "入力エラー", "サービス名を入力してください")
            return
        if self.data:
            db.update_service(
                self.data["id"],
                self.name.text().strip(),
                self.stype.currentData(),
                self.fee.value(),
                self.description.text().strip()
            )
        else:
            db.add_service(
                self.name.text().strip(),
                self.stype.currentData(),
                self.fee.value(),
                self.description.text().strip()
            )
        self.accept()
