import sys
import database as db
from style import get_stylesheet, APP_NAME

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QLabel
    from PySide6.QtCore import Qt, QTimer
except ImportError:
    print("PySide6が見つかりません。setup.bat を実行してインストールしてください。")
    sys.exit(1)

from ui.tab_dashboard import DashboardTab
from ui.tab_budget import BudgetTab
from ui.tab_subscriptions import SubscriptionsTab
from ui.tab_accounts import AccountsTab
from ui.tab_memo import MemoTab
from ui.tab_settings import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 820)
        self.year_month = db.current_ym()
        self._build_ui()
        self._refresh_all()

    def _build_ui(self):
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        self.setCentralWidget(tabs)

        self.tab_dash  = DashboardTab()
        self.tab_pers  = BudgetTab("personal")
        self.tab_corp  = BudgetTab("corporate")
        self.tab_subs  = SubscriptionsTab()
        self.tab_accts = AccountsTab()
        self.tab_memo  = MemoTab()
        self.tab_set   = SettingsTab()

        tabs.addTab(self.tab_dash,  "🏠  今月の状況")
        tabs.addTab(self.tab_pers,  "👤  個人")
        tabs.addTab(self.tab_corp,  "🏢  法人")
        tabs.addTab(self.tab_subs,  "📋  サブスク顧客")
        tabs.addTab(self.tab_accts, "🏦  口座残高")
        tabs.addTab(self.tab_memo,  "📌  備忘・TODO")
        tabs.addTab(self.tab_set,   "⚙️  マスタ設定")

        # データ変更シグナルをダッシュボードに伝播
        for tab in (self.tab_pers, self.tab_corp, self.tab_subs,
                    self.tab_accts, self.tab_set):
            if hasattr(tab, "data_changed"):
                tab.data_changed.connect(self._on_data_changed)

        tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs = tabs

    def _refresh_all(self):
        ym = self.year_month
        self.tab_dash.refresh(ym)
        self.tab_pers.refresh(ym)
        self.tab_corp.refresh(ym)
        self.tab_subs.refresh(ym)
        self.tab_accts.refresh(ym)
        self.tab_memo.refresh(ym)
        self.tab_set.refresh(ym)

    def _on_data_changed(self):
        self.tab_dash.refresh(self.year_month)

    def _on_tab_changed(self, idx: int):
        tab = self.tabs.widget(idx)
        ym = self.year_month
        if hasattr(tab, "refresh"):
            tab.refresh(ym)


def main():
    db.init_db()

    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet())
    app.setApplicationName(APP_NAME)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
