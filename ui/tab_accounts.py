from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QComboBox, QDialogButtonBox, QMessageBox,
    QInputDialog, QProgressBar
)
from PySide6.QtCore import Qt, Signal
import database as db
from style import COLORS
from ui.widgets.common import make_card, section_label, fmt_yen, badge_label


class AccountsTab(QWidget):
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.year_month = db.current_ym()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        hdr = QHBoxLayout()
        lbl = QLabel("口座残高")
        lbl.setObjectName("heading")
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_add = QPushButton("+ 口座追加")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self._add_account)
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

        # 個人口座
        ph = QHBoxLayout()
        ph.addWidget(section_label("個人口座"))
        self.lbl_p_total = QLabel("")
        self.lbl_p_total.setStyleSheet(f"color:{COLORS['text_sub']};font-size:12px;")
        ph.addStretch()
        ph.addWidget(self.lbl_p_total)
        self.vl.addLayout(ph)

        self.card_p = make_card()
        self.vl_p = QVBoxLayout(self.card_p)
        self.vl_p.setContentsMargins(0, 0, 0, 0)
        self.vl_p.setSpacing(0)
        self.vl.addWidget(self.card_p)

        # 法人口座
        ch = QHBoxLayout()
        ch.addWidget(section_label("法人口座"))
        self.lbl_c_total = QLabel("")
        self.lbl_c_total.setStyleSheet(f"color:{COLORS['text_sub']};font-size:12px;")
        ch.addStretch()
        ch.addWidget(self.lbl_c_total)
        self.vl.addLayout(ch)

        self.card_c = make_card()
        self.vl_c = QVBoxLayout(self.card_c)
        self.vl_c.setContentsMargins(0, 0, 0, 0)
        self.vl_c.setSpacing(0)
        self.vl.addWidget(self.card_c)

        # 積立口座
        sh = QHBoxLayout()
        sh.addWidget(section_label("積立状況"))
        btn_add_sf = QPushButton("+ 積立を追加")
        btn_add_sf.clicked.connect(self._add_sinking)
        sh.addStretch()
        sh.addWidget(btn_add_sf)
        self.vl.addLayout(sh)

        self.card_sf = make_card()
        self.vl_sf = QVBoxLayout(self.card_sf)
        self.vl_sf.setContentsMargins(14, 10, 14, 10)
        self.vl_sf.setSpacing(8)
        self.vl.addWidget(self.card_sf)

        self.vl.addStretch()

    def refresh(self, year_month: str):
        self.year_month = year_month
        self._refresh_accounts("personal", self.vl_p, self.lbl_p_total)
        self._refresh_accounts("corporate", self.vl_c, self.lbl_c_total)
        self._refresh_sinking(year_month)

    def _refresh_accounts(self, category: str, layout, total_lbl):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        accounts = db.get_accounts(category)
        if not accounts:
            lb = QLabel("口座が登録されていません")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:12px;")
            layout.addWidget(lb)
            total_lbl.setText("")
            return

        total = 0
        for acc in accounts:
            if acc["account_type"] in ("operating", "savings"):
                total += acc["balance"]
            row = _AccountRow(acc)
            row.balance_updated.connect(lambda: self.refresh(self.year_month))
            row.delete_requested.connect(lambda aid: self._del_account(aid))
            layout.addWidget(row)

        total_lbl.setText(f"合計 {fmt_yen(total)}")

    def _refresh_sinking(self, year_month: str):
        while self.vl_sf.count():
            item = self.vl_sf.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        funds = db.get_sinking_funds()
        if not funds:
            lb = QLabel("積立項目が未登録です")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};")
            self.vl_sf.addWidget(lb)
            return

        for fund in funds:
            row = _SinkingFundRow(fund, year_month)
            row.updated.connect(lambda: self.refresh(self.year_month))
            row.edit_requested.connect(self._edit_sinking)
            row.delete_requested.connect(self._del_sinking)
            self.vl_sf.addWidget(row)

    def _add_account(self):
        dlg = AccountDialog(parent=self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _del_account(self, aid: int):
        reply = QMessageBox.question(self, "確認", "この口座を削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_account(aid)
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _add_sinking(self):
        dlg = SinkingFundDialog(parent=self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _edit_sinking(self, fid: int):
        funds = db.get_sinking_funds()
        data = next((f for f in funds if f["id"] == fid), None)
        if not data:
            return
        dlg = SinkingFundDialog(data=data, parent=self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _del_sinking(self, fid: int):
        reply = QMessageBox.question(self, "確認", "この積立項目を削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_sinking_fund(fid)
            self.refresh(self.year_month)
            self.data_changed.emit()


class _AccountRow(QWidget):
    balance_updated = Signal()
    delete_requested = Signal(int)

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(48)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};background:transparent;"
        )
        hl = QHBoxLayout(self)
        hl.setContentsMargins(14, 4, 8, 4)
        hl.setSpacing(8)

        lb_name = QLabel(data["name"])
        lb_name.setMinimumWidth(180)
        hl.addWidget(lb_name, 1)

        lb_upd = QLabel(data.get("updated_at", "")[:10])
        lb_upd.setStyleSheet(f"color:{COLORS['text_dim']};font-size:11px;background:transparent;border:none;")
        lb_upd.setFixedWidth(80)
        hl.addWidget(lb_upd)

        lb_bal = QLabel(fmt_yen(data["balance"]))
        lb_bal.setFixedWidth(120)
        lb_bal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lb_bal.setStyleSheet(
            f"font-size:15px;font-weight:bold;color:{COLORS['text']};background:transparent;border:none;"
        )
        hl.addWidget(lb_bal)

        btn_upd = QPushButton("残高更新")
        btn_upd.setFixedWidth(70)
        btn_upd.clicked.connect(self._update_balance)
        hl.addWidget(btn_upd)

        btn_del = QPushButton("✕")
        btn_del.setFixedWidth(30)
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.data["id"]))
        hl.addWidget(btn_del)

    def _update_balance(self):
        val, ok = QInputDialog.getInt(
            self, "残高更新",
            f"「{self.data['name']}」の現在残高を入力してください：",
            self.data["balance"], 0, 999999999
        )
        if ok:
            db.update_account_balance(self.data["id"], val)
            self.balance_updated.emit()


class _SinkingFundRow(QWidget):
    updated = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, fund: dict, year_month: str, parent=None):
        super().__init__(parent)
        self.fund = fund
        self.year_month = year_month
        self.setMinimumHeight(80)
        self.setStyleSheet(
            f"border:1px solid {COLORS['border']};border-radius:6px;"
            f"background:{COLORS['surface']};margin-bottom:4px;"
        )
        self._build()

    def _build(self):
        fund = self.fund
        bal_data = db.get_sinking_fund_balance(fund["id"], self.year_month)
        balance = bal_data.get("balance", 0)
        annual = fund["annual_budget"]
        monthly = fund["monthly_amount"]
        pct = int(balance / annual * 100) if annual else 0

        vl = QVBoxLayout(self)
        vl.setContentsMargins(14, 10, 14, 10)
        vl.setSpacing(4)

        top = QHBoxLayout()
        cat_badge = badge_label(
            "個人" if fund["category"] == "personal" else "法人",
            COLORS["amber_bg"] if fund["category"] == "personal" else COLORS["blue_bg"],
            COLORS["amber_light"] if fund["category"] == "personal" else COLORS["blue_light"]
        )
        top.addWidget(cat_badge)

        name_lb = QLabel(fund["name"])
        name_lb.setStyleSheet("font-weight:bold;font-size:13px;background:transparent;border:none;")
        top.addWidget(name_lb, 1)

        target_lb = QLabel(f"年間目標 {fmt_yen(annual)}  月積立 {fmt_yen(monthly)}")
        target_lb.setStyleSheet(f"color:{COLORS['text_sub']};font-size:12px;background:transparent;border:none;")
        top.addWidget(target_lb)

        btn_edit = QPushButton("設定")
        btn_edit.setFixedWidth(50)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(fund["id"]))
        top.addWidget(btn_edit)

        btn_del = QPushButton("✕")
        btn_del.setFixedWidth(30)
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(lambda: self.delete_requested.emit(fund["id"]))
        top.addWidget(btn_del)

        vl.addLayout(top)

        mid = QHBoxLayout()
        bal_lb = QLabel(f"{fmt_yen(balance)}")
        bal_lb.setStyleSheet(f"font-size:16px;font-weight:bold;color:{COLORS['teal']};background:transparent;border:none;")
        mid.addWidget(bal_lb)
        total_lb = QLabel(f"/ {fmt_yen(annual)}  （{pct}%）")
        total_lb.setStyleSheet(f"color:{COLORS['text_sub']};font-size:12px;background:transparent;border:none;")
        mid.addWidget(total_lb)
        mid.addStretch()

        btn_dep = QPushButton("残高更新")
        btn_dep.setFixedWidth(80)
        btn_dep.clicked.connect(self._update_balance)
        mid.addWidget(btn_dep)

        if fund.get("target_months"):
            target_lb2 = QLabel(f"支出予定: {fund['target_months']}")
            target_lb2.setStyleSheet(f"color:{COLORS['amber_light']};font-size:11px;background:transparent;border:none;")
            mid.addWidget(target_lb2)

        vl.addLayout(mid)

        bar = QProgressBar()
        bar.setFixedHeight(6)
        bar.setRange(0, 100)
        bar.setValue(pct)
        bar.setStyleSheet(
            f"QProgressBar{{background:{COLORS['card']};border:none;border-radius:3px;}}"
            f"QProgressBar::chunk{{background:{COLORS['teal']};border-radius:3px;}}"
        )
        vl.addWidget(bar)

    def _update_balance(self):
        bal_data = db.get_sinking_fund_balance(self.fund["id"], self.year_month)
        current = bal_data.get("balance", 0)
        val, ok = QInputDialog.getInt(
            self, "積立残高更新",
            f"「{self.fund['name']}」の現在の積立残高を入力してください：",
            current, 0, 99999999
        )
        if ok:
            db.update_sinking_fund_balance(self.fund["id"], self.year_month, val)
            self.updated.emit()


class AccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("口座を追加")
        self.setMinimumWidth(320)
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("例: ○○銀行 普通")
        layout.addRow("口座名 *", self.name)

        self.category = QComboBox()
        self.category.addItem("個人", "personal")
        self.category.addItem("法人", "corporate")
        layout.addRow("区分", self.category)

        self.atype = QComboBox()
        self.atype.addItem("運用口座", "operating")
        self.atype.addItem("貯蓄口座", "savings")
        layout.addRow("種別", self.atype)

        self.balance = QSpinBox()
        self.balance.setRange(0, 999999999)
        self.balance.setSingleStep(10000)
        self.balance.setSuffix(" 円")
        layout.addRow("現在残高", self.balance)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "入力エラー", "口座名を入力してください")
            return
        db.add_account(
            self.name.text().strip(),
            self.category.currentData(),
            self.atype.currentData(),
            self.balance.value()
        )
        self.accept()


class SinkingFundDialog(QDialog):
    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("積立を追加" if not data else "積立を編集")
        self.setMinimumWidth(360)
        self._build()
        if data:
            self._populate()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("例: 納税積立、車検・保険")
        layout.addRow("積立名 *", self.name)

        self.category = QComboBox()
        self.category.addItem("個人", "personal")
        self.category.addItem("法人", "corporate")
        layout.addRow("区分", self.category)

        self.annual = QSpinBox()
        self.annual.setRange(0, 99999999)
        self.annual.setSingleStep(10000)
        self.annual.setSuffix(" 円/年")
        self.annual.valueChanged.connect(self._update_monthly)
        layout.addRow("年間予算 *", self.annual)

        self.monthly_lbl = QLabel("月積立: ¥0")
        self.monthly_lbl.setStyleSheet(f"color:{COLORS['teal']};font-weight:bold;")
        layout.addRow("月積立（自動計算）", self.monthly_lbl)

        self.target_months = QLineEdit()
        self.target_months.setPlaceholderText("例: 3月・8月（任意）")
        layout.addRow("支出予定月", self.target_months)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _update_monthly(self, val: int):
        self.monthly_lbl.setText(f"月積立: {fmt_yen(val // 12)}")

    def _populate(self):
        d = self.data
        self.name.setText(d.get("name", ""))
        idx = self.category.findData(d.get("category", "personal"))
        if idx >= 0:
            self.category.setCurrentIndex(idx)
        self.annual.setValue(d.get("annual_budget", 0))
        self.target_months.setText(d.get("target_months", ""))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "入力エラー", "積立名を入力してください")
            return
        if self.annual.value() == 0:
            QMessageBox.warning(self, "入力エラー", "年間予算を入力してください")
            return
        if self.data:
            db.update_sinking_fund(
                self.data["id"],
                self.name.text().strip(),
                self.category.currentData(),
                self.annual.value(),
                self.target_months.text().strip(),
                1
            )
        else:
            db.add_sinking_fund(
                self.name.text().strip(),
                self.category.currentData(),
                self.annual.value(),
                self.target_months.text().strip()
            )
        self.accept()
