import sys
import database as db
import encryption as enc
from style import get_stylesheet, APP_NAME

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget,
        QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
        QLabel, QMessageBox, QVBoxLayout
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
except ImportError:
    print("PySide6が見つかりません。setup.bat を実行してインストールしてください。")
    sys.exit(1)

from ui.tab_dashboard import DashboardTab
from ui.tab_budget import BudgetTab
from ui.tab_subscriptions import SubscriptionsTab
from ui.tab_accounts import AccountsTab
from ui.tab_memo import MemoTab
from ui.tab_settings import SettingsTab


# ── グローバル例外ハンドラ ────────────────────────────
def _global_error_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    msg = f"{exc_type.__name__}:\n{exc_value}"
    QMessageBox.critical(
        None,
        "エラーが発生しました",
        f"予期しないエラーが発生しました。\n\n{msg}\n\nアプリを再起動してください。"
    )

sys.excepthook = _global_error_handler


# ── パスワードダイアログ ──────────────────────────────
class UnlockDialog(QDialog):
    """起動時パスワード入力"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — パスワード認証")
        self.setMinimumWidth(320)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        layout = QVBoxLayout(self)

        info = QLabel("データベースが暗号化されています。\nパスワードを入力してください。")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("padding: 10px;")
        layout.addWidget(info)

        form = QFormLayout()
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw.setPlaceholderText("パスワード")
        form.addRow("パスワード", self.pw)
        layout.addLayout(form)

        self.err_lbl = QLabel("")
        self.err_lbl.setStyleSheet("color: #e24b4a; font-size: 12px;")
        self.err_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.err_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("ログイン")
        btns.button(QDialogButtonBox.Cancel).setText("終了")
        btns.accepted.connect(self._try_unlock)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.pw.returnPressed.connect(self._try_unlock)
        self._password = None

    def _try_unlock(self):
        pw = self.pw.text()
        if not pw:
            self.err_lbl.setText("パスワードを入力してください")
            return
        if enc.unlock(db.DB_PATH, pw):
            self._password = pw
            self.accept()
        else:
            self.err_lbl.setText("パスワードが違います。もう一度入力してください。")
            self.pw.clear()
            self.pw.setFocus()

    @property
    def password(self):
        return self._password


# ── メインウィンドウ ──────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self, encryption_password: str = None):
        super().__init__()
        self._enc_password = encryption_password
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

        for tab in (self.tab_pers, self.tab_corp, self.tab_subs,
                    self.tab_accts, self.tab_set):
            if hasattr(tab, "data_changed"):
                tab.data_changed.connect(self._on_data_changed)

        # 暗号化パスワード変更シグナルを受け取る
        if hasattr(self.tab_set, "encryption_password_changed"):
            self.tab_set.encryption_password_changed.connect(self._on_password_changed)

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
        if hasattr(tab, "refresh"):
            tab.refresh(self.year_month)

    def _on_password_changed(self, new_password: str):
        """設定タブでパスワードが変更されたときに保持を更新"""
        self._enc_password = new_password

    def closeEvent(self, event):
        """終了時にDBを再暗号化"""
        if enc.is_enabled() and self._enc_password:
            try:
                enc.lock(db.DB_PATH, self._enc_password)
            except Exception as e:
                QMessageBox.warning(
                    self, "警告",
                    f"終了時の暗号化に失敗しました。\nデータは保存されていますが暗号化されていません。\n{e}"
                )
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet())
    app.setApplicationName(APP_NAME)

    # アイコン設定（exe・タスクバー・ショートカット全てに反映）
    import os
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 暗号化が有効な場合はパスワードを要求
    encryption_password = None
    if enc.is_enabled():
        if not enc.is_available():
            QMessageBox.critical(
                None, "エラー",
                "暗号化ライブラリが見つかりません。\n"
                "setup.bat を再実行してください。"
            )
            sys.exit(1)
        dlg = UnlockDialog()
        if not dlg.exec():
            sys.exit(0)
        encryption_password = dlg.password

    db.init_db()

    win = MainWindow(encryption_password=encryption_password)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
