"""
Flask Web Application for Personal Expense Tracker and Budget Management System.
Handles routes, session CSRF protection, template context, flash notifications,
and clean separation of HTTP handling from business logic.
"""

import os
import secrets
from datetime import date, datetime
from typing import Any, Dict

from flask import (
    Flask,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from database import init_db
import expense_manager as manager
from validators import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    PAYMENT_METHODS,
    SUPPORTED_CURRENCIES,
    format_currency_amount,
    minor_units_to_decimal,
    parse_amount_to_minor_units,
    validate_budget_data,
    validate_category_budget_data,
    validate_date_range,
    validate_transaction_data
)

app = Flask(__name__)
# Secure secret key with persistent or generated fallback
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# Initialize database on startup
init_db()


# ==========================================
# CSRF PROTECTION & SECURITY HELPERS
# ==========================================

def generate_csrf_token() -> str:
    """Generates or retrieves CSRF token from current session."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)
    return session["csrf_token"]


def verify_csrf_token() -> bool:
    """Verifies that submitted CSRF token matches session token."""
    token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
    if not token or token != session.get("csrf_token"):
        return False
    return True


@app.before_request
def csrf_protect():
    """Validates CSRF token for state-modifying POST requests."""
    if request.method == "POST":
        # Ignore CSRF only if explicit exemption is set (none by default)
        if not verify_csrf_token():
            flash("Security check failed: Invalid or expired CSRF session token. Please try again.", "danger")
            return redirect(request.referrer or url_for("dashboard"))


# ==========================================
# CONTEXT PROCESSORS & JINJA2 FILTERS
# ==========================================

@app.context_processor
def inject_global_data():
    """Injects common variables into all Jinja2 templates."""
    settings = manager.get_all_settings()
    currency_symbol = settings.get("currency_symbol", "₹")
    currency_code = settings.get("currency_code", "INR")
    today = date.today()

    return {
        "csrf_token": generate_csrf_token,
        "currency_symbol": currency_symbol,
        "currency_code": currency_code,
        "expense_categories": EXPENSE_CATEGORIES,
        "income_categories": INCOME_CATEGORIES,
        "payment_methods": PAYMENT_METHODS,
        "supported_currencies": SUPPORTED_CURRENCIES,
        "current_year": today.year,
        "current_month": today.month,
        "today_iso": today.isoformat(),
        "active_endpoint": request.endpoint
    }


@app.template_filter("currency")
def currency_filter(amount_minor: Any) -> str:
    """Formats minor units to formatted currency string."""
    try:
        val = int(amount_minor) if amount_minor is not None else 0
    except (ValueError, TypeError):
        val = 0
    settings = manager.get_all_settings()
    symbol = settings.get("currency_symbol", "₹")
    return format_currency_amount(val, symbol=symbol)


@app.template_filter("to_decimal_str")
def to_decimal_str_filter(amount_minor: Any) -> str:
    """Converts minor units to decimal float string for input values: 150050 -> '1500.50'."""
    try:
        val = int(amount_minor) if amount_minor is not None else 0
    except (ValueError, TypeError):
        val = 0
    return f"{minor_units_to_decimal(val):.2f}"


@app.template_filter("format_date")
def format_date_filter(date_str: str) -> str:
    """Formats ISO YYYY-MM-DD date to human-readable 'DD Mon YYYY'."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except ValueError:
        return date_str


# ==========================================
# CORE APPLICATION ROUTES
# ==========================================

@app.route("/")
def dashboard():
    """
    Feature 1: Financial Dashboard.
    Displays summary cards, monthly budget progress, recent transactions, and Chart.js visuals.
    """
    today = date.today()
    summary = manager.get_financial_summary(year=today.year, month=today.month)
    recent_transactions = manager.get_recent_transactions(limit=6)
    category_spending = manager.get_category_spending_breakdown(
        start_date=summary["start_date"],
        end_date=summary["end_date"]
    )
    monthly_trends = manager.get_monthly_spending_trends(months_count=6)

    return render_template(
        "dashboard.html",
        summary=summary,
        recent_transactions=recent_transactions,
        category_spending=category_spending,
        monthly_trends=monthly_trends
    )


@app.route("/transactions")
def transactions_list():
    """
    Feature 4: Transaction Management.
    Displays paginated/searchable list of all transactions with filters and sorting.
    """
    search = request.args.get("search", "").strip()
    t_type = request.args.get("type", "All").strip()
    category = request.args.get("category", "All").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    sort_by = request.args.get("sort_by", "date").strip()
    sort_order = request.args.get("sort_order", "desc").strip()

    # Validate date range if provided
    is_valid_range, range_err = validate_date_range(start_date or None, end_date or None)
    if not is_valid_range:
        flash(range_err, "warning")
        start_date, end_date = "", ""

    filters = {
        "search": search if search else None,
        "transaction_type": t_type if t_type in ("Income", "Expense") else None,
        "category": category if category != "All" else None,
        "start_date": start_date if start_date else None,
        "end_date": end_date if end_date else None
    }

    # Pagination logic
    page = request.args.get("page", 1, type=int)
    per_page = 15
    total_count = manager.get_total_transaction_count(filters=filters)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    tx_list = manager.get_transactions(
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=per_page,
        offset=offset
    )

    # Compute quick totals for the filtered set
    filtered_all = manager.get_transactions(filters=filters)
    filtered_income = sum(t["amount"] for t in filtered_all if t["transaction_type"] == "Income")
    filtered_expense = sum(t["amount"] for t in filtered_all if t["transaction_type"] == "Expense")

    return render_template(
        "transactions.html",
        transactions=tx_list,
        total_count=total_count,
        page=page,
        total_pages=total_pages,
        search=search,
        selected_type=t_type,
        selected_category=category,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        filtered_income=filtered_income,
        filtered_expense=filtered_expense
    )


@app.route("/transactions/add", methods=["GET", "POST"])
def add_transaction():
    """
    Feature 2: Add Income and Expense Transactions.
    Renders the form on GET and validates and saves on POST.
    """
    if request.method == "POST":
        is_valid, err_msg, clean_data = validate_transaction_data(request.form)
        if not is_valid:
            flash(err_msg, "danger")
            return render_template(
                "add_transaction.html",
                form_data=request.form
            )

        try:
            tx_id = manager.add_transaction(clean_data)
            flash(f"Transaction of {format_currency_amount(clean_data['amount'])} recorded successfully!", "success")
            return redirect(url_for("transactions_list"))
        except Exception as e:
            flash(f"Database error while saving transaction: {str(e)}", "danger")
            return render_template("add_transaction.html", form_data=request.form)

    # GET request: default to today's date
    default_form = {
        "transaction_date": date.today().isoformat(),
        "transaction_type": "Expense",
        "category": "Food",
        "payment_method": "UPI"
    }
    return render_template("add_transaction.html", form_data=default_form)


@app.route("/transactions/<int:tx_id>/edit", methods=["GET", "POST"])
def edit_transaction(tx_id: int):
    """
    Feature 4: Edit Transaction.
    Pre-fills existing transaction and updates upon valid POST submission.
    """
    tx = manager.get_transaction_by_id(tx_id)
    if not tx:
        flash("Transaction not found or has already been deleted.", "warning")
        return redirect(url_for("transactions_list"))

    if request.method == "POST":
        is_valid, err_msg, clean_data = validate_transaction_data(request.form)
        if not is_valid:
            flash(err_msg, "danger")
            return render_template("edit_transaction.html", transaction=tx, form_data=request.form)

        try:
            success = manager.update_transaction(tx_id, clean_data)
            if success:
                flash("Transaction updated successfully!", "success")
                return redirect(url_for("transactions_list"))
            else:
                flash("Failed to update transaction. Record may not exist.", "danger")
        except Exception as e:
            flash(f"Error updating transaction: {str(e)}", "danger")

    return render_template("edit_transaction.html", transaction=tx, form_data=tx)


@app.route("/transactions/<int:tx_id>/delete", methods=["POST"])
def delete_transaction(tx_id: int):
    """
    Feature 4: Delete Transaction.
    Requires POST request with CSRF token; prompts confirmation via UI.
    """
    tx = manager.get_transaction_by_id(tx_id)
    if not tx:
        flash("Transaction not found or already deleted.", "warning")
        return redirect(url_for("transactions_list"))

    try:
        manager.delete_transaction(tx_id)
        flash("Transaction deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting transaction: {str(e)}", "danger")

    return redirect(request.referrer or url_for("transactions_list"))


@app.route("/budgets", methods=["GET", "POST"])
def budgets():
    """
    Feature 5: Budget Management.
    Sets monthly overall budget and individual category spending limits.
    Calculates actual spending, utilization %, remaining budget, and warnings.
    """
    today = date.today()
    try:
        selected_year = int(request.args.get("year", today.year))
        selected_month = int(request.args.get("month", today.month))
        if not (1 <= selected_month <= 12 and 2000 <= selected_year <= 2100):
            selected_year, selected_month = today.year, today.month
    except (ValueError, TypeError):
        selected_year, selected_month = today.year, today.month

    # Handle form submissions for budgets
    if request.method == "POST":
        action = request.form.get("action")

        if action == "set_monthly_budget":
            is_valid, err_msg, b_data = validate_budget_data(request.form)
            if not is_valid:
                flash(err_msg, "danger")
            else:
                manager.set_monthly_budget(b_data["year"], b_data["month"], b_data["monthly_limit"])
                flash(f"Monthly budget for {b_data['month']:02d}/{b_data['year']} updated successfully!", "success")
            return redirect(url_for("budgets", year=request.form.get("year"), month=request.form.get("month")))

        elif action == "set_category_budget":
            is_valid, err_msg, cb_data = validate_category_budget_data(request.form)
            if not is_valid:
                flash(err_msg, "danger")
            else:
                manager.set_category_budget(
                    cb_data["year"],
                    cb_data["month"],
                    cb_data["category"],
                    cb_data["budget_limit"]
                )
                flash(f"Budget for category '{cb_data['category']}' saved successfully!", "success")
            return redirect(url_for("budgets", year=request.form.get("year"), month=request.form.get("month")))

        elif action == "delete_category_budget":
            cat = request.form.get("category", "")
            manager.delete_category_budget(selected_year, selected_month, cat)
            flash(f"Budget limit for '{cat}' removed.", "info")
            return redirect(url_for("budgets", year=selected_year, month=selected_month))

    # Retrieve data for selected month
    monthly_budget = manager.get_monthly_budget(selected_year, selected_month)
    summary = manager.get_financial_summary(year=selected_year, month=selected_month)
    category_budgets = manager.get_category_budgets_with_spending(selected_year, selected_month)

    # Calculate allocated budget vs overall budget
    total_allocated_categories = sum(cb["budget_limit"] for cb in category_budgets)

    return render_template(
        "budgets.html",
        selected_year=selected_year,
        selected_month=selected_month,
        monthly_budget=monthly_budget,
        summary=summary,
        category_budgets=category_budgets,
        total_allocated_categories=total_allocated_categories
    )


@app.route("/reports")
def reports():
    """
    Feature 6: Financial Reports and Analytics.
    Provides daily, weekly, and monthly summaries, category comparisons, and charts.
    """
    today = date.today()
    period = request.args.get("period", "this_month")
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Determine date range based on period
    if period == "this_month":
        start_date = date(today.year, today.month, 1).isoformat()
        end_date = today.isoformat()
    elif period == "last_month":
        first_this_month = date(today.year, today.month, 1)
        last_day_prev_month = first_this_month - manager.timedelta(days=1)
        start_date = date(last_day_prev_month.year, last_day_prev_month.month, 1).isoformat()
        end_date = last_day_prev_month.isoformat()
    elif period == "last_30_days":
        start_date = (today - manager.timedelta(days=30)).isoformat()
        end_date = today.isoformat()
    elif period == "this_year":
        start_date = f"{today.year}-01-01"
        end_date = today.isoformat()
    elif period == "all_time":
        start_date = "2000-01-01"
        end_date = today.isoformat()
    elif period == "custom":
        is_valid, err = validate_date_range(start_date or None, end_date or None)
        if not is_valid:
            flash(err, "warning")
            start_date = date(today.year, today.month, 1).isoformat()
            end_date = today.isoformat()

    # Generate analytical data
    summary = manager.get_financial_summary(start_date=start_date, end_date=end_date)
    category_breakdown = manager.get_category_spending_breakdown(start_date=start_date, end_date=end_date)
    daily_summary = manager.get_daily_expense_summary(start_date=start_date, end_date=end_date)
    weekly_summary = manager.get_weekly_expense_summary(start_date=start_date, end_date=end_date)
    monthly_trends = manager.get_monthly_spending_trends(months_count=12)

    # Average daily spend
    try:
        d1 = datetime.strptime(start_date, "%Y-%m-%d").date()
        d2 = datetime.strptime(end_date, "%Y-%m-%d").date()
        days_span = max(1, (d2 - d1).days + 1)
        avg_daily_expense = int(summary["total_expenses"] / days_span)
    except Exception:
        avg_daily_expense = 0

    return render_template(
        "reports.html",
        period=period,
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        category_breakdown=category_breakdown,
        daily_summary=daily_summary,
        weekly_summary=weekly_summary,
        monthly_trends=monthly_trends,
        avg_daily_expense=avg_daily_expense
    )


@app.route("/export/csv")
def export_csv():
    """
    Feature 7: CSV Export.
    Exports transactions matching filters to a CSV attachment.
    """
    search = request.args.get("search", "").strip()
    t_type = request.args.get("type", "All").strip()
    category = request.args.get("category", "All").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    filters = {
        "search": search if search else None,
        "transaction_type": t_type if t_type in ("Income", "Expense") else None,
        "category": category if category != "All" else None,
        "start_date": start_date if start_date else None,
        "end_date": end_date if end_date else None
    }

    csv_data = manager.generate_csv_string(filters=filters)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transactions_{timestamp}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """
    Feature 8: Settings Page.
    Allows configuring preferred currency, default monthly budget, theme preference,
    and reviewing expense/income categories and application diagnostic metadata.
    """
    if request.method == "POST":
        currency_code = request.form.get("currency_code", "INR").strip().upper()
        if currency_code in SUPPORTED_CURRENCIES:
            manager.update_setting("currency_code", currency_code)
            manager.update_setting("currency_symbol", SUPPORTED_CURRENCIES[currency_code]["symbol"])

        default_budget_input = request.form.get("default_monthly_budget")
        b_minor = parse_amount_to_minor_units(default_budget_input)
        if b_minor is not None:
            manager.update_setting("default_monthly_budget", str(b_minor))

        theme = request.form.get("theme_preference", "light").strip().lower()
        if theme in ("light", "dark"):
            manager.update_setting("theme_preference", theme)

        flash("Settings updated successfully!", "success")
        return redirect(url_for("settings"))

    all_settings = manager.get_all_settings()
    total_tx = manager.get_total_transaction_count()

    return render_template(
        "settings.html",
        settings=all_settings,
        total_records=total_tx
    )


# ==========================================
# REST API ENDPOINTS (FOR DYNAMIC REFRESHES)
# ==========================================

@app.route("/api/dashboard-charts")
def api_dashboard_charts():
    """Returns JSON formatted chart data for asynchronous dashboard updates."""
    today = date.today()
    summary = manager.get_financial_summary(year=today.year, month=today.month)
    breakdown = manager.get_category_spending_breakdown(
        start_date=summary["start_date"],
        end_date=summary["end_date"]
    )
    trends = manager.get_monthly_spending_trends(months_count=6)

    return jsonify({
        "summary": {
            "income": float(minor_units_to_decimal(summary["total_income"])),
            "expenses": float(minor_units_to_decimal(summary["total_expenses"])),
            "balance": float(minor_units_to_decimal(summary["net_cash_flow"])),
            "budget": float(minor_units_to_decimal(summary["monthly_budget"])),
            "remaining": float(minor_units_to_decimal(summary["remaining_budget"])),
            "utilization": summary["budget_utilization"]
        },
        "category_breakdown": {
            "labels": [b["category"] for b in breakdown],
            "amounts": [float(minor_units_to_decimal(b["total_amount"])) for b in breakdown]
        },
        "trends": trends
    })


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("404.html", error_message="Internal Server Error occurred. Please try again."), 500


if __name__ == "__main__":
    # Local development server
    port = int(os.environ.get("PORT", 5000))
    print(f"Personal Expense Tracker starting at http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)

