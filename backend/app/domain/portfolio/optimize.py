"""CP-SAT selection over exact, full-network subset values (maximum ten sites)."""
from decimal import Decimal, ROUND_HALF_UP
from time import monotonic
from ..pipeline import evaluate_subset


def paise(amount):
    return int((Decimal(str(amount))*100).quantize(Decimal(1),rounding=ROUND_HALF_UP))


def optimise_portfolio(project, context, max_stores, acknowledged_risk_site_ids, *, deadline_seconds=5.0):
    evaluation=context["evaluation"]; scenario=context["scenario"]; network=context["network_context"]
    budget=paise(scenario["budget_inr"]); end=monotonic()+max(0,deadline_seconds)
    sites=sorted(project["sites"],key=lambda x:x["site_id"]); analyses={x["site_id"]:x for x in evaluation["site_analyses"]}
    if len(sites)>10 or not 0<=max_stores<=10: raise ValueError("Prototype supports at most ten sites")
    known={x["site_id"] for x in sites}
    if set(acknowledged_risk_site_ids)-known: raise ValueError("Unknown risk acknowledgement")
    eligible=set(); exclusions=[]
    for site in sites:
        sid=site["site_id"]; a=analyses[sid]; status=a["failfast"]["status"]
        reasons=[]; codes=[]
        if status in {"REJECTED","REVIEW_REQUIRED"}:
            codes+=a["failfast"]["failed_rule_ids"] or [status]; reasons+=a["failfast"]["reasons"] or ["This location is not eligible."]
        elif status=="AT_RISK" and sid not in acknowledged_risk_site_ids:
            codes.append("RISK_NOT_ACKNOWLEDGED");reasons.append("Acknowledge this location’s downside risk before including it.")
        elif paise(site["capex_inr"])>budget:
            codes.append("CAPEX_OVER_BUDGET");reasons.append("Initial investment exceeds the scenario budget.")
        else: eligible.add(sid)
        if codes: exclusions.append({"site_id":sid,"reason_codes":codes,"reasons":reasons})
    result={"selected_site_ids":[],"budget_used_inr":0,"budget_unused_inr":budget/100,"full_network_npv_inr":0,
            "status":"UNKNOWN","evaluated_subsets":0,"total_subsets":2**len(sites),"solver_status":"UNKNOWN",
            "solver_name":"Google OR-Tools CP-SAT","solver_version":None,"exclusions":exclusions,
            "objective_precision_inr":.01,"optimality_gap":None,"limitations":["Full-network subset values include branch displacement and candidate overlap once; no additional pair penalty."]}
    try:
        import ortools
        from ortools.sat.python import cp_model
    except (ImportError, OSError):
        # TODO: needs backend — verify an OR-Tools runtime permitted by the host application-control policy.
        return {**result,"solver_status":"UNAVAILABLE","limitations":result["limitations"]+["OR-Tools is unavailable; no portfolio recommendation was computed."]}
    result["solver_version"]=ortools.__version__
    rows=[{"ids":[],"cost":0,"npv":0,"value":0.0}];examined=0
    for mask in range(2**len(sites)):
        if mask and monotonic()>=end: break
        examined+=1
        selected=[s for i,s in enumerate(sites) if mask&(1<<i)]
        if not selected: continue
        ids=[s["site_id"] for s in selected];cost=sum(paise(s["capex_inr"]) for s in selected)
        if len(ids)>max_stores or cost>budget or not set(ids)<=eligible: continue
        value=evaluate_subset(network,ids)["npv_inr"]
        rows.append({"ids":ids,"cost":cost,"npv":paise(value),"value":value})
    # Exact primary objective and deterministic tie policies, with no coefficient multiplication overflow.
    lex={tuple(r["ids"]):i for i,r in enumerate(sorted(rows,key=lambda r:r["ids"]))}
    model=cp_model.CpModel(); choice=[model.new_bool_var(f"subset_{i}") for i in range(len(rows))]
    model.add(sum(choice)==1)
    cost=sum(r["cost"]*v for r,v in zip(rows,choice));count=sum(len(r["ids"])*v for r,v in zip(rows,choice))
    model.add(cost<=budget);model.add(count<=max_stores)
    npv=sum(r["npv"]*v for r,v in zip(rows,choice));lex_order=sum(lex[tuple(r["ids"])]*v for r,v in zip(rows,choice))
    solver=cp_model.CpSolver();solver.parameters.num_search_workers=1;solver.parameters.random_seed=0
    best=max(rows,key=lambda r:(r["npv"],-r["cost"],-len(r["ids"]),-lex[tuple(r["ids"])]))
    proven=True
    for expression,maximise in [(npv,True),(cost,False),(count,False),(lex_order,False)]:
        remaining=end-monotonic()
        if remaining<=0: proven=False;break
        solver.parameters.max_time_in_seconds=remaining
        if maximise: model.maximize(expression)
        else: model.minimize(expression)
        status=solver.solve(model)
        if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE): proven=False;break
        best=next(r for r,v in zip(rows,choice) if solver.value(v))
        if status!=cp_model.OPTIMAL: proven=False;break
        model.add(expression==solver.value(expression))
    complete=examined==result["total_subsets"] and proven
    chosen=set(best["ids"])
    for sid in sorted(eligible-chosen):
        site=next(s for s in sites if s["site_id"]==sid)
        if max_stores==0 or len(chosen)>=max_stores: code="STORE_COUNT_LIMIT";reason="The selected combination respects the store-count cap."
        elif best["cost"]+paise(site["capex_inr"])>budget: code="BUDGET_COMBINATION";reason="This site does not fit the remaining investment budget."
        else: code="LOWER_NETWORK_VALUE";reason="Including this site did not improve the best evaluated network value."
        exclusions.append({"site_id":sid,"reason_codes":[code],"reasons":[reason]})
    return {**result,"selected_site_ids":best["ids"],"budget_used_inr":best["cost"]/100,"budget_unused_inr":(budget-best["cost"])/100,
            "full_network_npv_inr":best["value"],"evaluated_subsets":examined,"status":"FULL_NETWORK_EXACT" if complete else "FEASIBLE_PARTIAL",
            "solver_status":"OPTIMAL" if complete else ("FEASIBLE" if examined==result["total_subsets"] else "PARTIAL"),"optimality_gap":0 if complete else None}
