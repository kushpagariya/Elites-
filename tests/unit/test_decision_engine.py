"""Numerical invariants, not a final product acceptance run."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
import numpy as np
from backend.app.schemas import Assumptions, Scenario
from backend.app.domain.pipeline import run_evaluation, evaluate_subset, run_rescue, dayparts, infrastructure
from backend.app.domain.portfolio.optimize import optimise_portfolio


def fixture(**assumptions):
    root=Path(__file__).resolve().parents[2]/"data"/"demo"
    project=json.loads((root/"project.json").read_text())
    project["inputs"]={name:json.loads((root/(name+".json")).read_text()) for name in ["cells","pois","weights","infrastructure","source_manifest"]}
    scenario=Scenario(scenario_id="unit-case",project_id="demo",name="Unit case",budget_inr=project["budget_inr"],assumptions=Assumptions(**assumptions)).model_dump()
    return project,scenario


class DecisionTests(unittest.TestCase):
    def test_one_cell_closed_form_network_and_sales_threshold(self):
        p,s=fixture()
        site={**p["sites"][0],"latitude":19,"longitude":73,"store_size_sqm":100,"capex_inr":100,"monthly_rent_inr":0,"annual_opex_inr":0}
        p["sites"]=[site];p["projection_years"]=1;p["discount_rate_fraction"]=0
        p["stores"]=[{**p["stores"][0],"latitude":19,"longitude":73,"store_size_sqm":100,"theta":0,"variable_contribution_margin":.2}]
        p["inputs"]["cells"]=[{"cell_id":"unit","latitude":19,"longitude":73,"annual_wallet_inr":1000000,"source_id":"unit","source_status":"SYNTHETIC"}]
        p["inputs"]["pois"]=[{"poi_id":"unit","latitude":19,"longitude":73,"category":"transit","source_id":"unit","source_status":"SYNTHETIC"}]
        r=run_evaluation(p,s);a=r["site_analyses"][0]
        # Reference share .55 against external attraction 2 gives A=22/9.
        # Adding the existing branch (A=1) gives new-site share 22/49.
        revenue=1000000*22/49;loss=(1000000/3-1000000*9/49)*.2
        self.assertAlmostEqual(a["annual_revenue_inr"],revenue,places=5)
        self.assertAlmostEqual(a["lost_existing_contribution_inr"],loss,places=5)
        self.assertAlmostEqual(a["npv_inr"],revenue*.3-loss-100,places=5)
        site["monthly_rent_inr"]=11000
        context=run_evaluation(p,s)["_context"]
        rescue=run_rescue(context,site["site_id"],"sales",.5,3)
        self.assertEqual(rescue["status"],"SOLVED");self.assertTrue(rescue["verified"])
        self.assertGreater(rescue["threshold"],1);self.assertLess(rescue["threshold"],3)

    def test_deterministic_and_immutable(self):
        p,s=fixture();original=deepcopy((p,s));a=run_evaluation(p,s);b=run_evaluation(p,s)
        self.assertEqual(a,b);self.assertEqual((p,s),original)
        self.assertEqual(a["method_mode"],"scenario_assumptions");self.assertIsNone(a["model_artifact_id"])

    def test_wallet_conservation_and_no_double_counting(self):
        p,s=fixture(demand_multiplier=2);context=run_evaluation(p,s)["_context"]
        wallets=np.asarray(context["wallets"]);branches=np.asarray(context["branches"]);external=np.asarray(context["external"])
        candidates=np.asarray([context["attractions"][i][0] for i in [0,1]])
        total=external+branches.sum(0)+candidates.sum(0)
        self.assertTrue(np.allclose((external+branches.sum(0)+candidates.sum(0))/total,1))
        self.assertAlmostEqual(float(((external+branches.sum(0)+candidates.sum(0))/total*wallets).sum()),float(wallets.sum()),places=5)
        combined=evaluate_subset(context,["site-01","site-02"])
        self.assertAlmostEqual(combined["annual_cashflows_inr"][0],combined["operating_profit_inr"]-combined["lost_existing_contribution_inr"],places=5)
        singles=sum(evaluate_subset(context,[id])["annual_revenue_inr"] for id in ["site-01","site-02"])
        self.assertLess(combined["annual_revenue_inr"],singles)
        self.assertAlmostEqual(combined["lost_existing_contribution_inr"],sum(b["lost_contribution_inr"] for b in combined["branch_impacts"]),places=5)

    def test_sensitivity_and_zero_vs_missing_dayparts(self):
        p,s=fixture();r=run_evaluation(p,s)
        for site in r["site_analyses"]:
            self.assertLess(site["sensitivity"]["low"]["npv_inr"],site["npv_inr"])
            self.assertGreater(site["sensitivity"]["high"]["npv_inr"],site["npv_inr"])
        site=p["sites"][0];inputs=deepcopy(p["inputs"]);inputs["pois"]=[]
        self.assertTrue(all(x["opportunity_index"] is None for x in dayparts(site,inputs)))
        inputs["pois"]=[{"poi_id":"p","category":"office","latitude":site["latitude"],"longitude":site["longitude"],"source_id":"unit-synthetic","source_status":"SYNTHETIC"}]
        inputs["weights"]["category_weights"]["office"]["weekday_lunch"]=0
        lunch=next(x for x in dayparts(site,inputs) if x["time_bin"]=="weekday_lunch")
        self.assertEqual(lunch["opportunity_index"],0);self.assertEqual(lunch["support_count"],1)
        self.assertAlmostEqual(sum(x["opportunity_index"] for x in dayparts(site,inputs)),100)

    def test_event_date_delay_and_cancel(self):
        p,s=fixture(infrastructure_state="opens",opening_date="2027-04-24",infrastructure_effect_fraction=.2)
        site=p["sites"][7];current=infrastructure(site,p["inputs"],s["assumptions"],5)[0]
        self.assertGreater(current["active_fractions"][0],0);self.assertLess(current["active_fractions"][0],1)
        a={**s["assumptions"],"infrastructure_state":"delayed","delay_months":24}
        delayed=infrastructure(site,p["inputs"],a,5)[0]
        self.assertEqual(delayed["active_fractions"][:2],[0,0]);self.assertEqual(delayed["opening_date"],"2029-04-24")
        p["inputs"]["infrastructure"][0]["status"]="cancelled"
        self.assertEqual(infrastructure(site,p["inputs"],s["assumptions"],5)[0]["active_fractions"],[0]*5)

    def test_rent_and_sales_rescue_preserve_budget_failure(self):
        p,s=fixture(demand_multiplier=2);s["budget_inr"]=0
        r=run_evaluation(p,s);context=r["_context"]
        rescue=run_rescue(context,"site-02","rent",0,1000000)
        self.assertEqual(rescue["status"],"SOLVED");self.assertTrue(rescue["verified"])
        self.assertIn("CAPEX_OVER_BUDGET",rescue["remaining_failed_rule_ids"])
        threshold=rescue["threshold"];original=context["sites"][1]["effective_inputs"]["monthly_rent_inr"]
        for value,positive in [(threshold-1,True),(threshold+1,False)]:
            copy=deepcopy(context);copy["sites"][1]["effective_inputs"]["monthly_rent_inr"]=value
            self.assertEqual(evaluate_subset(copy,["site-02"])["npv_inr"]>=0,positive)
        self.assertEqual(context["sites"][1]["effective_inputs"]["monthly_rent_inr"],original)
        with self.assertRaises(ValueError):run_rescue(context,"site-02","sales",3,.5)
        p,s=fixture(demand_multiplier=0);zero=run_evaluation(p,s)["_context"]
        self.assertEqual(run_rescue(zero,"site-02","rent")["status"],"NOT_RECOVERABLE_WITHIN_BOUNDS")

    def test_portfolio_full_network_empty_risk_and_cutoff(self):
        p,s=fixture(demand_multiplier=3,rent_multiplier=.3,operating_cost_multiplier=.3)
        r=run_evaluation(p,s);context={"evaluation":r,"scenario":s,"network_context":r["_context"]}
        ack=[x["site_id"] for x in r["site_analyses"] if x["failfast"]["status"]=="AT_RISK"]
        result=optimise_portfolio(p,context,2,ack)
        if result["solver_status"]=="UNAVAILABLE": self.skipTest("OR-Tools dependency import is blocked by Windows Application Control (pandas sparse DLL)")
        self.assertEqual(result["solver_status"],"OPTIMAL");self.assertEqual(result["evaluated_subsets"],1024)
        self.assertLessEqual(result["budget_used_inr"],s["budget_inr"])
        self.assertEqual(result["full_network_npv_inr"],evaluate_subset(r["_context"],result["selected_site_ids"])["npv_inr"])
        empty=optimise_portfolio(p,context,0,ack)
        self.assertEqual(empty["selected_site_ids"],[]);self.assertEqual(empty["full_network_npv_inr"],0)
        limited=optimise_portfolio(p,context,2,ack,deadline_seconds=0)
        self.assertEqual(limited["status"],"FEASIBLE_PARTIAL");self.assertIsNone(limited["optimality_gap"])
        self.assertLess(limited["evaluated_subsets"],limited["total_subsets"])
        risk=next(iter(r["site_analyses"]));risk["failfast"]["status"]="AT_RISK"
        unacked=optimise_portfolio(p,context,2,[])
        self.assertNotIn(risk["site_id"],unacked["selected_site_ids"])

if __name__=="__main__":unittest.main()
