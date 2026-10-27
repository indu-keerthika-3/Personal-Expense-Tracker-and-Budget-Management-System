"""
Unit and Integration Tests for Transaction Management and Financial Calculations.
Covers:
- Adding valid income and expense transactions
- Rejecting zero, negative, or invalid amounts
- Editing transactions
- Deleting transactions
- Filtering by date, category, search, and type
- Total income and expense calculation
- Empty database handling
- CSV export generation
- Validation edge cases
- Flask route interactions
"""

import os
import sys
import tempfile
import unittest
from datetime import date

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from database import init_db
import expense_manager as manager
from validators import (
    parse_amount_to_minor_units,
    validate_date_iso,
    validate_transaction_data
)


class TestTransactions(unittest.TestCase):
    def setUp(self):
        """Create a new temporary database for each test isolation."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_db(self.db_path)

        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_add_valid_income_transaction(self):
        """Test Scenario 1: Adding a valid income transaction."""
        tx_data = {
            "transaction_date": "2026-10-15",
            "transaction_type": "Income",
            "category": "Salary",
            "amount": 7500000,  # ₹75,000.00 in minor units
            "payment_method": "Bank Transfer",
            "description": "Monthly Salary from employer"
        }
        tx_id = manager.add_transaction(tx_data, db_path=self.db_path)
        self.assertIsInstance(tx_id, int)
        self.assertGreater(tx_id, 0)

        record = manager.get_transaction_by_id(tx_id, db_path=self.db_path)
        self.assertIsNotNone(record)
        self.assertEqual(record["transaction_type"], "Income")
        self.assertEqual(record["category"], "Salary")
        self.assertEqual(record["amount"], 7500000)
        self.assertEqual(record["payment_method"], "Bank Transfer")

    def test_add_valid_expense_transaction(self):
        """Test Scenario 2: Adding a valid expense transaction."""
        tx_data = {
            "transaction_date": "2026-10-16",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 145050,  # ₹1,450.50 in minor units
            "payment_method": "UPI",
            "description": "Supermarket groceries"
        }
        tx_id = manager.add_transaction(tx_data, db_path=self.db_path)
        record = manager.get_transaction_by_id(tx_id, db_path=self.db_path)
        self.assertIsNotNone(record)
        self.assertEqual(record["transaction_type"], "Expense")
        self.assertEqual(record["category"], "Food")
        self.assertEqual(record["amount"], 145050)

    def test_reject_zero_or_negative_amounts(self):
        """Test Scenario 3: Rejecting zero or negative transaction amounts."""
        # Zero amount
        self.assertIsNone(parse_amount_to_minor_units("0"))
        self.assertIsNone(parse_amount_to_minor_units(0))
        self.assertIsNone(parse_amount_to_minor_units("0.00"))

        # Negative amount
        self.assertIsNone(parse_amount_to_minor_units("-500"))
        self.assertIsNone(parse_amount_to_minor_units("-12.50"))

        # Non-numeric string
        self.assertIsNone(parse_amount_to_minor_units("invalid_amt"))

        # Validation function rejection
        invalid_form = {
            "transaction_date": "2026-10-15",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": "-100",
            "payment_method": "Cash",
            "description": "Test"
        }
        is_valid, err, _ = validate_transaction_data(invalid_form)
        self.assertFalse(is_valid)
        self.assertIn("positive", err.lower())

    def test_edit_existing_transaction(self):
        """Test Scenario 4: Editing an existing transaction."""
        tx_data = {
            "transaction_date": "2026-10-10",
            "transaction_type": "Expense",
            "category": "Shopping",
            "amount": 250000,
            "payment_method": "Credit Card",
            "description": "Original Purchase"
        }
        tx_id = manager.add_transaction(tx_data, db_path=self.db_path)

        updated_data = {
            "transaction_date": "2026-10-12",
            "transaction_type": "Expense",
            "category": "Shopping",
            "amount": 320000,  # changed amount to 3200.00
            "payment_method": "Debit Card",
            "description": "Updated Purchase Description"
        }
        success = manager.update_transaction(tx_id, updated_data, db_path=self.db_path)
        self.assertTrue(success)

        fetched = manager.get_transaction_by_id(tx_id, db_path=self.db_path)
        self.assertEqual(fetched["transaction_date"], "2026-10-12")
        self.assertEqual(fetched["amount"], 320000)
        self.assertEqual(fetched["payment_method"], "Debit Card")
        self.assertEqual(fetched["description"], "Updated Purchase Description")

    def test_delete_transaction(self):
        """Test Scenario 5: Deleting a transaction."""
        tx_data = {
            "transaction_date": "2026-10-11",
            "transaction_type": "Expense",
            "category": "Utilities",
            "amount": 95000,
            "payment_method": "Net Banking",
            "description": "Electricity Bill"
        }
        tx_id = manager.add_transaction(tx_data, db_path=self.db_path)
        self.assertIsNotNone(manager.get_transaction_by_id(tx_id, db_path=self.db_path))

        deleted = manager.delete_transaction(tx_id, db_path=self.db_path)
        self.assertTrue(deleted)

        self.assertIsNone(manager.get_transaction_by_id(tx_id, db_path=self.db_path))

    def test_filter_transactions_by_date_and_category(self):
        """Test Scenario 6: Filtering transactions by date and category."""
        # Insert 3 test records
        manager.add_transaction({
            "transaction_date": "2026-10-01",
            "transaction_type": "Income",
            "category": "Salary",
            "amount": 5000000,
            "payment_method": "Bank Transfer",
            "description": "Salary"
        }, db_path=self.db_path)

        manager.add_transaction({
            "transaction_date": "2026-10-05",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 50000,
            "payment_method": "Cash",
            "description": "Lunch"
        }, db_path=self.db_path)

        manager.add_transaction({
            "transaction_date": "2026-10-20",
            "transaction_type": "Expense",
            "category": "Transportation",
            "amount": 30000,
            "payment_method": "UPI",
            "description": "Fuel"
        }, db_path=self.db_path)

        # Filter by Category = Food
        food_results = manager.get_transactions({"category": "Food"}, db_path=self.db_path)
        self.assertEqual(len(food_results), 1)
        self.assertEqual(food_results[0]["category"], "Food")

        # Filter by Date range
        range_results = manager.get_transactions({
            "start_date": "2026-10-04",
            "end_date": "2026-10-15"
        }, db_path=self.db_path)
        self.assertEqual(len(range_results), 1)
        self.assertEqual(range_results[0]["description"], "Lunch")

        # Search by description keyword
        search_results = manager.get_transactions({"search": "Fuel"}, db_path=self.db_path)
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0]["category"], "Transportation")

    def test_calculate_total_income_and_expense_correctly(self):
        """Test Scenarios 7 & 8: Calculating total income and total expenses."""
        manager.add_transaction({
            "transaction_date": "2026-10-01",
            "transaction_type": "Income",
            "category": "Salary",
            "amount": 6000000,  # 60,000.00
            "payment_method": "Bank Transfer",
            "description": "Salary"
        }, db_path=self.db_path)

        manager.add_transaction({
            "transaction_date": "2026-10-02",
            "transaction_type": "Income",
            "category": "Freelancing",
            "amount": 1500000,  # 15,000.00
            "payment_method": "UPI",
            "description": "Website Design"
        }, db_path=self.db_path)

        manager.add_transaction({
            "transaction_date": "2026-10-05",
            "transaction_type": "Expense",
            "category": "Rent",
            "amount": 2000000,  # 20,000.00
            "payment_method": "Net Banking",
            "description": "Apartment Rent"
        }, db_path=self.db_path)

        manager.add_transaction({
            "transaction_date": "2026-10-10",
            "transaction_type": "Expense",
            "category": "Utilities",
            "amount": 500000,  # 5,000.00
            "payment_method": "UPI",
            "description": "Bills"
        }, db_path=self.db_path)

        summary = manager.get_financial_summary(
            start_date="2026-10-01",
            end_date="2026-10-31",
            year=2026,
            month=10,
            db_path=self.db_path
        )

        # Expected: Income = 75,000.00 (7500000 minor units)
        self.assertEqual(summary["total_income"], 7500000)
        # Expected: Expenses = 25,000.00 (2500000 minor units)
        self.assertEqual(summary["total_expenses"], 2500000)
        # Net Cash Flow = 75,000 - 25,000 = 50,000.00 (5000000 minor units)
        self.assertEqual(summary["net_cash_flow"], 5000000)
        # Savings Rate = (50000 / 75000) * 100 = 66.67%
        self.assertAlmostEqual(summary["savings_rate"], 66.67, places=1)

    def test_handling_empty_database(self):
        """Test Scenario 11: Handling an empty database."""
        summary = manager.get_financial_summary(
            start_date="2026-10-01",
            end_date="2026-10-31",
            year=2026,
            month=10,
            db_path=self.db_path
        )
        self.assertEqual(summary["total_income"], 0)
        self.assertEqual(summary["total_expenses"], 0)
        self.assertEqual(summary["net_cash_flow"], 0)
        self.assertEqual(summary["savings_rate"], 0.0)
        self.assertEqual(summary["total_transactions"], 0)

        txs = manager.get_transactions(db_path=self.db_path)
        self.assertEqual(txs, [])

    def test_export_transaction_records_to_csv(self):
        """Test Scenario 10: Exporting transaction records to CSV."""
        manager.add_transaction({
            "transaction_date": "2026-10-05",
            "transaction_type": "Expense",
            "category": "Food",
            "amount": 45000,
            "payment_method": "Cash",
            "description": "Lunch meeting"
        }, db_path=self.db_path)

        csv_text = manager.generate_csv_string(db_path=self.db_path)
        self.assertIn("Transaction ID,Date,Type,Category,Amount (INR),Payment Method,Description,Created At", csv_text)
        self.assertIn("Food", csv_text)
        self.assertIn("450.00", csv_text)
        self.assertIn("Lunch meeting", csv_text)

    def test_invalid_form_submissions(self):
        """Test Scenario 12: Handling invalid form submissions."""
        # Missing date
        valid, err, _ = validate_transaction_data({
            "transaction_date": "",
            "transaction_type": "Income",
            "category": "Salary",
            "amount": "1000",
            "payment_method": "Cash"
        })
        self.assertFalse(valid)
        self.assertIn("valid date", err.lower())

        # Invalid category for type
        valid, err, _ = validate_transaction_data({
            "transaction_date": "2026-10-10",
            "transaction_type": "Income",
            "category": "Food",  # Food is an expense category, not income
            "amount": "1000",
            "payment_method": "Cash"
        })
        self.assertFalse(valid)
        self.assertIn("invalid category", err.lower())

    def test_flask_routes_and_http_responses(self):
        """Test Flask HTTP routes for dashboard, transactions, export, and settings."""
        with self.client:
            # 1. Dashboard Route
            resp = self.client.get("/")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Financial Dashboard", resp.data)

            # 2. Add Transaction Route (GET)
            resp = self.client.get("/transactions/add")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"New Income or Expense", resp.data)

            # 3. Add Transaction Route (POST)
            # Fetch CSRF token from session
            with self.client.session_transaction() as sess:
                token = sess.get("csrf_token")
            if not token:
                # Issue GET to initialize session
                self.client.get("/")
                with self.client.session_transaction() as sess:
                    token = sess.get("csrf_token")

            post_data = {
                "csrf_token": token,
                "transaction_date": "2026-10-18",
                "transaction_type": "Income",
                "category": "Salary",
                "amount": "50000.00",
                "payment_method": "Bank Transfer",
                "description": "Salary Payday"
            }
            resp_post = self.client.post("/transactions/add", data=post_data, follow_redirects=True)
            self.assertEqual(resp_post.status_code, 200)
            self.assertIn(b"recorded successfully", resp_post.data)

            # 4. View Transactions History Route
            resp_list = self.client.get("/transactions")
            self.assertEqual(resp_list.status_code, 200)
            self.assertIn(b"Salary Payday", resp_list.data)

            # 5. CSV Export Route
            resp_csv = self.client.get("/export/csv")
            self.assertEqual(resp_csv.status_code, 200)
            self.assertEqual(resp_csv.mimetype, "text/csv")
            self.assertIn("attachment", resp_csv.headers.get("Content-Disposition", ""))

            # 6. Reports Route
            resp_rep = self.client.get("/reports?period=this_month")
            self.assertEqual(resp_rep.status_code, 200)
            self.assertIn(b"Reports & Analytics", resp_rep.data)

            # 7. Budgets Route
            resp_bud = self.client.get("/budgets")
            self.assertEqual(resp_bud.status_code, 200)
            self.assertIn(b"Budget Management", resp_bud.data)

            # 8. Settings Route
            resp_set = self.client.get("/settings")
            self.assertEqual(resp_set.status_code, 200)
            self.assertIn(b"Application Settings", resp_set.data)

            # 9. 404 Route
            resp_404 = self.client.get("/non-existent-page-xyz")
            self.assertEqual(resp_404.status_code, 404)
            self.assertIn(b"Page or Resource Not Found", resp_404.data)



if __name__ == "__main__":
    unittest.main()
