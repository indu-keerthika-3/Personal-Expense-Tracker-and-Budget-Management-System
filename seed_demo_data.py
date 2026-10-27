"""
Demo Data Seeder for Personal Expense Tracker.
Seeds realistic initial transactions and monthly budgets for instant exploration.
Run with: python seed_demo_data.py
"""

from datetime import date
from database import init_db
import expense_manager as manager

def seed():
    init_db()
    today = date.today()
    year = today.year
    month = today.month

    # Set overall monthly budget to ₹50,000 (5,000,000 minor units)
    manager.set_monthly_budget(year, month, 5000000)

    # Set category budgets
    manager.set_category_budget(year, month, "Food", 1200000)          # ₹12,000
    manager.set_category_budget(year, month, "Rent", 1800000)          # ₹18,000
    manager.set_category_budget(year, month, "Utilities", 500000)      # ₹5,000
    manager.set_category_budget(year, month, "Transportation", 400000) # ₹4,000
    manager.set_category_budget(year, month, "Shopping", 600000)       # ₹6,000
    manager.set_category_budget(year, month, "Entertainment", 300000)  # ₹3,000

    # Sample Transactions
    samples = [
        # Incomes
        {
            "transaction_date": f"{year:04d}-{month:02d}-01",
            "transaction_type": "Income",
            "category": "Salary",
            "amount": 7500000,  # ₹75,000.00
            "payment_method": "Bank Transfer",
            "description": "Primary Monthly Corporate Salary"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-08",
            "transaction_type": "Income",
            "category": "Freelancing",
            "amount": 1850000,  # ₹18,500.00
            "payment_method": "UPI",
            "description": "Full-stack UI Consulting Project"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-15",
            "transaction_type": "Income",
            "category": "Investment Income",
            "amount": 420000,   # ₹4,200.00
            "payment_method": "Bank Transfer",
            "description": "Mutual Fund & Stock Dividend"
        },
        # Expenses
        {
            "transaction_date": f"{year:04d}-{month:02d}-02",
            "transaction_type": "Expense",
            "category": "Rent",
            "amount": 1800000,  # ₹18,000.00
            "payment_method": "Net Banking",
            "description": "Apartment Monthly Rent"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-03",
            "transaction_type": "Expense",
            "category": "Utilities",
            "amount": 265000,   # ₹2,650.00
            "payment_method": "UPI",
            "description": "High-Speed Fiber Internet & Electricity"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-05",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 345000,   # ₹3,450.00
            "payment_method": "UPI",
            "description": "Weekly Supermarket Grocery Restock"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-09",
            "transaction_type": "Expense",
            "category": "Transportation",
            "amount": 180000,   # ₹1,800.00
            "payment_method": "Debit Card",
            "description": "Vehicle Fuel & Metro Recharge"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-12",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 128000,   # ₹1,280.00
            "payment_method": "UPI",
            "description": "Weekend Dining with Family"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-16",
            "transaction_type": "Expense",
            "category": "Shopping",
            "amount": 420000,   # ₹4,200.00
            "payment_method": "Credit Card",
            "description": "Work Desk Accessories & Books"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-20",
            "transaction_type": "Expense",
            "category": "Healthcare",
            "amount": 85000,    # ₹850.00
            "payment_method": "Cash",
            "description": "Pharmacy Prescription & Vitamins"
        },
        {
            "transaction_date": f"{year:04d}-{month:02d}-22",
            "transaction_type": "Expense",
            "category": "Entertainment",
            "amount": 99900,    # ₹999.00
            "payment_method": "Credit Card",
            "description": "Streaming Service Subscription Renewals"
        }
    ]

    for item in samples:
        manager.add_transaction(item)

    print(f"Successfully seeded {len(samples)} demo transactions and budgets for {today.strftime('%B %Y')}!")

if __name__ == "__main__":
    seed()

