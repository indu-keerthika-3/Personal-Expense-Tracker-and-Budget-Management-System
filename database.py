"""
Database Module for Personal Expense Tracker and Budget Management System.
Handles SQLite connection, schema definition, migration/initialization, and indexing.
"""

import os
import sqlite3
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "expense_tracker.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Income', 'Expense')),
    category TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK(amount > 0),
    payment_method TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    monthly_limit INTEGER NOT NULL CHECK(monthly_limit >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, month)
);

CREATE TABLE IF NOT EXISTS category_budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    category TEXT NOT NULL,
    budget_limit INTEGER NOT NULL CHECK(budget_limit >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, month, category)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Performance and Query Optimization Indexes
CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_trans_cat ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_budget_ym ON budgets(year, month);
CREATE INDEX IF NOT EXISTS idx_cat_budget_ym ON category_budgets(year, month, category);
"""

DEFAULT_SETTINGS = {
    "currency_symbol": "₹",
    "currency_code": "INR",
    "default_monthly_budget": "5000000",  # minor units: 50,000.00
    "theme_preference": "light"
}


def get_db_path(custom_path: Optional[str] = None) -> str:
    """Return configured database path or default."""
    if custom_path:
        return custom_path
    return os.environ.get("EXPENSE_TRACKER_DB", DEFAULT_DB_PATH)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish a connection to SQLite database with Row factory enabled
    and Foreign Key constraints enforced.
    """
    target_path = get_db_path(db_path)
    # Ensure directory exists if path is not in-memory
    if target_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initialize SQLite database tables, indexes, and seed default settings if missing.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
            cursor = conn.cursor()
            for key, val in DEFAULT_SETTINGS.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, val)
                )
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database successfully initialized at {get_db_path()}")

