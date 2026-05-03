from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
import database as db
from style import COLORS
from ui.widgets.common import (
    MetricCard, make_card, section_label, fmt_yen, badge_label, sub_label
)


class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self.layout_main = QVBoxLayout(content)
        self.layout_main.setSpacing(12)
        self.layout_main.setContentsMargins(0, 0, 0, 0)

        # ── 今月の収支サマリー ──
        self.layout_main.addWidget(section_label("今月の状況"))

        self.grid_metrics = QGridLayout()
        self.grid_metrics.setSpacing(10)

        self.mc_p_income  = MetricCard("個人 収入", color=COLORS["purple"])
        self.mc_p_expense = MetricCard("個人 支出", color=COLORS["blue"])
        self.mc_c_income  = MetricCard("法人 売上", color=COLORS["purple"])
        self.mc_c_expense = MetricCard("法人 経費", color=COLORS["amber"])

        self.grid_metrics.addWidget(self.mc_p_income,  0, 0)
        self.grid_metrics.addWidget(self.mc_p_expense, 0, 1)
        self.grid_metrics.addWidget(self.mc_c_income,  0, 2)
        self.grid_metrics.addWidget(self.mc_c_expense, 0, 3)
        self.layout_main.addLayout(self.grid_metrics)

        # ── 口座残高 + 入金待ち ──
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.card_balance = make_card()
        bal_layout = QVBoxLayout(self.card_balance)
        bal_layout.setContentsMargins(14, 12, 14, 12)
        lbl = section_label("口座残高合計")
        bal_layout.addWidget(lbl)
        self.lbl_balance_total = QLabel("¥0")
        self.lbl_balance_total.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{COLORS['text']};"
        )
        bal_layout.addWidget(self.lbl_balance_total)
        self.lbl_balance_sub = sub_label("個人 ¥0 ／ 法人 ¥0")
        bal_layout.addWidget(self.lbl_balance_sub)
        row2.addWidget(self.card_balance)

        self.card_mrr = make_card()
        mrr_layout = QVBoxLayout(self.card_mrr)
        mrr_layout.setContentsMargins(14, 12, 14, 12)
        mrr_layout.addWidget(section_label("MRR（サブスク月次売上）"))
        self.lbl_mrr = QLabel("¥0")
        self.lbl_mrr.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{COLORS['teal']};"
        )
        mrr_layout.addWidget(self.lbl_mrr)
        self.lbl_mrr_sub = sub_label("顧客 0社")
        mrr_layout.addWidget(self.lbl_mrr_sub)
        row2.addWidget(self.card_mrr)

        self.layout_main.addLayout(row2)

        # ── 入金待ち一覧 ──
        self.layout_main.addWidget(section_label("入金確認待ち"))
        self.card_pending = make_card()
        self.pending_layout = QVBoxLayout(self.card_pending)
        self.pending_layout.setContentsMargins(14, 10, 14, 10)
        self.pending_layout.setSpacing(0)
        self.layout_main.addWidget(self.card_pending)

        # ── 積立状況 ──
        self.layout_main.addWidget(section_label("積立状況"))
        self.card_sinking = make_card()
        self.sinking_layout = QHBoxLayout(self.card_sinking)
        self.sinking_layout.setContentsMargins(14, 12, 14, 12)
        self.sinking_layout.setSpacing(10)
        self.layout_main.addWidget(self.card_sinking)

        self.layout_main.addStretch()

    def refresh(self, year_month: str):
        self._ym = year_month

        # 目標取得
        goal_p = db.get_goal(year_month, "personal")
        goal_c = db.get_goal(year_month, "corporate")

        # 収支サマリー
        sum_p = db.get_summary(year_month, "personal")
        sum_c = db.get_summary(year_month, "corporate")

        # 個人収入
        p_inc = sum_p["income_actual"]
        p_inc_tgt = goal_p.get("income_target", 0)
        pct = int(p_inc / p_inc_tgt * 100) if p_inc_tgt else 0
        self.mc_p_income.update(
            fmt_yen(p_inc),
            f"目標 {fmt_yen(p_inc_tgt)} の{pct}%",
            pct, COLORS["purple"]
        )

        # 個人支出
        p_exp = sum_p["expense_actual"]
        p_exp_lim = goal_p.get("expense_limit", 0)
        pct = int(p_exp / p_exp_lim * 100) if p_exp_lim else 0
        col = COLORS["red"] if pct > 90 else COLORS["blue"]
        self.mc_p_expense.update(
            fmt_yen(p_exp),
            f"上限 {fmt_yen(p_exp_lim)} の{pct}%",
            pct, col
        )

        # 法人売上
        c_inc = sum_c["income_actual"]
        c_inc_tgt = goal_c.get("income_target", 0)
        pct = int(c_inc / c_inc_tgt * 100) if c_inc_tgt else 0
        self.mc_c_income.update(
            fmt_yen(c_inc),
            f"目標 {fmt_yen(c_inc_tgt)} の{pct}%",
            pct, COLORS["purple"]
        )

        # 法人経費
        c_exp = sum_c["expense_actual"]
        c_exp_lim = goal_c.get("expense_limit", 0)
        pct = int(c_exp / c_exp_lim * 100) if c_exp_lim else 0
        col = COLORS["red"] if pct > 90 else COLORS["amber"]
        self.mc_c_expense.update(
            fmt_yen(c_exp),
            f"上限 {fmt_yen(c_exp_lim)} の{pct}%",
            pct, col
        )

        # 口座残高
        bal_p = db.get_total_balance("personal")
        bal_c = db.get_total_balance("corporate")
        self.lbl_balance_total.setText(fmt_yen(bal_p + bal_c))
        self.lbl_balance_sub.setText(
            f"個人 {fmt_yen(bal_p)} ／ 法人 {fmt_yen(bal_c)}"
        )

        # MRR
        customers = db.get_customers()
        mrr = sum(c["monthly_fee"] for c in customers)
        self.lbl_mrr.setText(fmt_yen(mrr))
        self.lbl_mrr_sub.setText(f"顧客 {len(customers)}社")

        # 入金待ち一覧
        self._refresh_pending(year_month)

        # 積立状況
        self._refresh_sinking(year_month)

    def _refresh_pending(self, year_month: str):
        # clear
        while self.pending_layout.count():
            item = self.pending_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        incomes_p = db.get_income_items(year_month, "personal")
        incomes_c = db.get_income_items(year_month, "corporate")
        pending = [i for i in incomes_p + incomes_c if i["status"] == "planned"]

        if not pending:
            lb = QLabel("入金待ちの項目はありません")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:8px;")
            self.pending_layout.addWidget(lb)
            return

        for item in pending[:5]:
            row = QHBoxLayout()
            row.setContentsMargins(0, 5, 0, 5)

            cat_badge = badge_label(
                "個人" if item["category"] == "personal" else "法人",
                COLORS["amber_bg"] if item["category"] == "personal"
                else COLORS["blue_bg"],
                COLORS["amber_light"] if item["category"] == "personal"
                else COLORS["blue_light"]
            )
            row.addWidget(cat_badge)

            lb_name = QLabel(item["source"])
            row.addWidget(lb_name, 1)

            lb_date = QLabel(item["expected_date"] or "日程未定")
            lb_date.setStyleSheet(f"color:{COLORS['text_sub']};")
            row.addWidget(lb_date)

            lb_amt = QLabel(fmt_yen(item["planned_amount"]))
            lb_amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lb_amt.setStyleSheet(
                f"color:{COLORS['green_light']};font-weight:bold;min-width:80px;"
            )
            row.addWidget(lb_amt)

            wrapper = QWidget()
            wrapper.setLayout(row)
            wrapper.setStyleSheet(
                f"border-bottom:1px solid {COLORS['border']};background:transparent;"
            )
            self.pending_layout.addWidget(wrapper)

        if len(pending) > 5:
            lb = QLabel(f"…ほか {len(pending)-5}件")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:6px;")
            self.pending_layout.addWidget(lb)

    def _refresh_sinking(self, year_month: str):
        while self.sinking_layout.count():
            item = self.sinking_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        funds = db.get_sinking_funds()
        if not funds:
            lb = QLabel("積立項目が未登録です（マスタ設定から追加できます）")
            lb.setStyleSheet(f"color:{COLORS['text_dim']};padding:8px;")
            self.sinking_layout.addWidget(lb)
            return

        for fund in funds:
            bal = db.get_sinking_fund_balance(fund["id"], year_month)
            balance = bal.get("balance", 0)
            annual = fund["annual_budget"]
            pct = int(balance / annual * 100) if annual else 0

            card = make_card()
            card.setMinimumWidth(160)
            vl = QVBoxLayout(card)
            vl.setContentsMargins(12, 10, 12, 10)
            vl.setSpacing(4)

            cat_badge = badge_label(
                "個人" if fund["category"] == "personal" else "法人",
                COLORS["amber_bg"] if fund["category"] == "personal"
                else COLORS["blue_bg"],
                COLORS["amber_light"] if fund["category"] == "personal"
                else COLORS["blue_light"]
            )
            vl.addWidget(cat_badge)

            name_lbl = QLabel(fund["name"])
            name_lbl.setStyleSheet("font-weight:bold;font-size:12px;background:transparent;border:none;")
            vl.addWidget(name_lbl)

            bal_lbl = QLabel(f"{fmt_yen(balance)} / {fmt_yen(annual)}")
            bal_lbl.setStyleSheet(f"font-size:12px;color:{COLORS['text']};background:transparent;border:none;")
            vl.addWidget(bal_lbl)

            from PySide6.QtWidgets import QProgressBar
            bar = QProgressBar()
            bar.setFixedHeight(5)
            bar.setRange(0, 100)
            bar.setValue(pct)
            bar.setStyleSheet(
                f"QProgressBar{{background:{COLORS['surface']};border:none;border-radius:2px;}}"
                f"QProgressBar::chunk{{background:{COLORS['teal']};border-radius:2px;}}"
            )
            vl.addWidget(bar)

            pct_lbl = QLabel(f"{pct}%  月積立 {fmt_yen(fund['monthly_amount'])}")
            pct_lbl.setStyleSheet(f"font-size:11px;color:{COLORS['text_sub']};background:transparent;border:none;")
            vl.addWidget(pct_lbl)

            self.sinking_layout.addWidget(card)

        self.sinking_layout.addStretch()
