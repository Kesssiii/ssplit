import unittest

from app import create_app
from app.data import create_bill, login_user, register_user
from app.database import get_db


class ExpenseOverviewTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        with self.app.app_context():
            db = get_db()
            db.execute("DELETE FROM sessions")
            db.execute("DELETE FROM bills")
            db.execute("DELETE FROM users")
            db.execute("DELETE FROM sqlite_sequence WHERE name = 'sessions'")
            db.execute("DELETE FROM sqlite_sequence WHERE name = 'bills'")
            db.execute("DELETE FROM sqlite_sequence WHERE name = 'users'")
            db.commit()

    def test_expense_overview_returns_balances_and_breakdowns(self):
        with self.app.app_context():
            alice = register_user("Alice", "alice@example.com", "Password123")
            bob = register_user("Bob", "bob@example.com", "Password123")
            carol = register_user("Carol", "carol@example.com", "Password123")

            session = login_user("alice@example.com", "Password123")
            token = session["token"]

            create_bill(alice["id"], "Rent", 120.00, alice["id"], "1,2,3", "2026-10-01")
            create_bill(bob["id"], "Groceries", 90.00, bob["id"], "1,2", "2026-10-02")
            create_bill(carol["id"], "Utilities", 60.00, carol["id"], "1,2,3", "2026-10-03")

        response = self.client.get(
            "/api/expenses/overview",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["summary"]["total_paid_by_me"], 120.0)
        self.assertEqual(payload["summary"]["total_i_owe"], 65.0)
        self.assertEqual(payload["summary"]["total_owed_to_me"], 80.0)
        self.assertEqual(payload["summary"]["net_balance"], 15.0)

        self.assertEqual(payload["my_expenses"]["total"], 120.0)
        self.assertEqual(payload["my_debts"]["total"], 65.0)
        self.assertEqual(payload["debts_to_me"]["total"], 80.0)

        self.assertIn("bills", payload["my_expenses"])
        self.assertIn("by_person", payload["my_debts"])
        self.assertIn("by_person", payload["debts_to_me"])


if __name__ == "__main__":
    unittest.main()
