from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QComboBox, QDialogButtonBox, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
import database as db
from style import COLORS
from ui.widgets.common import (
    make_card, section_label, fmt_yen, badge_label, MetricCard
)


class SubscriptionsTab(QWidget):
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.year_month = db.current_ym()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("サブスク顧客管理")
        lbl.setObjectName("heading")
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_add = QPushButton("+ 顧客追加")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self._add_customer)
        hdr.addWidget(btn_add)
        root.addLayout(hdr)

        # サマリーカード
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.mc_mrr     = MetricCard("MRR合計", color=COLORS["teal"])
        self.mc_count   = MetricCard("顧客数（アクティブ）")
        self.mc_pending = MetricCard("今月 入金待ち", color=COLORS["amber"])
        self.grid.addWidget(self.mc_mrr,     0, 0)
        self.grid.addWidget(self.mc_count,   0, 1)
        self.grid.addWidget(self.mc_pending, 0, 2)
        root.addLayout(self.grid)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self.vl = QVBoxLayout(content)
        self.vl.setSpacing(12)
        self.vl.setContentsMargins(0, 0, 0, 0)

        # 入金確認（今月）
        pay_hdr = QHBoxLayout()
        pay_hdr.addWidget(section_label("今月の入金確認"))
        self.vl.addLayout(pay_hdr)

        self.card_payments = make_card()
        self.pay_layout = QVBoxLayout(self.card_payments)
        self.pay_layout.setContentsMargins(0, 0, 0, 0)
        self.pay_layout.setSpacing(0)
        self.vl.addWidget(self.card_payments)

        # 顧客一覧
        self.vl.addWidget(section_label("顧客一覧"))
        self.card_customers = make_card()
        self.cust_layout = QVBoxLayout(self.card_customers)
        self.cust_layout.setContentsMargins(0, 0, 0, 0)
        self.cust_layout.setSpacing(0)
        self.vl.addWidget(self.card_customers)

        self.vl.addStretch()

    def refresh(self, year_month: str):
        self.year_month = year_month
        db.ensure_customer_payments(year_month)

        customers = db.get_customers()
        payments  = db.get_customer_payments(year_month)
        mrr       = sum(c["monthly_fee"] for c in customers)
        pending   = [p for p in payments if p["status"] == "pending"]

        self.mc_mrr.update(fmt_yen(mrr))
        self.mc_count.update(f"{len(customers)} 社")
        self.mc_pending.update(
            f"{len(pending)} 件",
            fmt_yen(sum(p["amount"] for p in pending)),
        )

        self._refresh_payments(payments)
        self._refresh_customers(customers)

    def _refresh_payments(self, payments):
        while self.pay_layout.count():
            item = self.pay_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not payments:
            lb = QLabel("顧客が登録されていません")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:12px;")
            self.pay_layout.addWidget(lb)
            return

        for p in payments:
            row = _PaymentRow(p)
            row.changed.connect(lambda: self.refresh(self.year_month))
            self.pay_layout.addWidget(row)

    def _refresh_customers(self, customers):
        while self.cust_layout.count():
            item = self.cust_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not customers:
            lb = QLabel("顧客が登録されていません")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:12px;")
            self.cust_layout.addWidget(lb)
            return

        hdr = QHBoxLayout()
        hdr.setContentsMargins(8, 4, 8, 4)
        for text, width in [("顧客名", -1), ("サービス", 100),
                             ("月額", 90), ("入金日", 80), ("", 120)]:
            lb = QLabel(text)
            lb.setStyleSheet(
                f"color:{COLORS['text_dim']};font-size:11px;background:transparent;"
            )
            if width > 0:
                lb.setFixedWidth(width)
            hdr.addWidget(lb, 0 if width > 0 else 1)
        w = QWidget()
        w.setLayout(hdr)
        w.setStyleSheet(
            f"background:{COLORS['surface']};border-bottom:1px solid {COLORS['border']};"
        )
        self.cust_layout.addWidget(w)

        for c in customers:
            row = _CustomerRow(c)
            row.edit_requested.connect(self._edit_customer)
            row.delete_requested.connect(self._del_customer)
            self.cust_layout.addWidget(row)

    def _add_customer(self):
        services = db.get_services()
        if not services:
            QMessageBox.warning(
                self, "サービス未登録",
                "先にマスタ設定からサービスを登録してください。"
            )
            return
        dlg = CustomerDialog(parent=self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _edit_customer(self, cid: int):
        customers = db.get_customers(active_only=False)
        data = next((c for c in customers if c["id"] == cid), None)
        if not data:
            return
        dlg = CustomerDialog(data=data, parent=self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _del_customer(self, cid: int):
        reply = QMessageBox.question(
            self, "確認", "この顧客を無効化しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.deactivate_customer(cid)
            self.refresh(self.year_month)
            self.data_changed.emit()


# ── 入金確認行 ────────────────────────────────────────────
class _PaymentRow(QWidget):
    changed = Signal()   # 確認・取消どちらでも発火

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(48)

        is_confirmed = data["status"] == "confirmed"
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};"
            f"background:{'rgba(42,53,32,0.4)' if is_confirmed else 'transparent'};"
        )

        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 4, 10, 4)
        hl.setSpacing(8)

        # サービスバッジ
        svc_colors = {
            "subscription": (COLORS["teal_bg"],   COLORS["teal"]),
            "consulting":   (COLORS["amber_bg"],   COLORS["amber_light"]),
            "project":      (COLORS["coral_bg"],   COLORS["coral"]),
        }
        stype = data.get("service_type", "subscription")
        bg, fg = svc_colors.get(stype, (COLORS["surface"], COLORS["text_sub"]))
        hl.addWidget(badge_label(data.get("service_name", ""), bg, fg))

        # 顧客名
        lb = QLabel(data["customer_name"])
        lb.setMinimumWidth(160)
        hl.addWidget(lb, 1)

        # 金額
        amt = QLabel(fmt_yen(data["amount"]))
        amt.setFixedWidth(90)
        amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amt.setStyleSheet(
            f"color:{COLORS['text']};font-weight:bold;background:transparent;border:none;"
        )
        hl.addWidget(amt)

        if is_confirmed:
            # 確認済バッジ
            hl.addWidget(badge_label("確認済", COLORS["green_bg"], COLORS["green_light"]))

            # 確認日
            date_lb = QLabel(data.get("confirmed_date", "") or "")
            date_lb.setStyleSheet(
                f"color:{COLORS['text_dim']};font-size:11px;background:transparent;border:none;"
            )
            date_lb.setFixedWidth(70)
            hl.addWidget(date_lb)

            # 取消ボタン
            btn_reset = QPushButton("取消")
            btn_reset.setFixedWidth(54)
            btn_reset.setObjectName("danger")
            btn_reset.setToolTip("未確認状態に戻す")
            btn_reset.clicked.connect(self._reset)
            hl.addWidget(btn_reset)
        else:
            # 入金確認ボタン
            btn = QPushButton("入金確認 ✓")
            btn.setObjectName("success")
            btn.setFixedWidth(90)
            btn.clicked.connect(self._confirm)
            hl.addWidget(btn)

    def _confirm(self):
        db.confirm_customer_payment(self.data["id"])
        self.changed.emit()

    def _reset(self):
        reply = QMessageBox.question(
            self, "確認",
            f"「{self.data['customer_name']}」の入金確認を取り消しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.reset_customer_payment(self.data["id"])
            self.changed.emit()


# ── 顧客一覧行 ────────────────────────────────────────────
class _CustomerRow(QWidget):
    edit_requested   = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(44)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};background:transparent;"
        )
        hl = QHBoxLayout(self)
        hl.setContentsMargins(8, 4, 8, 4)
        hl.setSpacing(8)

        lb = QLabel(data["name"])
        lb.setMinimumWidth(150)
        hl.addWidget(lb, 1)

        svc_colors = {
            "subscription": (COLORS["teal_bg"],   COLORS["teal"]),
            "consulting":   (COLORS["amber_bg"],   COLORS["amber_light"]),
        }
        bg, fg = svc_colors.get(
            data.get("service_type", ""), (COLORS["surface"], COLORS["text_sub"])
        )
        svc_badge = badge_label(data.get("service_name", ""), bg, fg)
        svc_badge.setFixedWidth(100)
        hl.addWidget(svc_badge)

        lb_amt = QLabel(fmt_yen(data["monthly_fee"]))
        lb_amt.setFixedWidth(90)
        lb_amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lb_amt.setStyleSheet(
            f"color:{COLORS['text']};background:transparent;border:none;"
        )
        hl.addWidget(lb_amt)

        lb_day = QLabel(data.get("billing_day", ""))
        lb_day.setFixedWidth(80)
        lb_day.setStyleSheet(
            f"color:{COLORS['text_sub']};background:transparent;border:none;"
        )
        hl.addWidget(lb_day)

        btn_edit = QPushButton("編集")
        btn_edit.setFixedWidth(50)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.data["id"]))
        hl.addWidget(btn_edit)

        btn_del = QPushButton("無効化")
        btn_del.setFixedWidth(60)
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.data["id"]))
        hl.addWidget(btn_del)


# ── 顧客ダイアログ ────────────────────────────────────────
class CustomerDialog(QDialog):
    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("顧客を追加" if not data else "顧客を編集")
        self.setMinimumWidth(360)
        self._build()
        if data:
            self._populate()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("例: 株式会社〇〇")
        layout.addRow("顧客名 *", self.name)

        self.service = QComboBox()
        for s in db.get_services():
            self.service.addItem(s["name"], s["id"])
        layout.addRow("サービス *", self.service)

        self.fee = QSpinBox()
        self.fee.setRange(0, 9999999)
        self.fee.setSingleStep(1000)
        _w = QWidget()
        _hl = QHBoxLayout(_w)
        _hl.setContentsMargins(0, 0, 0, 0)
        _hl.setSpacing(6)
        _hl.addWidget(self.fee)
        _hl.addWidget(QLabel("円/月"))
        layout.addRow("月額 *", _w)

        self.billing = QLineEdit()
        self.billing.setPlaceholderText("例: 毎月25日、月末、月初")
        layout.addRow("入金日", self.billing)

        self.contract = QLineEdit()
        self.contract.setPlaceholderText("例: 2025-04-01")
        layout.addRow("契約開始日", self.contract)

        self.note = QLineEdit()
        layout.addRow("メモ", self.note)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self):
        d = self.data
        self.name.setText(d.get("name", ""))
        idx = self.service.findData(d.get("service_id"))
        if idx >= 0:
            self.service.setCurrentIndex(idx)
        self.fee.setValue(d.get("monthly_fee", 0))
        self.billing.setText(d.get("billing_day", ""))
        self.contract.setText(d.get("contract_date", ""))
        self.note.setText(d.get("note", ""))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "入力エラー", "顧客名を入力してください")
            return
        if self.data:
            db.update_customer(
                self.data["id"],
                self.name.text().strip(),
                self.service.currentData(),
                self.fee.value(),
                self.billing.text().strip(),
                self.note.text().strip()
            )
        else:
            db.add_customer(
                self.name.text().strip(),
                self.service.currentData(),
                self.fee.value(),
                self.billing.text().strip(),
                self.contract.text().strip(),
                self.note.text().strip()
            )
        self.accept()
