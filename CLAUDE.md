# CLAUDE.md — Cashflow360 プロジェクト引き継ぎ

> このファイルはClaude Codeが最初に読む引き継ぎ書です。
> プロジェクトの全体像・構成・ルール・現状を把握してから作業を開始してください。

---

## プロジェクト概要

**アプリ名:** キャッシュフロー管理（Cashflow360）  
**種別:** Windows デスクトップアプリ（PySide6 + SQLite）  
**目的:** 個人と法人のキャッシュフローを一元管理する個人用ツール  
**オーナー:** 個人利用（1ユーザー）

---

## 技術スタック

| 項目 | 内容 |
|------|------|
| 言語 | Python 3.11+ |
| UI フレームワーク | PySide6（Qt6） |
| DB | SQLite3（標準ライブラリ） |
| 暗号化 | cryptography（Fernet / AES-128） |
| ビルド | PyInstaller（`build.bat`） |
| バージョン管理 | Git + GitHub Desktop |

---

## ディレクトリ構成

```
cashflow-app/
├── CLAUDE.md               ← このファイル
├── main.py                 ← エントリーポイント・ウィンドウ定義
├── database.py             ← 全DB操作（SQLite）
├── encryption.py           ← DBファイルの暗号化・復号
├── style.py                ← カラーパレット・スタイルシート
├── requirements.txt        ← PySide6, cryptography
├── setup.bat               ← 初回セットアップ
├── run.bat                 ← アプリ起動
├── build.bat               ← PyInstallerでexe化
├── キャッシュフロー管理.pyw  ← ダブルクリック起動用
├── キャッシュフロー管理.spec ← PyInstaller設定
└── ui/
    ├── __init__.py
    ├── tab_dashboard.py    ← 今月の状況タブ
    ├── tab_budget.py       ← 個人・法人 予実タブ（共通クラス）
    ├── tab_subscriptions.py← サブスク顧客管理タブ
    ├── tab_accounts.py     ← 口座残高・積立タブ
    ├── tab_memo.py         ← 備忘・TODOタブ
    ├── tab_settings.py     ← マスタ設定タブ
    └── widgets/
        ├── __init__.py
        └── common.py       ← 共通ウィジェット（MetricCard, badge_label等）
```

---

## データベース設計（SQLite）

**DBパス:** `~/cashflow_app/data.db`  
**暗号化時:** `~/cashflow_app/.data.enc`（平文DBは起動時のみ展開）

### テーブル一覧

| テーブル | 役割 |
|----------|------|
| `services` | サービスマスタ（subscription / consulting / project） |
| `goals` | 月次目標（収入目標・支出上限・MRR目標） |
| `income_items` | 収入予定・実績（planned/confirmed） |
| `fixed_expenses_master` | 固定費マスタ（monthly_budget自動展開の元） |
| `monthly_budget` | 月次予実（fixed_auto / sinking / variable） |
| `extra_expenses` | 予定外支出（前半/後半） |
| `subscription_customers` | サブスク顧客 |
| `customer_payments` | 顧客の月次入金確認 |
| `accounts` | 口座（operating / savings） |
| `sinking_funds` | 積立マスタ |
| `sinking_fund_balance` | 積立月次スナップショット |
| `memos` | 備忘・TODO（payment / income / todo） |

### 重要なDB関数（database.py）

```python
# 月次予実の自動展開（固定費マスタ→monthly_budget）
ensure_monthly_budget(year_month, category)

# 顧客支払いレコードの自動生成
ensure_customer_payments(year_month)

# サマリー取得（収入・支出の予定/実績）
get_summary(year_month, category) -> dict

# MRR合計
get_mrr() -> int
```

---

## アーキテクチャ上のルール

### カテゴリ
- `"personal"` = 個人
- `"corporate"` = 法人
- タブ・DB・全関数でこの2値を使う

### 年月フォーマット
- 常に `"YYYY-MM"` 形式（例: `"2025-05"`）
- `db.current_ym()` で現在月を取得

### UI パターン
- 各タブは `refresh(year_month: str)` メソッドを持つ
- データ変更時は `data_changed = Signal()` を emit → `tab_dashboard` が自動更新
- スタイルは必ず `style.py` の `COLORS` 辞書を参照（ハードコード禁止）

### エラーハンドリング
- `database.py` の全関数には `@_db_op` デコレータが必要
- UIの予期せぬエラーは `main.py` の `_global_error_handler` が捕捉

### 暗号化の仕組み
```
起動時: .data.enc → (Fernetで復号) → data.db（一時展開）
終了時: data.db → (Fernetで再暗号化) → .data.enc
```
- `encryption.py` の `is_enabled()` で暗号化有効判定
- パスワードは `MainWindow._enc_password` に保持（メモリのみ）

---

## 既知の制限・TODO

- [ ] `tab_settings.py` に `encryption_password_changed` シグナルが参照されているが未実装
      → `main.py` の `_on_password_changed` がシグナルを受け取る想定
- [ ] パスワード変更UI（`encryption.py` に `change_password()` は実装済み、UIが未実装）
- [ ] 月次レポート出力機能（CSV/PDFエクスポート）未実装
- [ ] `fixed_auto` / `sinking` タイプの実績入力が手動不可
      → `_BudgetItemRow._edit_actual()` は `variable` のみ有効

---

## よく使うコマンド

```bash
# アプリ起動
python main.py

# DB初期化（初回のみ）
python database.py

# exe ビルド（Windows）
build.bat
```

---

## コーディング規約

- **日本語UI:** ラベル・メッセージは全て日本語
- **型ヒント:** 関数引数・戻り値に付ける（既存コードに合わせる）
- **DB接続:** `get_connection()` を使い、必ず `conn.close()` する
- **新テーブル:** `init_db()` 内の `executescript` に追記
- **新DB関数:** `@_db_op` デコレータを必ずつける
- **新タブ:** `main.py` の `_build_ui()` と `_refresh_all()` に追加

---

## 作業開始時の確認事項

1. `python -c "import PySide6; print('OK')"` でPySide6が入っているか確認
2. `python database.py` でDBが正常に初期化されるか確認
3. `python main.py` でアプリが起動するか確認
4. 変更後は必ず `python main.py` で動作確認してからコミット
