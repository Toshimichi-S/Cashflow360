from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QComboBox, QDialogButtonBox, QMessageBox,
    QGridLayout, QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
import database as db
from style import COLORS
from ui.widgets.common import (
    MetricCard, make_card, section_label, fmt_yen,
    badge_label, spacer_h, BudgetRow, sub_label
)

# 列幅の定数（ヘッダーと行で完全に一致させる）
COL_BADGE  = 50
COL_NAME   = 160
COL_BUDGET = 88
COL_ACTUAL = 88
COL_DIFF   = 96
COL_BTN    = 76


class BudgetTab(QWidget):
    """個人・法人 共通の予実タブ"""
    data_changed = Signal()

    def __init__(self, category: str, parent=None):
        super().__init__(parent)
        self.category = category
        self.year_month = db.current_ym()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        # ── ヘッダー行 ──────────────────────────────────
        hdr_card = QFrame()
        hdr_card.setStyleSheet(
            f"background:{COLORS['surface']};"
            f"border:1px solid {COLORS['border']};"
            f"border-radius:8px;"
        )
        hdr_inner = QHBoxLayout(hdr_card)
        hdr_inner.setContentsMargins(16, 12, 16, 12)

        cat_name = "個人" if self.category == "personal" else "法人"
        self.lbl_title = QLabel(f"{cat_name} — 予実管理")
        self.lbl_title.setObjectName("heading")
        hdr_inner.addWidget(self.lbl_title)
        hdr_inner.addStretch()

        self.btn_prev = QPushButton("← 前月")
        self.btn_next = QPushButton("翌月 →")
        self.btn_prev.setFixedWidth(72)
        self.btn_next.setFixedWidth(72)
        self.btn_prev.clicked.connect(self._prev_month)
        self.btn_next.clicked.connect(self._next_month)
        hdr_inner.addWidget(self.btn_prev)
        hdr_inner.addWidget(self.btn_next)
        root.addWidget(hdr_card)

        # ── サマリーカード ──────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(10)
        self.mc_income_plan   = MetricCard("収入 予定")
        self.mc_income_actual = MetricCard("収入 確認済", color=COLORS["green"])
        self.mc_expense_budget= MetricCard("支出 予算")
        self.mc_expense_actual= MetricCard("支出 実績", color=COLORS["amber"])
        grid.addWidget(self.mc_income_plan,    0, 0)
        grid.addWidget(self.mc_income_actual,  0, 1)
        grid.addWidget(self.mc_expense_budget, 0, 2)
        grid.addWidget(self.mc_expense_actual, 0, 3)
        root.addLayout(grid)

        # ── スクロールエリア ────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self.vl = QVBoxLayout(content)
        self.vl.setSpacing(14)
        self.vl.setContentsMargins(0, 0, 4, 0)

        # ── 収入セクション ──────────────────────────────
        inc_hdr = QHBoxLayout()
        inc_hdr.addWidget(section_label("収入（入金確認）"))
        inc_hdr.addStretch()
        btn_add_inc = QPushButton("＋ 収入を追加")
        btn_add_inc.clicked.connect(self._add_income)
        inc_hdr.addWidget(btn_add_inc)
        self.vl.addLayout(inc_hdr)

        self.card_income = make_card()
        self.income_layout = QVBoxLayout(self.card_income)
        self.income_layout.setContentsMargins(0, 0, 0, 0)
        self.income_layout.setSpacing(0)
        self.vl.addWidget(self.card_income)

        # ── 支出セクション ──────────────────────────────
        exp_hdr = QHBoxLayout()
        exp_hdr.addWidget(section_label("支出 予実"))
        exp_hdr.addStretch()
        if self.category == "personal":
            btn_add_budget = QPushButton("＋ 変動費を追加")
            btn_add_budget.clicked.connect(self._add_variable_budget)
            exp_hdr.addWidget(btn_add_budget)
        self.vl.addLayout(exp_hdr)

        # 列ヘッダー（定数と一致）
        hdr_row = QWidget()
        hdr_row.setStyleSheet(
            f"background:{COLORS['surface']};"
            f"border:1px solid {COLORS['border']};"
            f"border-radius:6px 6px 0 0;"
        )
        hdr_hl = QHBoxLayout(hdr_row)
        hdr_hl.setContentsMargins(10, 6, 10, 6)
        hdr_hl.setSpacing(8)

        def _hdr_lbl(text, width, align=Qt.AlignLeft | Qt.AlignVCenter):
            lb = QLabel(text)
            lb.setStyleSheet(
                f"color:{COLORS['text_dim']};font-size:11px;"
                f"font-weight:bold;letter-spacing:1px;background:transparent;"
            )
            lb.setAlignment(align)
            if width > 0:
                lb.setFixedWidth(width)
            return lb

        hdr_hl.addWidget(_hdr_lbl("種別", COL_BADGE))
        hdr_hl.addWidget(_hdr_lbl("項目", COL_NAME))
        hdr_hl.addWidget(_hdr_lbl("", -1), 1)   # バーのスペース
        hdr_hl.addWidget(_hdr_lbl("予算",   COL_BUDGET, Qt.AlignRight | Qt.AlignVCenter))
        hdr_hl.addWidget(_hdr_lbl("実績",   COL_ACTUAL, Qt.AlignRight | Qt.AlignVCenter))
        hdr_hl.addWidget(_hdr_lbl("差異",   COL_DIFF,   Qt.AlignRight | Qt.AlignVCenter))
        hdr_hl.addWidget(_hdr_lbl("",       COL_BTN))   # ボタン列のスペーサー
        self.vl.addWidget(hdr_row)

        self.card_budget = make_card()
        self.card_budget.setStyleSheet(
            f"QFrame#card {{"
            f"  background-color:{COLORS['card']};"
            f"  border:1px solid {COLORS['border']};"
            f"  border-top:none;"
            f"  border-radius:0 0 8px 8px;"
            f"}}"
        )
        self.budget_layout = QVBoxLayout(self.card_budget)
        self.budget_layout.setContentsMargins(0, 2, 0, 2)
        self.budget_layout.setSpacing(0)
        self.vl.addWidget(self.card_budget)

        # ── 予定外支出 ──────────────────────────────────
        extra_hdr = QHBoxLayout()
        extra_hdr.addWidget(section_label("予定外支出（まとめ入力）"))
        extra_hdr.addStretch()
        btn_add_extra = QPushButton("＋ 追加")
        btn_add_extra.clicked.connect(self._add_extra)
        extra_hdr.addWidget(btn_add_extra)
        self.vl.addLayout(extra_hdr)

        self.card_extra = make_card()
        self.extra_layout = QVBoxLayout(self.card_extra)
        self.extra_layout.setContentsMargins(14, 10, 14, 10)
        self.extra_layout.setSpacing(4)
        self.vl.addWidget(self.card_extra)

        self.vl.addStretch()

    # ── 月移動 ───────────────────────────────────────────
    def _prev_month(self):
        from datetime import datetime
        dt = datetime.strptime(self.year_month, "%Y-%m")
        self.year_month = (f"{dt.year-1}-12" if dt.month == 1
                           else f"{dt.year}-{dt.month-1:02d}")
        self.refresh(self.year_month)

    def _next_month(self):
        from datetime import datetime
        dt = datetime.strptime(self.year_month, "%Y-%m")
        self.year_month = (f"{dt.year+1}-01" if dt.month == 12
                           else f"{dt.year}-{dt.month+1:02d}")
        self.refresh(self.year_month)

    # ── データ更新 ────────────────────────────────────────
    def refresh(self, year_month: str):
        self.year_month = year_month
        cat_name = "個人" if self.category == "personal" else "法人"
        self.lbl_title.setText(f"{cat_name} — 予実管理　{year_month}")

        db.ensure_monthly_budget(year_month, self.category)

        summary = db.get_summary(year_month, self.category)
        goal    = db.get_goal(year_month, self.category)
        inc_tgt = goal.get("income_target", 0)
        exp_lim = goal.get("expense_limit", 0)

        self.mc_income_plan.update(fmt_yen(summary["income_planned"]))
        pct = int(summary["income_actual"] / inc_tgt * 100) if inc_tgt else 0
        self.mc_income_actual.update(
            fmt_yen(summary["income_actual"]),
            f"目標 {fmt_yen(inc_tgt)} の {pct}%",
            pct, COLORS["green"]
        )
        self.mc_expense_budget.update(fmt_yen(summary["expense_budget"]))
        pct = int(summary["expense_actual"] / exp_lim * 100) if exp_lim else 0
        col = COLORS["red"] if pct > 90 else COLORS["amber"]
        self.mc_expense_actual.update(
            fmt_yen(summary["expense_actual"]),
            f"上限 {fmt_yen(exp_lim)} の {pct}%",
            pct, col
        )

        self._refresh_income()
        self._refresh_budget()
        self._refresh_extra()

    def _refresh_income(self):
        _clear_layout(self.income_layout)
        items = db.get_income_items(self.year_month, self.category)
        if not items:
            lb = QLabel("　収入が登録されていません")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:14px 0;")
            self.income_layout.addWidget(lb)
            return
        for inc in items:
            row = _IncomeRow(inc, self.category)
            row.confirmed.connect(self._on_income_confirmed)
            row.deleted.connect(self._on_income_deleted)
            self.income_layout.addWidget(row)

    def _refresh_budget(self):
        _clear_layout(self.budget_layout)
        items = db.get_monthly_budget(self.year_month, self.category)
        if not items:
            lb = QLabel("　支出項目が未設定です（マスタ設定から追加できます）")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:14px 0;")
            self.budget_layout.addWidget(lb)
            return
        for item in items:
            row = _BudgetItemRow(item)
            row.actual_updated.connect(self._on_actual_updated)
            self.budget_layout.addWidget(row)

    def _refresh_extra(self):
        _clear_layout(self.extra_layout)
        extras = db.get_extra_expenses(self.year_month, self.category)
        if not extras:
            lb = QLabel("予定外支出なし")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};")
            self.extra_layout.addWidget(lb)
            return
        for e in extras:
            row = QHBoxLayout()
            row.setSpacing(10)
            period_badge = badge_label(
                "前半" if e["period"] == "first" else "後半",
                COLORS["surface"], COLORS["text_sub"]
            )
            row.addWidget(period_badge)
            row.addWidget(QLabel(e["item_name"]), 1)
            amt = QLabel(fmt_yen(e["amount"]))
            amt.setStyleSheet(f"color:{COLORS['amber_light']};font-weight:bold;")
            row.addWidget(amt)
            btn_del = QPushButton("削除")
            btn_del.setObjectName("danger")
            btn_del.setFixedWidth(50)
            btn_del.clicked.connect(lambda _, eid=e["id"]: self._del_extra(eid))
            row.addWidget(btn_del)

            w = QWidget()
            w.setLayout(row)
            w.setStyleSheet(
                f"border-bottom:1px solid {COLORS['border']};background:transparent;"
            )
            self.extra_layout.addWidget(w)

    # ── アクション ────────────────────────────────────────
    def _on_income_confirmed(self):
        self.refresh(self.year_month)
        self.data_changed.emit()

    def _on_income_deleted(self):
        self.refresh(self.year_month)
        self.data_changed.emit()

    def _on_actual_updated(self):
        self.refresh(self.year_month)
        self.data_changed.emit()

    def _add_income(self):
        dlg = AddIncomeDialog(self.year_month, self.category, self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _add_variable_budget(self):
        dlg = AddVariableBudgetDialog(self.year_month, self.category, self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _add_extra(self):
        dlg = AddExtraDialog(self.year_month, self.category, self)
        if dlg.exec():
            self.refresh(self.year_month)
            self.data_changed.emit()

    def _del_extra(self, eid: int):
        db.delete_extra_expense(eid)
        self.refresh(self.year_month)
        self.data_changed.emit()


# ── ユーティリティ ────────────────────────────────────────
def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


# ── 収入行 ────────────────────────────────────────────────
class _IncomeRow(QWidget):
    confirmed = Signal()
    deleted   = Signal()

    def __init__(self, data: dict, category: str, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(48)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};background:transparent;"
        )

        hl = QHBoxLayout(self)
        hl.setContentsMargins(12, 4, 12, 4)
        hl.setSpacing(10)

        type_map = {
            "salary":       ("給与",     COLORS["purple_bg"],  COLORS["purple_light"]),
            "subscription": ("サブスク", COLORS["teal_bg"],    COLORS["teal"]),
            "consulting":   ("コンサル", COLORS["amber_bg"],   COLORS["amber_light"]),
            "project":      ("受託",     COLORS["coral_bg"],   COLORS["coral"]),
            "other":        ("その他",   COLORS["surface"],    COLORS["text_sub"]),
        }
        t = data.get("service_type", "other")
        t_name, t_bg, t_fg = type_map.get(t, ("その他", COLORS["surface"], COLORS["text_sub"]))
        hl.addWidget(badge_label(t_name, t_bg, t_fg))

        lb = QLabel(data["source"])
        lb.setMinimumWidth(160)
        hl.addWidget(lb, 1)

        lb_date = QLabel(data.get("expected_date") or "")
        lb_date.setFixedWidth(70)
        lb_date.setStyleSheet(f"color:{COLORS['text_sub']};background:transparent;")
        hl.addWidget(lb_date)

        lb_amt = QLabel(fmt_yen(data["planned_amount"]))
        lb_amt.setFixedWidth(100)
        lb_amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lb_amt.setStyleSheet(
            f"color:{COLORS['text']};font-weight:bold;background:transparent;"
        )
        hl.addWidget(lb_amt)

        if data["status"] == "confirmed":
            st = badge_label("確認済", COLORS["green_bg"], COLORS["green_light"])
            hl.addWidget(st)
        else:
            btn = QPushButton("入金確認 ✓")
            btn.setObjectName("success")
            btn.setFixedWidth(90)
            btn.clicked.connect(self._confirm)
            hl.addWidget(btn)

        btn_del = QPushButton("✕")
        btn_del.setFixedWidth(30)
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(self._delete)
        hl.addWidget(btn_del)

    def _confirm(self):
        db.confirm_income(self.data["id"], self.data["planned_amount"])
        self.confirmed.emit()

    def _delete(self):
        db.delete_income_item(self.data["id"])
        self.deleted.emit()


# ── 予実行（全タイプに実績入力ボタン付き） ────────────────
class _BudgetItemRow(QWidget):
    actual_updated = Signal()

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(52)
        self.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']};background:transparent;"
        )

        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 4, 10, 4)
        hl.setSpacing(8)

        # 種別バッジ
        type_colors = {
            "fixed_auto": (COLORS["purple_bg"],  COLORS["purple_light"], "自動"),
            "sinking":    (COLORS["teal_bg"],     COLORS["teal"],         "積立"),
            "variable":   (COLORS["blue_bg"],     COLORS["blue_light"],   "変動"),
        }
        itype = data.get("item_type", "variable")
        bg, fg, tname = type_colors.get(itype, (COLORS["surface"], COLORS["text_sub"], ""))
        badge = badge_label(tname, bg, fg)
        badge.setFixedWidth(COL_BADGE)
        hl.addWidget(badge)

        # 項目名
        lb = QLabel(data["item_name"])
        lb.setMinimumWidth(COL_NAME)
        lb.setStyleSheet("background:transparent;border:none;")
        hl.addWidget(lb, 0)

        # プログレスバー（stretch で余白を埋める）
        budget = data["budget_amount"]
        actual = data["actual_amount"]
        pct    = int(actual / budget * 100) if budget else 0

        bar_col = (COLORS["red"]   if pct > 100 else
                   COLORS["amber"] if pct > 85  else
                   COLORS["teal"]  if itype == "sinking" else
                   COLORS["blue"])

        bar = QProgressBar()
        bar.setFixedHeight(10)
        bar.setRange(0, 100)
        bar.setValue(min(pct, 100))
        bar.setTextVisible(False)
        bar.setStyleSheet(
            f"QProgressBar{{"
            f"  background:{COLORS['surface']};"
            f"  border:1px solid {COLORS['border']};"
            f"  border-radius:5px;"
            f"}}"
            f"QProgressBar::chunk{{"
            f"  background:{bar_col};"
            f"  border-radius:5px;"
            f"}}"
        )
        hl.addWidget(bar, 1)

        # 予算
        lb_budget = QLabel(fmt_yen(budget))
        lb_budget.setFixedWidth(COL_BUDGET)
        lb_budget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lb_budget.setStyleSheet(
            f"color:{COLORS['text_sub']};background:transparent;border:none;"
        )
        hl.addWidget(lb_budget)

        # 実績
        lb_actual = QLabel(fmt_yen(actual))
        lb_actual.setFixedWidth(COL_ACTUAL)
        lb_actual.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lb_actual.setStyleSheet(
            f"color:{COLORS['text']};font-weight:bold;background:transparent;border:none;"
        )
        hl.addWidget(lb_actual)

        # 差異
        diff = budget - actual
        diff_text  = f"+{fmt_yen(diff)}" if diff >= 0 else fmt_yen(diff)
        diff_color = COLORS["green"] if diff >= 0 else COLORS["red"]
        diff_lbl = QLabel(diff_text)
        diff_lbl.setFixedWidth(COL_DIFF)
        diff_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        diff_lbl.setStyleSheet(
            f"color:{diff_color};font-weight:bold;background:transparent;border:none;"
        )
        hl.addWidget(diff_lbl)

        # 実績入力ボタン（全タイプに表示）
        btn_edit = QPushButton("実績入力")
        btn_edit.setFixedWidth(COL_BTN)
        btn_edit.setFixedHeight(28)
        btn_edit.clicked.connect(self._edit_actual)
        hl.addWidget(btn_edit)

    def _edit_actual(self):
        from PySide6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getInt(
            self, "実績入力",
            f"「{self.data['item_name']}」の実績額を入力してください：",
            self.data["actual_amount"], 0, 99999999
        )
        if ok:
            db.update_budget_actual(self.data["id"], val)
            self.actual_updated.emit()


# ── ダイアログ群 ──────────────────────────────────────────
class AddIncomeDialog(QDialog):
    def __init__(self, year_month, category, parent=None):
        super().__init__(parent)
        self.year_month = year_month
        self.category   = category
        self.setWindowTitle("収入を追加")
        self.setMinimumWidth(380)
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.source = QLineEdit()
        self.source.setPlaceholderText("例: 給与、〇〇社コンサル料")
        layout.addRow("収入元 *", self.source)

        self.stype = QComboBox()
        for k, v in [("salary","給与"), ("subscription","サブスク"),
                     ("consulting","コンサル"), ("project","受託"), ("other","その他")]:
            self.stype.addItem(v, k)
        layout.addRow("種別", self.stype)

        self.amount = QSpinBox()
        self.amount.setRange(0, 99999999)
        self.amount.setSingleStep(1000)
        _w, _hl = _spin_row(self.amount, "円")
        layout.addRow("予定額 *", _w)

        self.exp_date = QLineEdit()
        self.exp_date.setPlaceholderText("例: 5/25  または  月末")
        layout.addRow("入金予定日", self.exp_date)

        self.note = QLineEdit()
        layout.addRow("メモ", self.note)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        if not self.source.text().strip():
            QMessageBox.warning(self, "入力エラー", "収入元を入力してください")
            return
        if self.amount.value() == 0:
            QMessageBox.warning(self, "入力エラー", "金額を入力してください")
            return
        db.add_income_item(
            self.year_month, self.category,
            self.source.text().strip(),
            self.stype.currentData(),
            self.amount.value(),
            self.exp_date.text().strip(),
            self.note.text().strip()
        )
        self.accept()


class AddVariableBudgetDialog(QDialog):
    def __init__(self, year_month, category, parent=None):
        super().__init__(parent)
        self.year_month = year_month
        self.category   = category
        self.setWindowTitle("変動費を追加")
        self.setMinimumWidth(340)
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.name = QLineEdit()
        self.name.setPlaceholderText("例: 外食費、雑費")
        layout.addRow("項目名 *", self.name)

        self.budget = QSpinBox()
        self.budget.setRange(0, 99999999)
        self.budget.setSingleStep(1000)
        _w, _hl = _spin_row(self.budget, "円")
        layout.addRow("目標額 *", _w)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "入力エラー", "項目名を入力してください")
            return
        db.add_variable_budget_item(
            self.year_month, self.category,
            self.name.text().strip(), self.budget.value()
        )
        self.accept()


class AddExtraDialog(QDialog):
    def __init__(self, year_month, category, parent=None):
        super().__init__(parent)
        self.year_month = year_month
        self.category   = category
        self.setWindowTitle("予定外支出を追加")
        self.setMinimumWidth(340)
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.period = QComboBox()
        self.period.addItem("前半（〜15日）",    "first")
        self.period.addItem("後半（16日〜月末）", "second")
        layout.addRow("期間", self.period)

        self.name = QLineEdit()
        self.name.setPlaceholderText("例: 外食費オーバー、臨時購入")
        layout.addRow("項目名 *", self.name)

        self.amount = QSpinBox()
        self.amount.setRange(0, 99999999)
        self.amount.setSingleStep(500)
        _w, _hl = _spin_row(self.amount, "円")
        layout.addRow("金額 *", _w)

        self.note = QLineEdit()
        layout.addRow("メモ", self.note)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "入力エラー", "項目名を入力してください")
            return
        if self.amount.value() == 0:
            QMessageBox.warning(self, "入力エラー", "金額を入力してください")
            return
        db.add_extra_expense(
            self.year_month, self.category,
            self.period.currentData(),
            self.name.text().strip(),
            self.amount.value(),
            self.note.text().strip()
        )
        self.accept()


# ── ヘルパー ──────────────────────────────────────────────
def _spin_row(spinbox: QSpinBox, unit: str):
    w  = QWidget()
    hl = QHBoxLayout(w)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.setSpacing(6)
    hl.addWidget(spinbox)
    lbl = QLabel(unit)
    lbl.setStyleSheet(f"color:{COLORS['text_sub']};background:transparent;")
    hl.addWidget(lbl)
    hl.addStretch()
    return w, hl
