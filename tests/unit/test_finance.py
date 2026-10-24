"""Independent PRD finance oracles, runnable with standard-library unittest."""

import unittest

from backend.app.domain.finance import evaluate_cashflows


class FinanceOracleTests(unittest.TestCase):
    def test_prd_cashflow_oracle(self):
        result = evaluate_cashflows(1_000_000, [300_000] * 5, 0.10)
        self.assertAlmostEqual(result.npv_inr, 137_236.03, delta=1)
        self.assertAlmostEqual(result.horizon_roi, 0.5, places=8)
        self.assertAlmostEqual(result.payback_years, 3.3333, delta=0.01)

    def test_worked_sites_reverse_sales_order(self):
        higher_sales = evaluate_cashflows(8_000_000, [600_000] * 5, 0.12)
        lower_sales = evaluate_cashflows(6_000_000, [3_300_000] * 5, 0.12)
        self.assertAlmostEqual(higher_sales.npv_inr, -5_837_134, delta=1)
        self.assertAlmostEqual(lower_sales.npv_inr, 5_895_761.47, delta=1)
        self.assertGreater(lower_sales.npv_inr, higher_sales.npv_inr)

    def test_zero_capex_and_no_recovery(self):
        free = evaluate_cashflows(0, [100], 0.1)
        self.assertIsNone(free.horizon_roi)
        self.assertEqual(free.payback_years, 0)
        self.assertIsNone(evaluate_cashflows(100, [-10, 20], 0.1).payback_years)

    def test_invalid_values_rejected(self):
        for capex, flows, discount in [(-1, [1], 0.1), (1, [], 0.1), (1, [float("nan")], 0.1), (1, [1], -1)]:
            with self.assertRaises(ValueError):
                evaluate_cashflows(capex, flows, discount)


if __name__ == "__main__":
    unittest.main()
