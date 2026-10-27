"""
Unit and Integration Tests for Budget Management and Utilization Calculations.
Covers:
- Setting and retrieving monthly budgets
- Calculating remaining budget and utilization percentages
- Budget status transitions (normal <80%, warning >=80%, exceeded >100%)
- Updating budget utilization dynamically after transaction add, edit, and delete
- Category-level budgets and tracking
- Safe handling of zero or missing budgets (zero division prevention)
- Savings rate calculations
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import init_db
import expense_manager as manager
from validators import validate_budget_data, validate_category_budget_data


class TestBudgets(unittest.TestCase):
    def setUp(self):
        """Create a new temporary database for isolated testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_db(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_set_and_get_monthly_budget(self):
        """Test setting and retrieving monthly budget limits."""
        year, month = 2026, 10
        # Set budget to 40,000.00 (4,000,000 minor units)
        success = manager.set_monthly_budget(year, month, 4000000, db_path=self.db_path)
        self.assertTrue(success)

        retrieved = manager.get_monthly_budget(year, month, db_path=self.db_path)
        self.assertEqual(retrieved, 4000000)

        # Update budget to 45,000.00
        manager.set_monthly_budget(year, month, 4500000, db_path=self.db_path)
        self.assertEqual(manager.get_monthly_budget(year, month, db_path=self.db_path), 4500000)

    def test_budget_utilization_and_warning_thresholds(self):
        """Test budget utilization: normal (<80%), warning (>=80%), exceeded (>100%)."""
        year, month = 2026, 10
        # Set monthly budget = 10,000.00 (1,000,000 minor units)
        manager.set_monthly_budget(year, month, 1000000, db_path=self.db_path)

        # 1. 50% utilization (5,000.00 spent) -> Normal
        tx1 = manager.add_transaction({
            "transaction_date": "2026-10-05",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 500000,
            "payment_method": "UPI",
            "description": "Groceries"
        }, db_path=self.db_path)

        summary1 = manager.get_financial_summary(year=year, month=month, db_path=self.db_path)
        self.assertEqual(summary1["monthly_budget"], 1000000)
        self.assertEqual(summary1["eligible_expenses"], 500000)
        self.assertEqual(summary1["remaining_budget"], 500000)
        self.assertEqual(summary1["budget_utilization"], 50.0)
        self.assertEqual(summary1["budget_status"], "normal")

        # 2. Add 3,200.00 spent -> Total 8,200.00 (82% utilization) -> Warning
        tx2 = manager.add_transaction({
            "transaction_date": "2026-10-12",
            "transaction_type": "Expense",
            "category": "Shopping",
            "amount": 320000,
            "payment_method": "Credit Card",
            "description": "Clothes"
        }, db_path=self.db_path)

        summary2 = manager.get_financial_summary(year=year, month=month, db_path=self.db_path)
        self.assertEqual(summary2["eligible_expenses"], 820000)
        self.assertEqual(summary2["remaining_budget"], 180000)
        self.assertEqual(summary2["budget_utilization"], 82.0)
        self.assertEqual(summary2["budget_status"], "warning")

        # 3. Add 2,500.00 spent -> Total 10,700.00 (107% utilization) -> Exceeded
        tx3 = manager.add_transaction({
            "transaction_date": "2026-10-20",
            "transaction_type": "Expense",
            "category": "Entertainment",
            "amount": 250000,
            "payment_method": "Debit Card",
            "description": "Concert tickets"
        }, db_path=self.db_path)

        summary3 = manager.get_financial_summary(year=year, month=month, db_path=self.db_path)
        self.assertEqual(summary3["eligible_expenses"], 1070000)
        self.assertEqual(summary3["remaining_budget"], -70000)
        self.assertEqual(summary3["budget_utilization"], 107.0)
        self.assertEqual(summary3["budget_status"], "exceeded")

    def test_updating_budget_utilization_after_transaction_changes(self):
        """Test Scenario 9: Updating budget utilization after transaction edit and delete."""
        year, month = 2026, 10
        manager.set_monthly_budget(year, month, 1000000, db_path=self.db_path)  # ₹10,000

        # Add initial expense of ₹6,000
        tx_id = manager.add_transaction({
            "transaction_date": "2026-10-08",
            "transaction_type": "Expense",
            "category": "Shopping",
            "amount": 600000,
            "payment_method": "Credit Card",
            "description": "Shopping"
        }, db_path=self.db_path)

        s1 = manager.get_financial_summary(year=year, month=month, db_path=self.db_path)
        self.assertEqual(s1["budget_utilization"], 60.0)

        # Edit expense to ₹9,000 (should move to 90% and warning status)
        manager.update_transaction(tx_id, {
            "transaction_date": "2026-10-08",
            "transaction_type": "Expense",
            "category": "Shopping",
            "amount": 900000,
            "payment_method": "Credit Card",
            "description": "Shopping updated"
        }, db_path=self.db_path)

        s2 = manager.get_financial_summary(year=year, month=month, db_path=self.db_path)
        self.assertEqual(s2["budget_utilization"], 90.0)
        self.assertEqual(s2["budget_status"], "warning")

        # Delete transaction (utilization should drop back to 0.0%)
        manager.delete_transaction(tx_id, db_path=self.db_path)
        s3 = manager.get_financial_summary(year=year, month=month, db_path=self.db_path)
        self.assertEqual(s3["budget_utilization"], 0.0)
        self.assertEqual(s3["remaining_budget"], 1000000)
        self.assertEqual(s3["budget_status"], "normal")

    def test_category_level_budgets(self):
        """Test setting and tracking individual category budgets."""
        year, month = 2026, 10
        # Set Food category budget to ₹5,000 (500,000 minor units)
        manager.set_category_budget(year, month, "Food", 500000, db_path=self.db_path)

        # Spend ₹4,500 on Food (90% utilization -> warning)
        manager.add_transaction({
            "transaction_date": "2026-10-10",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 450000,
            "payment_method": "UPI",
            "description": "Monthly groceries"
        }, db_path=self.db_path)

        # Spend ₹1,000 on Transportation (unbudgeted)
        manager.add_transaction({
            "transaction_date": "2026-10-11",
            "transaction_type": "Expense",
            "category": "Transportation",
            "amount": 100000,
            "payment_method": "Cash",
            "description": "Metro card"
        }, db_path=self.db_path)

        cat_budgets = manager.get_category_budgets_with_spending(year, month, db_path=self.db_path)
        food_budget = next(cb for cb in cat_budgets if cb["category"] == "Food")
        self.assertEqual(food_budget["budget_limit"], 500000)
        self.assertEqual(food_budget["actual_spending"], 450000)
        self.assertEqual(food_budget["remaining"], 50000)
        self.assertEqual(food_budget["utilization_pct"], 90.0)
        self.assertEqual(food_budget["status"], "warning")

        # Delete category budget
        del_res = manager.delete_category_budget(year, month, "Food", db_path=self.db_path)
        self.assertTrue(del_res)

        cat_budgets_after = manager.get_category_budgets_with_spending(year, month, db_path=self.db_path)
        food_budget_after = next(cb for cb in cat_budgets_after if cb["category"] == "Food")
        self.assertEqual(food_budget_after["budget_limit"], 0)

    def test_zero_budget_limit_division_safety(self):
        """Test that a 0 budget does not cause division by zero errors."""
        year, month = 2026, 10
        manager.set_monthly_budget(year, month, 0, db_path=self.db_path)

        manager.add_transaction({
            "transaction_date": "2026-10-05",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 20000,
            "payment_method": "Cash",
            "description": "Snacks"
        }, db_path=self.db_path)

        summary = manager.get_financial_summary(year=year, month=month, db_path=self.db_path)
        self.assertEqual(summary["monthly_budget"], 0)
        self.assertEqual(summary["budget_utilization"], 0.0)
        self.assertEqual(summary["remaining_budget"], -20000)

    def test_savings_rate_calculations(self):
        """Test savings rate calculations with positive, zero, and negative cash flows."""
        # 1. Income > Expenses
        manager.add_transaction({
            "transaction_date": "2026-10-01",
            "transaction_type": "Income",
            "category": "Salary",
            "amount": 1000000,  # ₹10,000
            "payment_method": "Bank Transfer",
            "description": "Salary"
        }, db_path=self.db_path)

        manager.add_transaction({
            "transaction_date": "2026-10-02",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 250000,  # ₹2,500
            "payment_method": "UPI",
            "description": "Groceries"
        }, db_path=self.db_path)

        s1 = manager.get_financial_summary(year=2026, month=10, db_path=self.db_path)
        # Net Cash Flow = 10,000 - 2,500 = 7,500
        # Savings Rate = (7,500 / 10,000) * 100 = 75.0%
        self.assertEqual(s1["savings_rate"], 75.0)

        # 2. Expenses exceed Income (Net cash flow is negative -> savings rate 0.0%)
        manager.add_transaction({
            "transaction_date": "2026-10-03",
            "transaction_type": "Expense",
            "category": "Rent",
            "amount": 1000000,  # another ₹10,000 expense
            "payment_method": "Bank Transfer",
            "description": "Rent"
        }, db_path=self.db_path)

        s2 = manager.get_financial_summary(year=2026, month=10, db_path=self.db_path)
        self.assertLess(s2["net_cash_flow"], 0)
        self.assertEqual(s2["savings_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()

