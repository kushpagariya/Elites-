"""Canonical rescue application regressions and read-only Bengaluru timing.

Tests: python -m unittest tests.unit.test_rescue_handoff -v
Timing: python -m tests.unit.test_rescue_handoff --benchmark
Benchmark output is isolated in .runtime/ml-final-handoff/, never frozen data.
"""
from copy import deepcopy
import json
from pathlib import Path
from statistics import median
from time import perf_counter
import unittest

from backend.app.domain.pipeline import prepare_evaluation, calculate_rescue, run_portfolio
from backend.app.domain.failfast.rules import sales_rescue, UnattainableRescue
from backend.app.domain.validation import digest
from tests.unit.test_decision_engine import fixture


def rescue_fixture():
    """Explicit assumed test targets, not an assertion of fitted inference."""
    project, scenario = fixture()
    project['sites'] = project['sites'][:1]
    project['stores'] = []
    project['inputs']['reference_predictions'] = {'s0': project['inputs']['reference_predictions']['s0']}
    project['sites'][0].update(capex_inr=1000., monthly_rent_inr=50., annual_opex_inr=100.)
    scenario['budget_inr'] = 1e9
    return project, scenario


def apply(project, scenario, answer):
    changed = deepcopy(scenario)
    changed['scenario_id'] = 'test-fresh-rescued-scenario'
    changed['assumptions'].setdefault('site_overrides', {}).setdefault('s0', {}).update(answer['actionable_site_override'])
    return prepare_evaluation(project, changed)


class RentApplicationTests(unittest.TestCase):
    def verify_multiplier(self, multiplier):
        p, s = rescue_fixture(); p['sites'][0]['monthly_rent_inr'] = 100.
        s['assumptions']['rent_multiplier'] = multiplier
        prepared = prepare_evaluation(p, s); original = digest([p, s, prepared])
        answer = calculate_rescue(p, prepared['context'], 's0', 'rent')
        self.assertEqual(answer['status'], 'SOLVED')
        self.assertEqual(answer['threshold'], answer['actionable_site_override']['monthly_rent_inr'])
        self.assertAlmostEqual(answer['max_viable_base_monthly_rent_inr'] * multiplier,
                               answer['max_viable_effective_monthly_rent_inr'], places=8)
        # Independent annuity calculation on this branch-free synthetic fixture.
        annuity = sum(1.1**(-y) for y in range(1, 6))
        independent = ((3000 * .3 - 100) - 1000 / annuity) / (12 * multiplier)
        self.assertAlmostEqual(answer['threshold'], independent, delta=.001)
        fresh = apply(p, s, answer)
        value = fresh['evaluation']['site_analyses'][0]['npv_inr']
        self.assertGreaterEqual(value, 0.); self.assertLessEqual(value, 1.)
        self.assertAlmostEqual(value, answer['applied_verification']['npv_inr'], places=8)
        for delta, sign in [(-.01, 1), (.01, -1)]:
            other = deepcopy(answer)
            other['actionable_site_override']['monthly_rent_inr'] += delta
            npv = apply(p, s, other)['evaluation']['site_analyses'][0]['npv_inr']
            self.assertGreater(sign * npv, 0.)
        self.assertEqual(original, digest([p, s, prepared]))

    def test_multiplier_one_applied_root_and_both_sides(self):
        self.verify_multiplier(1.)

    def test_multiplier_one_point_two_applied_root_and_both_sides(self):
        self.verify_multiplier(1.2)

    def test_zero_global_multiplier_has_no_finite_inverse(self):
        p, s = rescue_fixture(); s['assumptions']['rent_multiplier'] = 0.
        a = calculate_rescue(p, prepare_evaluation(p, s)['context'], 's0', 'rent')
        self.assertEqual(a['status'], 'NOT_RECOVERABLE_WITHIN_BOUNDS')
        self.assertEqual(a['application_status'], 'BLOCKED_ZERO_RENT_MULTIPLIER')
        self.assertIsNone(a['threshold']); self.assertIsNone(a['actionable_site_override'])
        self.assertIsNone(a['max_viable_base_monthly_rent_inr'])

    def test_invalid_global_multipliers_rejected(self):
        for multiplier in (-1., 4., True, float('nan'), float('inf')):
            p, s = rescue_fixture(); s['assumptions']['rent_multiplier'] = multiplier
            with self.subTest(multiplier=multiplier), self.assertRaises(ValueError):
                prepare_evaluation(p, s)

    def test_negative_zero_rent_npv_is_not_recoverable(self):
        p, s = rescue_fixture(); p['sites'][0]['annual_opex_inr'] = 2000.
        a = calculate_rescue(p, prepare_evaluation(p, s)['context'], 's0', 'rent')
        self.assertEqual(a['status'], 'NOT_RECOVERABLE_WITHIN_BOUNDS')
        self.assertIsNone(a['actionable_site_override']); self.assertIsNone(a['threshold'])

    def test_hard_rejection_blocks_rent_action_and_survives_financial_threshold(self):
        p, s = rescue_fixture()
        p['inputs']['site_eligibility'] = {'s0': dict(hard_failures=['UNAVAILABLE'])}
        a = calculate_rescue(p, prepare_evaluation(p, s)['context'], 's0', 'rent')
        self.assertEqual(a['application_status'], 'BLOCKED_HARD_ELIGIBILITY')
        self.assertEqual(a['status'], 'NOT_RECOVERABLE_WITHIN_BOUNDS')
        self.assertIsNone(a['actionable_site_override'])
        s['assumptions']['site_overrides'] = {'s0': dict(monthly_rent_inr=a['max_viable_base_monthly_rent_inr'])}
        fresh = prepare_evaluation(p, s)['evaluation']['site_analyses'][0]
        self.assertEqual(fresh['failfast']['status'], 'REJECTED')
        self.assertIn('HARD:UNAVAILABLE', fresh['failfast']['failed_rule_ids'])

    def test_base_rent_search_bound_is_preserved(self):
        p, s = rescue_fixture(); s['assumptions']['rent_multiplier'] = 1.2
        a = calculate_rescue(p, prepare_evaluation(p, s)['context'], 's0', 'rent', upper_bound=20.)
        self.assertEqual(a['threshold'], 20.)
        self.assertTrue(a['bound_limits_affordability_threshold'])
        self.assertEqual(a['financial_status'], 'SOLVED')
        self.assertEqual(a['reason'], 'VIABLE_AT_CONFIGURED_UPPER_RENT_BOUND')
        self.assertGreater(apply(p, s, a)['evaluation']['site_analyses'][0]['npv_inr'], 0.)


class SalesApplicationTests(unittest.TestCase):
    def verify_current(self, current):
        p, s = rescue_fixture(); s['assumptions']['site_overrides'] = {'s0': dict(sales_multiplier=current)}
        prepared = prepare_evaluation(p, s); original = digest([p, s, prepared])
        a = calculate_rescue(p, prepared['context'], 's0', 'sales')
        self.assertEqual(a['status'], 'SOLVED')
        self.assertAlmostEqual(a['relative_rescue_multiplier'] * current, a['new_absolute_sales_multiplier'])
        self.assertEqual(a['threshold'], a['actionable_site_override']['sales_multiplier'])
        self.assertEqual(a['threshold'], a['new_absolute_sales_multiplier'])
        self.assertGreaterEqual(a['relative_rescue_multiplier'], .5)
        self.assertLessEqual(a['relative_rescue_multiplier'], 3.)
        self.assertLessEqual(a['threshold'], 3.)
        independent_sales = (1000 / sum(1.1**(-y) for y in range(1, 6)) + 12*50 + 100) / .3
        self.assertAlmostEqual(a['threshold'], independent_sales / 3000, delta=.001)
        fresh = apply(p, s, a)
        value = fresh['evaluation']['site_analyses'][0]['npv_inr']
        self.assertGreaterEqual(value, 0.); self.assertLessEqual(value, 1.)
        self.assertAlmostEqual(value, a['applied_verification']['npv_inr'], places=8)
        self.assertEqual(original, digest([p, s, prepared]))

    def test_current_absolute_one_applies_zero_npv_scenario(self):
        self.verify_current(1.)

    def test_current_absolute_two_applies_zero_npv_scenario(self):
        self.verify_current(2.)

    def test_demand_once_and_existing_store_displacement_recomputed(self):
        p, s = rescue_fixture(); original, _ = fixture(); p['stores'] = original['stores']
        s['assumptions'].update(demand_multiplier=.8, rent_multiplier=1.2,
                                site_overrides={'s0': dict(sales_multiplier=2.)})
        before = prepare_evaluation(p, s)
        a = calculate_rescue(p, before['context'], 's0', 'sales')
        self.assertEqual(a['status'], 'SOLVED')
        fresh = apply(p, s, a); analysis = fresh['evaluation']['site_analyses'][0]
        self.assertGreater(analysis['lost_existing_contribution_inr'], before['evaluation']['site_analyses'][0]['lost_existing_contribution_inr'])
        for year in fresh['context']['frozen_network']['target_by_year_inr']:
            self.assertAlmostEqual(year[0], 3000 * .8 * a['threshold'])
        expected_cash = analysis['annual_revenue_inr']*.3 - 12*50*1.2 - 100 - analysis['lost_existing_contribution_inr']
        self.assertAlmostEqual(analysis['annual_cashflows_inr'][0], expected_cash)
        self.assertGreaterEqual(analysis['npv_inr'], 0.); self.assertLessEqual(analysis['npv_inr'], 1.)
        self.assertLessEqual(fresh['diagnostics']['site_details']['s0']['base']['conservation_error'], 1e-6)

    def test_unattainable_reference_range_returns_no_action(self):
        p, s = rescue_fixture()
        p['inputs']['reference_predictions']['s0']['reference_annual_sales_inr'] = 9000.
        s['assumptions']['site_overrides'] = {'s0': dict(sales_multiplier=3.)}
        prepared = prepare_evaluation(p, s)
        a = calculate_rescue(p, prepared['context'], 's0', 'sales')
        self.assertEqual(a['status'], 'NOT_RECOVERABLE_WITHIN_BOUNDS')
        self.assertEqual(a['application_status'], 'BLOCKED_REFERENCE_OR_CANONICAL_BOUNDS')
        self.assertIsNone(a['actionable_site_override']); self.assertIsNone(a['threshold'])

    def test_hard_rejection_blocks_sales_action(self):
        p, s = rescue_fixture()
        p['inputs']['site_eligibility'] = {'s0': dict(hard_failures=['UNAVAILABLE'])}
        a = calculate_rescue(p, prepare_evaluation(p, s)['context'], 's0', 'sales')
        self.assertEqual(a['application_status'], 'BLOCKED_HARD_ELIGIBILITY')
        self.assertIsNone(a['actionable_site_override']); self.assertIsNone(a['threshold'])
        self.assertFalse(a['clears_unrelated_failures'])

    def test_configured_relative_bounds_intersect_canonical_limit(self):
        p, s = rescue_fixture(); s['assumptions']['site_overrides'] = {'s0': dict(sales_multiplier=2.)}
        a = calculate_rescue(p, prepare_evaluation(p, s)['context'], 's0', 'sales', lower_bound=2., upper_bound=3.)
        self.assertEqual(a['configured_relative_sales_bounds'], [2., 3.])
        self.assertIsNone(a['effective_relative_sales_bounds'])
        self.assertEqual(a['status'], 'NOT_RECOVERABLE_WITHIN_BOUNDS')
        self.assertIsNone(a['actionable_site_override'])

    def test_zero_current_absolute_multiplier_is_explicitly_blocked(self):
        p, s = rescue_fixture(); s['assumptions']['site_overrides'] = {'s0': dict(sales_multiplier=0.)}
        a = calculate_rescue(p, prepare_evaluation(p, s)['context'], 's0', 'sales')
        self.assertEqual(a['application_status'], 'BLOCKED_ZERO_CURRENT_SALES_MULTIPLIER')
        self.assertIsNone(a['threshold']); self.assertIsNone(a['actionable_site_override'])


class FeasibleSearchTests(unittest.TestCase):
    def test_known_infeasible_lower_endpoint_still_finds_root_one_point_two(self):
        def objective(x):
            if x < 1: raise UnattainableRescue('lower theta bound')
            return 1000 * (x - 1.2)
        a = sales_rescue(objective)
        self.assertEqual(a['status'], 'SOLVED')
        self.assertAlmostEqual(a['threshold'], 1.2, delta=.001)
        self.assertGreaterEqual(a['verified_npv_inr'], 0.); self.assertLessEqual(a['verified_npv_inr'], 1.)

    def test_feasible_interior_with_both_endpoints_infeasible(self):
        def objective(x):
            if not 1 <= x <= 1.4: raise UnattainableRescue('physical interval')
            return 1000 * (x - 1.2)
        a = sales_rescue(objective)
        self.assertEqual(a['status'], 'SOLVED')
        self.assertAlmostEqual(a['threshold'], 1.2, delta=.001)
        self.assertAlmostEqual(a['feasible_bounds'][0], 1., places=10)
        self.assertAlmostEqual(a['feasible_bounds'][1], 1.4, places=10)
        self.assertTrue(a['infeasible_samples'])

    def test_nonmonotonic_objective_does_not_produce_action(self):
        a = sales_rescue(lambda x: 20 - 100*(x - 1.5)**2)
        self.assertEqual(a['status'], 'NON_MONOTONIC'); self.assertIsNone(a['threshold'])

    def test_feasible_but_unrecoverable_objective(self):
        a = sales_rescue(lambda x: -100.)
        self.assertEqual(a['reason'], 'NO_RECOVERY_IN_VERIFIED_FEASIBLE_INTERVAL')
        self.assertIsNone(a['threshold'])

    def test_no_feasible_point_is_distinct_from_numeric_failure(self):
        def impossible(x): raise UnattainableRescue('unattainable')
        a = sales_rescue(impossible)
        self.assertEqual(a['reason'], 'NO_VERIFIED_FEASIBLE_POINT')
        self.assertNotIn('numerical_error', a)

    def test_numerical_error_and_nonfinite_are_explicit_failures(self):
        def broken(x): raise ArithmeticError('calibration failure')
        for objective in (broken, lambda x: float('nan')):
            a = sales_rescue(objective)
            self.assertEqual(a['reason'], 'NUMERICAL_EVALUATION_FAILURE')
            self.assertIsNone(a['threshold']); self.assertFalse(a['infeasible_samples'])

    def test_execution_is_deterministic_and_bounded(self):
        calls = []
        def objective(x): calls.append(x); return 1000*(x-1.2)
        a = sales_rescue(objective); first_calls = calls[:]; calls.clear()
        b = sales_rescue(objective)
        self.assertEqual(a, b); self.assertEqual(first_calls, calls)
        self.assertLessEqual(len(calls), 237)
        self.assertTrue(all(.5 <= x <= 3. for x in calls))


def benchmark(repetitions=5):
    """Actual phase wall clocks. Do not treat example acknowledgements as approval."""
    from ml.decision_engine.run import build_project, baseline_scenario
    root = Path(__file__).resolve().parents[2]
    records = []
    for policy in ('unacknowledged', 'illustrative_acknowledged_risk'):
        for repeat in range(1, repetitions + 1):
            start = perf_counter()
            project = build_project(); scenario = baseline_scenario(project)
            loaded = perf_counter()
            prepared = prepare_evaluation(project, scenario)
            evaluated = perf_counter()
            risk = [a['site_id'] for a in prepared['evaluation']['site_analyses'] if a['failfast']['status'] == 'AT_RISK']
            acknowledgements = risk if policy == 'illustrative_acknowledged_risk' else []
            portfolio = run_portfolio(project, prepared['context'], 10, acknowledgements)
            finished = perf_counter()
            predictions = project['inputs']['reference_predictions']
            assert all(p['automatic_calibration_permitted'] is False and 'SHIFTED_MARKET_DEGRADATION_REVIEW' in p['warnings'] for p in predictions.values())
            records.append(dict(policy=policy,repeat=repeat,
                source_and_inference_seconds=loaded-start, evaluation_prepare_seconds=evaluated-loaded,
                portfolio_search_seconds=finished-evaluated, total_flow_seconds=finished-start,
                candidates=len(project['sites']),cells=len(project['inputs']['cells']),branches=len(project['stores']),
                budget_inr=scenario['budget_inr'],max_stores=10,acknowledged_risk_site_ids=acknowledgements,
                method_mode=prepared['evaluation']['method_mode'], model_artifact_id=prepared['evaluation']['model_artifact_id'],
                preserved_prediction_warnings=True, **portfolio))
    summaries = {}
    for policy in sorted({r['policy'] for r in records}):
        selected = [r for r in records if r['policy']==policy]
        summaries[policy] = {key:dict(median=median(r[key] for r in selected),maximum=max(r[key] for r in selected))
                            for key in ['source_and_inference_seconds','evaluation_prepare_seconds','portfolio_search_seconds','total_flow_seconds']}
    out = root/'.runtime/ml-final-handoff';out.mkdir(parents=True,exist_ok=True)
    result = dict(records=records,summaries=summaries,
        measured_portfolio_target_met=all(r['portfolio_search_seconds']<=5 and r['status']=='FULL_NETWORK_EXACT' for r in records),
        timer_scope='Actual wall clock from source/model loading through final portfolio; excludes Python startup/imports. New prepared project/evaluation for each policy/run; filesystem caches may be warm.',
        readiness_note='Existing offline consumer policy only. automatic_calibration_permitted=False is preserved, not overridden or enforced here; H02 requires teammate coordination.',
        acknowledgements_note='Acknowledged case is a declared offline demonstration policy, not human investment approval.',
        hard_timeout_note='Passing timings do not fix or prove strict in-flight cancellation; Part G code is unchanged.')
    (out/'portfolio_benchmark.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return result


if __name__ == '__main__':
    import sys
    if '--benchmark' in sys.argv:
        benchmark()
    else:
        unittest.main()
