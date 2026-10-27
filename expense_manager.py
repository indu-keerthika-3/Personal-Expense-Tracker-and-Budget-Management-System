"""
Core Business Logic and Financial Calculation Engine for Personal Expense Tracker.
Manages database transactions, budgeting calculations, reporting, analytics,
settings, and CSV data generation with precision safety.
"""

import csv
import io
from calendar import monthrange
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database import get_db_connection
from validators import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    format_currency_amount,
    minor_units_to_decimal
)


# ==========================================
# TRANSACTION CRUD OPERATIONS
# ==========================================

def add_transaction(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Inserts a new transaction record into the database."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions (
                    transaction_date, transaction_type, category, amount, payment_method, description
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["transaction_date"],
                    data["transaction_type"],
                    data["category"],
                    int(data["amount"]),
                    data["payment_method"],
                    data.get("description", "").strip()
                )
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_transaction_by_id(tx_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches a single transaction by primary key."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_transaction(tx_id: int, data: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Updates an existing transaction by ID. Returns True if row was updated."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transactions
                SET transaction_date = ?,
                    transaction_type = ?,
                    category = ?,
                    amount = ?,
                    payment_method = ?,
                    description = ?
                WHERE id = ?
                """,
                (
                    data["transaction_date"],
                    data["transaction_type"],
                    data["category"],
                    int(data["amount"]),
                    data["payment_method"],
                    data.get("description", "").strip(),
                    tx_id
                )
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_transaction(tx_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes a transaction by ID. Returns True if deleted."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_transactions(
    filters: Optional[Dict[str, Any]] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves filtered and sorted transactions.
    Supports search, type, category, date range, sorting by date or amount.
    """
    conn = get_db_connection(db_path)
    filters = filters or {}
    query_parts = ["SELECT * FROM transactions WHERE 1=1"]
    params: List[Any] = []

    # Filter by transaction type (Income / Expense)
    t_type = filters.get("transaction_type")
    if t_type and t_type in ("Income", "Expense"):
        query_parts.append("AND transaction_type = ?")
        params.append(t_type)

    # Filter by Category
    category = filters.get("category")
    if category and category != "All":
        query_parts.append("AND category = ?")
        params.append(category)

    # Filter by Start Date
    start_date = filters.get("start_date")
    if start_date:
        query_parts.append("AND transaction_date >= ?")
        params.append(start_date)

    # Filter by End Date
    end_date = filters.get("end_date")
    if end_date:
        query_parts.append("AND transaction_date <= ?")
        params.append(end_date)

    # Search keyword in description or category
    search = filters.get("search")
    if search:
        search_pattern = f"%{search.strip()}%"
        query_parts.append("AND (description LIKE ? OR category LIKE ?)")
        params.extend([search_pattern, search_pattern])

    # Sorting
    sort_col = "transaction_date"
    if sort_by == "amount":
        sort_col = "amount"
    elif sort_by == "category":
        sort_col = "category"
    elif sort_by == "id":
        sort_col = "id"

    order = "ASC" if str(sort_order).lower() == "asc" else "DESC"
    # Secondary order by id desc for deterministic ordering
    query_parts.append(f"ORDER BY {sort_col} {order}, id DESC")

    if limit is not None:
        query_parts.append("LIMIT ?")
        params.append(int(limit))
        if offset is not None:
            query_parts.append("OFFSET ?")
            params.append(int(offset))

    try:
        cursor = conn.cursor()
        cursor.execute(" ".join(query_parts), params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_total_transaction_count(filters: Optional[Dict[str, Any]] = None, db_path: Optional[str] = None) -> int:
    """Returns total count of transactions matching filter conditions."""
    conn = get_db_connection(db_path)
    filters = filters or {}
    query_parts = ["SELECT COUNT(*) as count FROM transactions WHERE 1=1"]
    params: List[Any] = []

    t_type = filters.get("transaction_type")
    if t_type and t_type in ("Income", "Expense"):
        query_parts.append("AND transaction_type = ?")
        params.append(t_type)

    category = filters.get("category")
    if category and category != "All":
        query_parts.append("AND category = ?")
        params.append(category)

    start_date = filters.get("start_date")
    if start_date:
        query_parts.append("AND transaction_date >= ?")
        params.append(start_date)

    end_date = filters.get("end_date")
    if end_date:
        query_parts.append("AND transaction_date <= ?")
        params.append(end_date)

    search = filters.get("search")
    if search:
        search_pattern = f"%{search.strip()}%"
        query_parts.append("AND (description LIKE ? OR category LIKE ?)")
        params.extend([search_pattern, search_pattern])

    try:
        cursor = conn.cursor()
        cursor.execute(" ".join(query_parts), params)
        row = cursor.fetchone()
        return row["count"] if row else 0
    finally:
        conn.close()


def get_recent_transactions(limit: int = 5, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Gets the most recent transactions for the dashboard."""
    return get_transactions(sort_by="date", sort_order="desc", limit=limit, db_path=db_path)


# ==========================================
# FINANCIAL CALCULATIONS & SUMMARIES
# ==========================================

def get_financial_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes accurate financial calculations:
    - Total Income: sum of income in period
    - Total Expenses: sum of expenses in period
    - Net Cash Flow: Total Income - Total Expenses
    - Monthly Budget: Monthly budget for the active month
    - Remaining Budget: Monthly Budget - Eligible Expenses
    - Budget Utilization: (Eligible Expenses / Monthly Budget) * 100
    - Savings Rate: (Net Cash Flow / Total Income) * 100 when Total Income > 0
    """
    conn = get_db_connection(db_path)
    today = date.today()
    target_year = year if year is not None else today.year
    target_month = month if month is not None else today.month

    # If start_date and end_date are not provided, default to current month range
    if not start_date or not end_date:
        _, last_day = monthrange(target_year, target_month)
        month_start = f"{target_year:04d}-{target_month:02d}-01"
        month_end = f"{target_year:04d}-{target_month:02d}-{last_day:02d}"
        query_start = start_date or month_start
        query_end = end_date or month_end
    else:
        query_start = start_date
        query_end = end_date

    try:
        cursor = conn.cursor()

        # 1. Total Income in selected period
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE transaction_type = 'Income'
              AND transaction_date >= ?
              AND transaction_date <= ?
            """,
            (query_start, query_end)
        )
        total_income = cursor.fetchone()["total"]

        # 2. Total Expenses in selected period
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE transaction_type = 'Expense'
              AND transaction_date >= ?
              AND transaction_date <= ?
            """,
            (query_start, query_end)
        )
        total_expenses = cursor.fetchone()["total"]

        # 3. Total Transaction Count in selected period
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM transactions
            WHERE transaction_date >= ?
              AND transaction_date <= ?
            """,
            (query_start, query_end)
        )
        total_tx_count = cursor.fetchone()["count"]

        # 4. Eligible Expenses for the active target month (for budget tracking)
        _, m_last = monthrange(target_year, target_month)
        month_start_str = f"{target_year:04d}-{target_month:02d}-01"
        month_end_str = f"{target_year:04d}-{target_month:02d}-{m_last:02d}"

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE transaction_type = 'Expense'
              AND transaction_date >= ?
              AND transaction_date <= ?
            """,
            (month_start_str, month_end_str)
        )
        eligible_monthly_expenses = cursor.fetchone()["total"]

        # 5. Retrieve Monthly Budget for target month
        cursor.execute(
            "SELECT monthly_limit FROM budgets WHERE year = ? AND month = ?",
            (target_year, target_month)
        )
        budget_row = cursor.fetchone()
        if budget_row:
            monthly_budget = budget_row["monthly_limit"]
        else:
            # Fallback to default setting if exists
            cursor.execute("SELECT value FROM settings WHERE key = 'default_monthly_budget'")
            set_row = cursor.fetchone()
            monthly_budget = int(set_row["value"]) if set_row else 5000000

        # Calculations
        net_cash_flow = total_income - total_expenses
        remaining_budget = monthly_budget - eligible_monthly_expenses

        # Budget Utilization (%)
        if monthly_budget > 0:
            budget_utilization = round((eligible_monthly_expenses / monthly_budget) * 100, 2)
        else:
            budget_utilization = 0.0

        # Savings Rate (%)
        if total_income > 0 and net_cash_flow > 0:
            savings_rate = round((net_cash_flow / total_income) * 100, 2)
        else:
            savings_rate = 0.0

        # Budget Status Warning / Alert
        if budget_utilization > 100.0:
            budget_status = "exceeded"
        elif budget_utilization >= 80.0:
            budget_status = "warning"
        else:
            budget_status = "normal"

        return {
            "start_date": query_start,
            "end_date": query_end,
            "year": target_year,
            "month": target_month,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_cash_flow": net_cash_flow,
            "monthly_budget": monthly_budget,
            "eligible_expenses": eligible_monthly_expenses,
            "remaining_budget": remaining_budget,
            "budget_utilization": budget_utilization,
            "savings_rate": savings_rate,
            "budget_status": budget_status,
            "total_transactions": total_tx_count
        }
    finally:
        conn.close()


# ==========================================
# BUDGET MANAGEMENT OPERATIONS
# ==========================================

def get_monthly_budget(year: int, month: int, db_path: Optional[str] = None) -> int:
    """Returns monthly budget limit for given year and month."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT monthly_limit FROM budgets WHERE year = ? AND month = ?", (year, month))
        row = cursor.fetchone()
        if row:
            return row["monthly_limit"]
        cursor.execute("SELECT value FROM settings WHERE key = 'default_monthly_budget'")
        s_row = cursor.fetchone()
        return int(s_row["value"]) if s_row else 5000000
    finally:
        conn.close()


def set_monthly_budget(year: int, month: int, monthly_limit: int, db_path: Optional[str] = None) -> bool:
    """Sets or updates overall monthly budget."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO budgets (year, month, monthly_limit)
                VALUES (?, ?, ?)
                ON CONFLICT(year, month) DO UPDATE SET
                    monthly_limit = excluded.monthly_limit
                """,
                (year, month, int(monthly_limit))
            )
            return True
    finally:
        conn.close()


def get_category_budgets_with_spending(
    year: int,
    month: int,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Computes category-level budget utilization for all expense categories.
    Returns: category, budget_limit, actual_spending, remaining, utilization_pct, status.
    """
    conn = get_db_connection(db_path)
    _, last_day = monthrange(year, month)
    m_start = f"{year:04d}-{month:02d}-01"
    m_end = f"{year:04d}-{month:02d}-{last_day:02d}"

    try:
        cursor = conn.cursor()

        # Get existing category budgets
        cursor.execute(
            "SELECT category, budget_limit FROM category_budgets WHERE year = ? AND month = ?",
            (year, month)
        )
        budget_map = {row["category"]: row["budget_limit"] for row in cursor.fetchall()}

        # Get actual expense spending per category in that month
        cursor.execute(
            """
            SELECT category, SUM(amount) as total_spent
            FROM transactions
            WHERE transaction_type = 'Expense'
              AND transaction_date >= ?
              AND transaction_date <= ?
            GROUP BY category
            """,
            (m_start, m_end)
        )
        spending_map = {row["category"]: row["total_spent"] for row in cursor.fetchall()}

        results = []
        for cat in EXPENSE_CATEGORIES:
            limit = budget_map.get(cat, 0)
            spent = spending_map.get(cat, 0)
            remaining = limit - spent

            if limit > 0:
                utilization = round((spent / limit) * 100, 2)
                if utilization > 100.0:
                    status = "exceeded"
                elif utilization >= 80.0:
                    status = "warning"
                else:
                    status = "normal"
            else:
                utilization = 0.0
                status = "unbudgeted" if spent > 0 else "no_budget"

            results.append({
                "category": cat,
                "budget_limit": limit,
                "actual_spending": spent,
                "remaining": remaining,
                "utilization_pct": utilization,
                "status": status
            })

        return results
    finally:
        conn.close()


def set_category_budget(
    year: int,
    month: int,
    category: str,
    budget_limit: int,
    db_path: Optional[str] = None
) -> bool:
    """Sets or updates a specific category budget."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO category_budgets (year, month, category, budget_limit)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(year, month, category) DO UPDATE SET
                    budget_limit = excluded.budget_limit
                """,
                (year, month, category, int(budget_limit))
            )
            return True
    finally:
        conn.close()


def delete_category_budget(year: int, month: int, category: str, db_path: Optional[str] = None) -> bool:
    """Removes a category budget for a given month."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM category_budgets WHERE year = ? AND month = ? AND category = ?",
                (year, month, category)
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


# ==========================================
# REPORTING & ANALYTICS
# ==========================================

def get_category_spending_breakdown(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns category-wise expense breakdown with totals and percentages."""
    conn = get_db_connection(db_path)
    query_parts = [
        """
        SELECT category, SUM(amount) as total_amount, COUNT(*) as tx_count
        FROM transactions
        WHERE transaction_type = 'Expense'
        """
    ]
    params: List[Any] = []
    if start_date:
        query_parts.append("AND transaction_date >= ?")
        params.append(start_date)
    if end_date:
        query_parts.append("AND transaction_date <= ?")
        params.append(end_date)
    query_parts.append("GROUP BY category ORDER BY total_amount DESC")

    try:
        cursor = conn.cursor()
        cursor.execute(" ".join(query_parts), params)
        rows = cursor.fetchall()

        total_expense = sum(r["total_amount"] for r in rows) if rows else 0
        breakdown = []
        for r in rows:
            amt = r["total_amount"]
            pct = round((amt / total_expense) * 100, 2) if total_expense > 0 else 0.0
            breakdown.append({
                "category": r["category"],
                "total_amount": amt,
                "tx_count": r["tx_count"],
                "percentage": pct
            })
        return breakdown
    finally:
        conn.close()


def get_monthly_spending_trends(months_count: int = 6, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns monthly income and expense trends for the last N months.
    Useful for Chart.js visualizations.
    """
    conn = get_db_connection(db_path)
    today = date.today()
    month_keys = []
    labels = []

    # Calculate month slots going back (months_count - 1) to current month
    for i in range(months_count - 1, -1, -1):
        # Approximate month arithmetic
        cur_year = today.year
        cur_month = today.month - i
        while cur_month <= 0:
            cur_month += 12
            cur_year -= 1
        month_keys.append(f"{cur_year:04d}-{cur_month:02d}")
        dt_sample = date(cur_year, cur_month, 1)
        labels.append(dt_sample.strftime("%b %Y"))

    oldest_prefix = month_keys[0]
    newest_prefix = month_keys[-1]

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT strftime('%Y-%m', transaction_date) as ym,
                   transaction_type,
                   SUM(amount) as total
            FROM transactions
            WHERE strftime('%Y-%m', transaction_date) >= ?
              AND strftime('%Y-%m', transaction_date) <= ?
            GROUP BY ym, transaction_type
            """,
            (oldest_prefix, newest_prefix)
        )
        rows = cursor.fetchall()

        income_map = {k: 0 for k in month_keys}
        expense_map = {k: 0 for k in month_keys}

        for r in rows:
            ym = r["ym"]
            t_type = r["transaction_type"]
            if ym in income_map and t_type == "Income":
                income_map[ym] = r["total"]
            elif ym in expense_map and t_type == "Expense":
                expense_map[ym] = r["total"]

        # Convert minor units to standard decimal units (floats) for chart display
        return {
            "labels": labels,
            "month_keys": month_keys,
            "income_minor": [income_map[k] for k in month_keys],
            "expense_minor": [expense_map[k] for k in month_keys],
            "income_data": [round(float(minor_units_to_decimal(income_map[k])), 2) for k in month_keys],
            "expense_data": [round(float(minor_units_to_decimal(expense_map[k])), 2) for k in month_keys]
        }
    finally:
        conn.close()


def get_daily_expense_summary(
    start_date: str,
    end_date: str,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns daily expense totals within date range."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT transaction_date, SUM(amount) as total_spent, COUNT(*) as count
            FROM transactions
            WHERE transaction_type = 'Expense'
              AND transaction_date >= ?
              AND transaction_date <= ?
            GROUP BY transaction_date
            ORDER BY transaction_date ASC
            """,
            (start_date, end_date)
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_weekly_expense_summary(
    start_date: str,
    end_date: str,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Groups expense transactions into 7-day or ISO-week blocks."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT strftime('%Y-W%W', transaction_date) as week_label,
                   MIN(transaction_date) as week_start,
                   MAX(transaction_date) as week_end,
                   SUM(amount) as total_spent,
                   COUNT(*) as count
            FROM transactions
            WHERE transaction_type = 'Expense'
              AND transaction_date >= ?
              AND transaction_date <= ?
            GROUP BY week_label
            ORDER BY week_label ASC
            """,
            (start_date, end_date)
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


# ==========================================
# SETTINGS MANAGEMENT
# ==========================================

def get_all_settings(db_path: Optional[str] = None) -> Dict[str, str]:
    """Retrieves all application settings as key-value pairs."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {r["key"]: r["value"] for r in cursor.fetchall()}
    finally:
        conn.close()


def get_setting(key: str, default: Optional[str] = None, db_path: Optional[str] = None) -> Optional[str]:
    """Retrieves a single setting value."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def update_setting(key: str, value: str, db_path: Optional[str] = None) -> bool:
    """Updates or inserts a setting key-value pair."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, str(value))
            )
            return True
    finally:
        conn.close()


# ==========================================
# CSV EXPORT GENERATION
# ==========================================

def generate_csv_string(filters: Optional[Dict[str, Any]] = None, db_path: Optional[str] = None) -> str:
    """
    Generates CSV formatted text containing transaction records matching filters.
    Includes: ID, Date, Type, Category, Amount, Payment Method, Description, Created At.
    """
    transactions = get_transactions(filters=filters, sort_by="date", sort_order="desc", db_path=db_path)
    settings = get_all_settings(db_path=db_path)
    currency_code = settings.get("currency_code", "INR")
    currency_sym = settings.get("currency_symbol", "₹")

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\r\n")

    # Header Row
    writer.writerow([
        "Transaction ID",
        "Date",
        "Type",
        "Category",
        f"Amount ({currency_code})",
        "Payment Method",
        "Description",
        "Created At"
    ])

    for tx in transactions:
        amount_dec = minor_units_to_decimal(tx["amount"])
        writer.writerow([
            tx["id"],
            tx["transaction_date"],
            tx["transaction_type"],
            tx["category"],
            f"{amount_dec:.2f}",
            tx["payment_method"],
            tx["description"] or "",
            tx["created_at"]
        ])

    return output.getvalue()

