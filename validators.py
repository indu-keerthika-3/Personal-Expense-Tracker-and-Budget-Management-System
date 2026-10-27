"""
Validation and data parsing module for Personal Expense Tracker.
Ensures rigorous server-side checks for transactions, budgets, dates, and amounts.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple

EXPENSE_CATEGORIES = [
    "Food",
    "Transportation",
    "Shopping",
    "Education",
    "Rent",
    "Utilities",
    "Healthcare",
    "Entertainment",
    "Travel",
    "Personal Care",
    "Other"
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelancing",
    "Business",
    "Scholarship",
    "Investment Income",
    "Other"
]

PAYMENT_METHODS = [
    "Cash",
    "Debit Card",
    "Credit Card",
    "UPI",
    "Net Banking",
    "Bank Transfer",
    "Other"
]

SUPPORTED_CURRENCIES = {
    "INR": {"symbol": "₹", "name": "Indian Rupee"},
    "USD": {"symbol": "$", "name": "US Dollar"},
    "EUR": {"symbol": "€", "name": "Euro"},
    "GBP": {"symbol": "£", "name": "British Pound"},
    "JPY": {"symbol": "¥", "name": "Japanese Yen"},
    "CAD": {"symbol": "CA$", "name": "Canadian Dollar"},
    "AUD": {"symbol": "AU$", "name": "Australian Dollar"}
}


def parse_amount_to_minor_units(amount_val: Any) -> Optional[int]:
    """
    Safely converts amount (string, float, int, Decimal) to integer minor units (paise/cents).
    Returns None if invalid or non-positive.
    """
    if amount_val is None:
        return None
    try:
        # Convert to string and strip spaces
        clean_str = str(amount_val).strip().replace(",", "")
        if not clean_str:
            return None
        dec = Decimal(clean_str)
        # Must be strictly positive
        if dec <= Decimal("0"):
            return None
        # Round to 2 decimal places to prevent sub-cent anomalies
        quantized = dec.quantize(Decimal("0.01"))
        minor_units = int(quantized * 100)
        return minor_units if minor_units > 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_non_negative_amount_to_minor_units(amount_val: Any) -> Optional[int]:
    """
    Converts amount to integer minor units allowing 0 (e.g. for zero budget limit).
    """
    if amount_val is None:
        return None
    try:
        clean_str = str(amount_val).strip().replace(",", "")
        if not clean_str:
            return None
        dec = Decimal(clean_str)
        if dec < Decimal("0"):
            return None
        quantized = dec.quantize(Decimal("0.01"))
        minor_units = int(quantized * 100)
        return minor_units if minor_units >= 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def minor_units_to_decimal(minor_units: int) -> Decimal:
    """Converts minor units (paise) back to Decimal standard units."""
    if minor_units is None:
        return Decimal("0.00")
    return (Decimal(minor_units) / Decimal("100")).quantize(Decimal("0.01"))


def format_currency_amount(minor_units: int, symbol: str = "₹") -> str:
    """Formats minor units as formatted currency string: ₹1,234.56 or -₹50.00."""
    if minor_units is None:
        minor_units = 0
    is_neg = minor_units < 0
    abs_val = abs(minor_units)
    dec = (Decimal(abs_val) / Decimal("100")).quantize(Decimal("0.01"))
    parts = f"{dec:,.2f}"
    if is_neg:
        return f"-{symbol}{parts}"
    return f"{symbol}{parts}"


def validate_date_iso(date_str: str) -> Optional[str]:
    """Validates date string in YYYY-MM-DD format. Returns sanitized date string or None."""
    if not date_str or not isinstance(date_str, str):
        return None
    clean = date_str.strip()
    try:
        dt = datetime.strptime(clean, "%Y-%m-%d")
        # Ensure year is reasonable
        if 1900 <= dt.year <= 2100:
            return clean
        return None
    except ValueError:
        return None


def validate_transaction_data(form_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates submitted transaction data.
    Returns:
        (is_valid: bool, error_message: Optional[str], clean_data: Optional[dict])
    """
    raw_date = form_data.get("transaction_date", "")
    valid_date = validate_date_iso(raw_date)
    if not valid_date:
        return False, "Please enter a valid date in YYYY-MM-DD format.", None

    trans_type = str(form_data.get("transaction_type", "")).strip().capitalize()
    if trans_type not in ("Income", "Expense"):
        return False, "Transaction type must be either 'Income' or 'Expense'.", None

    category = str(form_data.get("category", "")).strip()
    if not category:
        return False, "Please select or enter a category.", None

    valid_cats = INCOME_CATEGORIES if trans_type == "Income" else EXPENSE_CATEGORIES
    if category not in valid_cats:
        return False, f"Invalid category '{category}' for {trans_type}. Please choose from allowed categories.", None

    raw_amount = form_data.get("amount")
    amount_minor = parse_amount_to_minor_units(raw_amount)
    if amount_minor is None:
        return False, "Amount must be a positive number greater than 0.", None

    payment_method = str(form_data.get("payment_method", "")).strip()
    if not payment_method:
        return False, "Please select a payment method.", None
    if payment_method not in PAYMENT_METHODS:
        return False, f"Invalid payment method '{payment_method}'.", None

    description = str(form_data.get("description", "")).strip()
    if len(description) > 500:
        return False, "Description cannot exceed 500 characters.", None

    clean_data = {
        "transaction_date": valid_date,
        "transaction_type": trans_type,
        "category": category,
        "amount": amount_minor,
        "payment_method": payment_method,
        "description": description
    }
    return True, None, clean_data


def validate_budget_data(form_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates monthly budget inputs."""
    try:
        year = int(form_data.get("year", 0))
        month = int(form_data.get("month", 0))
    except (ValueError, TypeError):
        return False, "Year and Month must be valid integers.", None

    if not (2000 <= year <= 2100):
        return False, "Year must be between 2000 and 2100.", None
    if not (1 <= month <= 12):
        return False, "Month must be between 1 and 12.", None

    raw_limit = form_data.get("monthly_limit")
    limit_minor = parse_non_negative_amount_to_minor_units(raw_limit)
    if limit_minor is None:
        return False, "Budget limit must be a non-negative number.", None

    return True, None, {
        "year": year,
        "month": month,
        "monthly_limit": limit_minor
    }


def validate_category_budget_data(form_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates category-level budget input."""
    valid_res, err, base_data = validate_budget_data(form_data)
    if not valid_res:
        return False, err, None

    category = str(form_data.get("category", "")).strip()
    if category not in EXPENSE_CATEGORIES:
        return False, f"Category must be one of the predefined expense categories.", None

    raw_limit = form_data.get("budget_limit", form_data.get("monthly_limit"))
    limit_minor = parse_non_negative_amount_to_minor_units(raw_limit)
    if limit_minor is None:
        return False, "Category budget limit must be a non-negative number.", None

    return True, None, {
        "year": base_data["year"],
        "month": base_data["month"],
        "category": category,
        "budget_limit": limit_minor
    }


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Checks that start_date and end_date are valid ISO dates and start_date <= end_date."""
    if start_date:
        if not validate_date_iso(start_date):
            return False, "Invalid Start Date format. Use YYYY-MM-DD."
    if end_date:
        if not validate_date_iso(end_date):
            return False, "Invalid End Date format. Use YYYY-MM-DD."
    if start_date and end_date:
        if start_date > end_date:
            return False, "Start Date cannot be later than End Date."
    return True, None

