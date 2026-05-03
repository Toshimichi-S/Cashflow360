import sqlite3
import os
from datetime import datetime, date
from pathlib import Path


DB_PATH = Path.home() / "cashflow_app" / "data.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
    -- サービスマスタ
    CREATE TABLE IF NOT EXISTS services (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        type        TEXT NOT NULL DEFAULT 'subscription',
        standard_fee INTEGER DEFAULT 0,
        description TEXT DEFAULT '',
        is_active   INTEGER DEFAULT 1,
        created_at  TEXT DEFAULT ''
    );

    -- 目標設定
    CREATE TABLE IF NOT EXISTS goals (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        year_month      TEXT NOT NULL,
        category        TEXT NOT NULL,
        income_target   INTEGER DEFAULT 0,
        expense_limit   INTEGER DEFAULT 0,
        mrr_target      INTEGER DEFAULT 0,
        updated_at      TEXT DEFAULT '',
        UNIQUE(year_month, category)
    );

    -- 収入予定・実績
    CREATE TABLE IF NOT EXISTS income_items (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        year_month      TEXT NOT NULL,
        category        TEXT NOT NULL,
        source          TEXT NOT NULL,
        service_type    TEXT DEFAULT 'other',
        planned_amount  INTEGER DEFAULT 0,
        actual_amount   INTEGER DEFAULT 0,
        status          TEXT DEFAULT 'planned',
        expected_date   TEXT DEFAULT '',
        confirmed_date  TEXT DEFAULT '',
        note            TEXT DEFAULT '',
        created_at      TEXT DEFAULT ''
    );

    -- 固定費マスタ
    CREATE TABLE IF NOT EXISTS fixed_expenses_master (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        category        TEXT NOT NULL,
        monthly_amount  INTEGER DEFAULT 0,
        expense_type    TEXT DEFAULT 'subscription',
        is_seasonal     INTEGER DEFAULT 0,
        is_active       INTEGER DEFAULT 1,
        sort_order      INTEGER DEFAULT 0,
        created_at      TEXT DEFAULT ''
    );

    -- 月次予実（変動費・固定費の実績）
    CREATE TABLE IF NOT EXISTS monthly_budget (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        year_month      TEXT NOT NULL,
        category        TEXT NOT NULL,
        master_id       INTEGER DEFAULT 0,
        item_name       TEXT NOT NULL,
        item_type       TEXT NOT NULL DEFAULT 'fixed_auto',
        budget_amount   INTEGER DEFAULT 0,
        actual_amount   INTEGER DEFAULT 0,
        note            TEXT DEFAULT '',
        updated_at      TEXT DEFAULT '',
        UNIQUE(year_month, category, master_id, item_type)
    );

    -- 予定外支出（月2回まとめ入力）
    CREATE TABLE IF NOT EXISTS extra_expenses (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        year_month  TEXT NOT NULL,
        category    TEXT NOT NULL,
        period      TEXT NOT NULL,
        item_name   TEXT NOT NULL,
        amount      INTEGER DEFAULT 0,
        note        TEXT DEFAULT '',
        created_at  TEXT DEFAULT ''
    );

    -- サブスク顧客
    CREATE TABLE IF NOT EXISTS subscription_customers (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        service_id      INTEGER NOT NULL,
        monthly_fee     INTEGER DEFAULT 0,
        billing_day     TEXT DEFAULT 'end',
        contract_date   TEXT DEFAULT '',
        is_active       INTEGER DEFAULT 1,
        note            TEXT DEFAULT '',
        created_at      TEXT DEFAULT '',
        FOREIGN KEY (service_id) REFERENCES services(id)
    );

    -- 顧客の月次入金確認
    CREATE TABLE IF NOT EXISTS customer_payments (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id     INTEGER NOT NULL,
        year_month      TEXT NOT NULL,
        amount          INTEGER DEFAULT 0,
        status          TEXT DEFAULT 'pending',
        confirmed_date  TEXT DEFAULT '',
        UNIQUE(customer_id, year_month),
        FOREIGN KEY (customer_id) REFERENCES subscription_customers(id)
    );

    -- 口座
    CREATE TABLE IF NOT EXISTS accounts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        category        TEXT NOT NULL,
        account_type    TEXT DEFAULT 'operating',
        balance         INTEGER DEFAULT 0,
        updated_at      TEXT DEFAULT '',
        note            TEXT DEFAULT '',
        sort_order      INTEGER DEFAULT 0,
        is_active       INTEGER DEFAULT 1
    );

    -- 積立マスタ
    CREATE TABLE IF NOT EXISTS sinking_funds (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        category        TEXT NOT NULL,
        annual_budget   INTEGER DEFAULT 0,
        monthly_amount  INTEGER DEFAULT 0,
        target_months   TEXT DEFAULT '',
        carry_over      INTEGER DEFAULT 1,
        account_id      INTEGER DEFAULT 0,
        is_active       INTEGER DEFAULT 1,
        created_at      TEXT DEFAULT ''
    );

    -- 積立口座残高（月次スナップショット）
    CREATE TABLE IF NOT EXISTS sinking_fund_balance (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_id     INTEGER NOT NULL,
        year_month  TEXT NOT NULL,
        balance     INTEGER DEFAULT 0,
        deposited   INTEGER DEFAULT 0,
        withdrawn   INTEGER DEFAULT 0,
        note        TEXT DEFAULT '',
        updated_at  TEXT DEFAULT '',
        UNIQUE(fund_id, year_month),
        FOREIGN KEY (fund_id) REFERENCES sinking_funds(id)
    );

    -- 備忘・TODO
    CREATE TABLE IF NOT EXISTS memos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        memo_type   TEXT NOT NULL DEFAULT 'todo',
        category    TEXT DEFAULT 'personal',
        amount      INTEGER DEFAULT 0,
        due_date    TEXT DEFAULT '',
        is_done     INTEGER DEFAULT 0,
        note        TEXT DEFAULT '',
        created_at  TEXT DEFAULT ''
    );
    """)

    conn.commit()
    conn.close()


def current_ym():
    return datetime.now().strftime("%Y-%m")


# ── Goals ──────────────────────────────────────────────
def get_goal(year_month: str, category: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM goals WHERE year_month=? AND category=?",
        (year_month, category)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"income_target": 0, "expense_limit": 0, "mrr_target": 0}


def save_goal(year_month: str, category: str, income_target: int,
              expense_limit: int, mrr_target: int = 0):
    conn = get_connection()
    conn.execute("""
        INSERT INTO goals (year_month, category, income_target, expense_limit, mrr_target, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(year_month, category) DO UPDATE SET
            income_target=excluded.income_target,
            expense_limit=excluded.expense_limit,
            mrr_target=excluded.mrr_target,
            updated_at=excluded.updated_at
    """, (year_month, category, income_target, expense_limit, mrr_target))
    conn.commit()
    conn.close()


def copy_goal_from_prev(year_month: str, category: str):
    from datetime import datetime
    dt = datetime.strptime(year_month, "%Y-%m")
    if dt.month == 1:
        prev_ym = f"{dt.year-1}-12"
    else:
        prev_ym = f"{dt.year}-{dt.month-1:02d}"
    prev = get_goal(prev_ym, category)
    save_goal(year_month, category,
              prev.get("income_target", 0),
              prev.get("expense_limit", 0),
              prev.get("mrr_target", 0))


# ── Income Items ──────────────────────────────────────
def get_income_items(year_month: str, category: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM income_items WHERE year_month=? AND category=? ORDER BY created_at",
        (year_month, category)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_income_item(year_month, category, source, service_type, planned_amount,
                    expected_date="", note=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO income_items
        (year_month, category, source, service_type, planned_amount, expected_date, note)
        VALUES (?,?,?,?,?,?,?)
    """, (year_month, category, source, service_type, planned_amount, expected_date, note))
    conn.commit()
    conn.close()


def confirm_income(item_id: int, actual_amount: int):
    conn = get_connection()
    conn.execute("""
        UPDATE income_items SET status='confirmed',
        actual_amount=?, confirmed_date=date('now','localtime')
        WHERE id=?
    """, (actual_amount, item_id))
    conn.commit()
    conn.close()


def delete_income_item(item_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM income_items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


# ── Fixed Expenses Master ─────────────────────────────
def get_fixed_masters(category: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM fixed_expenses_master WHERE category=? AND is_active=1 ORDER BY sort_order, id",
        (category,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_fixed_master(category, name, monthly_amount, expense_type="subscription",
                     is_seasonal=0):
    conn = get_connection()
    conn.execute("""
        INSERT INTO fixed_expenses_master
        (category, name, monthly_amount, expense_type, is_seasonal)
        VALUES (?,?,?,?,?)
    """, (category, name, monthly_amount, expense_type, is_seasonal))
    conn.commit()
    conn.close()


def update_fixed_master(master_id, name, monthly_amount, is_seasonal):
    conn = get_connection()
    conn.execute("""
        UPDATE fixed_expenses_master
        SET name=?, monthly_amount=?, is_seasonal=?
        WHERE id=?
    """, (name, monthly_amount, is_seasonal, master_id))
    conn.commit()
    conn.close()


def delete_fixed_master(master_id):
    conn = get_connection()
    conn.execute("UPDATE fixed_expenses_master SET is_active=0 WHERE id=?", (master_id,))
    conn.commit()
    conn.close()


# ── Monthly Budget (予実) ─────────────────────────────
def get_monthly_budget(year_month: str, category: str) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM monthly_budget
        WHERE year_month=? AND category=?
        ORDER BY item_type, id
    """, (year_month, category)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def ensure_monthly_budget(year_month: str, category: str):
    existing = get_monthly_budget(year_month, category)
    existing_ids = {r["master_id"] for r in existing}
    masters = get_fixed_masters(category)
    sinking = get_sinking_funds(category)

    conn = get_connection()
    for m in masters:
        if m["id"] not in existing_ids:
            conn.execute("""
                INSERT OR IGNORE INTO monthly_budget
                (year_month, category, master_id, item_name, item_type, budget_amount)
                VALUES (?,?,?,?,?,?)
            """, (year_month, category, m["id"], m["name"],
                  "fixed_auto", m["monthly_amount"]))

    for s in sinking:
        key = 90000 + s["id"]
        if key not in existing_ids:
            conn.execute("""
                INSERT OR IGNORE INTO monthly_budget
                (year_month, category, master_id, item_name, item_type, budget_amount)
                VALUES (?,?,?,?,?,?)
            """, (year_month, category, key,
                  f"積立振替：{s['name']}", "sinking", s["monthly_amount"]))

    conn.commit()
    conn.close()


def update_budget_actual(budget_id: int, actual_amount: int, note: str = ""):
    conn = get_connection()
    conn.execute("""
        UPDATE monthly_budget SET actual_amount=?, note=?,
        updated_at=datetime('now','localtime') WHERE id=?
    """, (actual_amount, note, budget_id))
    conn.commit()
    conn.close()


def update_budget_target(budget_id: int, budget_amount: int):
    conn = get_connection()
    conn.execute(
        "UPDATE monthly_budget SET budget_amount=? WHERE id=?",
        (budget_amount, budget_id)
    )
    conn.commit()
    conn.close()


def add_variable_budget_item(year_month, category, item_name, budget_amount):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO monthly_budget
        (year_month, category, master_id, item_name, item_type, budget_amount)
        VALUES (?,?,?,?,?,?)
    """, (year_month, category, 0, item_name, "variable", budget_amount))
    conn.commit()
    conn.close()


# ── Extra Expenses (予定外支出) ──────────────────────
def get_extra_expenses(year_month: str, category: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM extra_expenses WHERE year_month=? AND category=? ORDER BY period, id",
        (year_month, category)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_extra_expense(year_month, category, period, item_name, amount, note=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO extra_expenses
        (year_month, category, period, item_name, amount, note)
        VALUES (?,?,?,?,?,?)
    """, (year_month, category, period, item_name, amount, note))
    conn.commit()
    conn.close()


def delete_extra_expense(expense_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM extra_expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()


# ── Summary helpers ──────────────────────────────────
def get_summary(year_month: str, category: str) -> dict:
    income = get_income_items(year_month, category)
    budget = get_monthly_budget(year_month, category)
    extras = get_extra_expenses(year_month, category)

    income_planned = sum(i["planned_amount"] for i in income)
    income_actual = sum(
        i["actual_amount"] if i["status"] == "confirmed" else 0
        for i in income
    )
    expense_budget = sum(b["budget_amount"] for b in budget)
    expense_actual = (
        sum(b["actual_amount"] for b in budget)
        + sum(e["amount"] for e in extras)
    )
    return {
        "income_planned": income_planned,
        "income_actual": income_actual,
        "expense_budget": expense_budget,
        "expense_actual": expense_actual,
    }


# ── Services ─────────────────────────────────────────
def get_services() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM services WHERE is_active=1 ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_service(name, stype, standard_fee, description=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO services (name, type, standard_fee, description) VALUES (?,?,?,?)",
        (name, stype, standard_fee, description)
    )
    conn.commit()
    conn.close()


def update_service(sid, name, stype, standard_fee, description):
    conn = get_connection()
    conn.execute("""
        UPDATE services SET name=?, type=?, standard_fee=?, description=?
        WHERE id=?
    """, (name, stype, standard_fee, description, sid))
    conn.commit()
    conn.close()


# ── Subscription Customers ────────────────────────────
def get_customers(active_only=True) -> list:
    conn = get_connection()
    q = """
        SELECT c.*, s.name as service_name, s.type as service_type
        FROM subscription_customers c
        LEFT JOIN services s ON c.service_id = s.id
    """
    if active_only:
        q += " WHERE c.is_active=1"
    q += " ORDER BY c.service_id, c.id"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_customer(name, service_id, monthly_fee, billing_day, contract_date="", note=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO subscription_customers
        (name, service_id, monthly_fee, billing_day, contract_date, note)
        VALUES (?,?,?,?,?,?)
    """, (name, service_id, monthly_fee, billing_day, contract_date, note))
    conn.commit()
    conn.close()


def update_customer(cid, name, service_id, monthly_fee, billing_day, note):
    conn = get_connection()
    conn.execute("""
        UPDATE subscription_customers
        SET name=?, service_id=?, monthly_fee=?, billing_day=?, note=?
        WHERE id=?
    """, (name, service_id, monthly_fee, billing_day, note, cid))
    conn.commit()
    conn.close()


def deactivate_customer(cid):
    conn = get_connection()
    conn.execute("UPDATE subscription_customers SET is_active=0 WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def ensure_customer_payments(year_month: str):
    customers = get_customers()
    conn = get_connection()
    for c in customers:
        conn.execute("""
            INSERT OR IGNORE INTO customer_payments
            (customer_id, year_month, amount, status)
            VALUES (?,?,?,?)
        """, (c["id"], year_month, c["monthly_fee"], "pending"))
    conn.commit()
    conn.close()


def get_customer_payments(year_month: str) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT cp.*, c.name as customer_name, s.name as service_name
        FROM customer_payments cp
        JOIN subscription_customers c ON cp.customer_id = c.id
        JOIN services s ON c.service_id = s.id
        WHERE cp.year_month=? AND c.is_active=1
        ORDER BY s.id, c.id
    """, (year_month,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def confirm_customer_payment(payment_id: int):
    conn = get_connection()
    conn.execute("""
        UPDATE customer_payments SET status='confirmed',
        confirmed_date=date('now','localtime')
        WHERE id=?
    """, (payment_id,))
    conn.commit()
    conn.close()


def get_mrr() -> int:
    customers = get_customers()
    return sum(c["monthly_fee"] for c in customers)


# ── Accounts ─────────────────────────────────────────
def get_accounts(category: str = None) -> list:
    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM accounts WHERE category=? AND is_active=1 ORDER BY sort_order, id",
            (category,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM accounts WHERE is_active=1 ORDER BY category, sort_order, id"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_account(name, category, account_type, balance=0, note=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO accounts (name, category, account_type, balance, note)
        VALUES (?,?,?,?,?)
    """, (name, category, account_type, balance, note))
    conn.commit()
    conn.close()


def update_account_balance(account_id: int, balance: int):
    conn = get_connection()
    conn.execute("""
        UPDATE accounts SET balance=?, updated_at=datetime('now','localtime')
        WHERE id=?
    """, (balance, account_id))
    conn.commit()
    conn.close()


def delete_account(account_id: int):
    conn = get_connection()
    conn.execute("UPDATE accounts SET is_active=0 WHERE id=?", (account_id,))
    conn.commit()
    conn.close()


def get_total_balance(category: str = None) -> int:
    accounts = get_accounts(category)
    return sum(a["balance"] for a in accounts
               if a["account_type"] in ("operating", "savings"))


# ── Sinking Funds ─────────────────────────────────────
def get_sinking_funds(category: str = None) -> list:
    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM sinking_funds WHERE category=? AND is_active=1 ORDER BY id",
            (category,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM sinking_funds WHERE is_active=1 ORDER BY category, id"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_sinking_fund(name, category, annual_budget, target_months="", carry_over=1):
    monthly = annual_budget // 12
    conn = get_connection()
    conn.execute("""
        INSERT INTO sinking_funds
        (name, category, annual_budget, monthly_amount, target_months, carry_over)
        VALUES (?,?,?,?,?,?)
    """, (name, category, annual_budget, monthly, target_months, carry_over))
    conn.commit()
    conn.close()


def update_sinking_fund(fid, name, category, annual_budget, target_months, carry_over):
    monthly = annual_budget // 12
    conn = get_connection()
    conn.execute("""
        UPDATE sinking_funds
        SET name=?, category=?, annual_budget=?, monthly_amount=?,
            target_months=?, carry_over=?
        WHERE id=?
    """, (name, category, annual_budget, monthly, target_months, carry_over, fid))
    conn.commit()
    conn.close()


def delete_sinking_fund(fid):
    conn = get_connection()
    conn.execute("UPDATE sinking_funds SET is_active=0 WHERE id=?", (fid,))
    conn.commit()
    conn.close()


def get_sinking_fund_balance(fund_id: int, year_month: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM sinking_fund_balance WHERE fund_id=? AND year_month=?",
        (fund_id, year_month)
    ).fetchone()
    conn.close()
    return dict(row) if row else {"balance": 0, "deposited": 0, "withdrawn": 0}


def update_sinking_fund_balance(fund_id: int, year_month: str,
                                 balance: int, deposited: int = 0, withdrawn: int = 0):
    conn = get_connection()
    conn.execute("""
        INSERT INTO sinking_fund_balance
        (fund_id, year_month, balance, deposited, withdrawn, updated_at)
        VALUES (?,?,?,?,?,datetime('now','localtime'))
        ON CONFLICT(fund_id, year_month) DO UPDATE SET
            balance=excluded.balance,
            deposited=excluded.deposited,
            withdrawn=excluded.withdrawn,
            updated_at=excluded.updated_at
    """, (fund_id, year_month, balance, deposited, withdrawn))
    conn.commit()
    conn.close()


# ── Memos ─────────────────────────────────────────────
def get_memos(done: bool = None) -> list:
    conn = get_connection()
    q = "SELECT * FROM memos"
    params = []
    if done is not None:
        q += " WHERE is_done=?"
        params.append(1 if done else 0)
    q += " ORDER BY is_done, due_date, id"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_memo(title, memo_type, category, amount=0, due_date="", note=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO memos (title, memo_type, category, amount, due_date, note)
        VALUES (?,?,?,?,?,?)
    """, (title, memo_type, category, amount, due_date, note))
    conn.commit()
    conn.close()


def toggle_memo_done(memo_id: int, done: bool):
    conn = get_connection()
    conn.execute("UPDATE memos SET is_done=? WHERE id=?", (1 if done else 0, memo_id))
    conn.commit()
    conn.close()


def delete_memo(memo_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM memos WHERE id=?", (memo_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"DB initialized at {DB_PATH}")
