"""Deterministic assumption-based decision engine; no HTTP, persistence or model claims."""
from copy import deepcopy
from datetime import date
import calendar
import math
import numpy as np
from .finance.cashflows import evaluate_cashflows

ENGINE_VERSION = "assumed-wallet-v1"
FINANCE_VERSION = "discounted-cashflows-v1"
RULE_VERSION = "failfast-v1"
MODEL_ARTIFACT_ID = None
PARAMETERS = {"distance_decay_m": 750, "reference_radius_m": 3000,
              "reference_wallet_share": 0.55, "reference_decay_m": 1500,
              "outside_attraction": 1, "external_attraction": 1,
              "area_exponent": 1, "infrastructure_radius_m": 3000,
              "calibration_tolerance_inr": 1}
LIMITATIONS = ["SYNTHETIC business records and geography; no measured sales or footfall.",
               "ASSUMED wallet-share estimator and attraction parameters; no trained model artifact or accuracy evidence.",
               "Sensitivity cases are commercial assumptions, not calibrated prediction intervals.",
               "External competition is an assumed attraction, not an observed competitor inventory.",
               "POI dates and opening hours are unavailable; availability and category weights are assumed."]


def distances(lat, lon, points):
    """Great-circle distances in metres (WGS84 coordinate inputs)."""
    a = np.radians(float(lat)); b = np.radians(float(lon))
    p = np.radians(np.array([[x["latitude"], x["longitude"]] for x in points], dtype=float))
    if not len(p):
        return np.array([], dtype=float)
    h = np.sin((p[:, 0]-a)/2)**2 + np.cos(a)*np.cos(p[:, 0])*np.sin((p[:, 1]-b)/2)**2
    return 6371008.8 * 2 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def shifted(d, months=0, years=0):
    month_index = d.year*12+d.month-1+months+years*12
    year, month = divmod(month_index, 12)
    return date(year, month+1, min(d.day, calendar.monthrange(year, month+1)[1]))


def infrastructure(site, inputs, a, years):
    rows=[]; valuation=date.fromisoformat(a.get("valuation_date", "2026-10-24"))
    for event in inputs["infrastructure"]:
        geometry=event.get("geometry") or {}; coords=geometry.get("coordinates")
        distance=None
        if geometry.get("type")=="Point" and isinstance(coords,list) and len(coords)==2:
            distance=float(distances(site["latitude"],site["longitude"],[{"latitude":coords[1],"longitude":coords[0]}])[0])
        exposure=0 if distance is None else max(0,1-distance/PARAMETERS["infrastructure_radius_m"])
        operational=event.get("status") in {"operational","open","completed"}
        cancelled=event.get("status") in {"cancelled","canceled"}
        opening=a.get("opening_date") or event.get("expected_open_date")
        if not opening and event.get("hypothetical_demo"):
            opening=event.get("assumed_demo_open_date")
        opened=date.fromisoformat(opening) if opening else None
        if opened and a.get("infrastructure_state")=="delayed" and not operational:
            opened=shifted(opened,months=a.get("delay_months",24))
        fractions=[]
        for y in range(years):
            start=shifted(valuation,years=y); end=shifted(valuation,years=y+1)
            active=(not cancelled) and (operational or a.get("infrastructure_state")!="current")
            fraction=1.0 if active and operational else (max(0,(end-max(start,opened)).days)/(end-start).days if active and opened else 0.0)
            fractions.append(min(1.0,fraction))
        rows.append({"event_id":event["infra_project_id"],"distance_m":distance,"exposure_fraction":exposure,
                     "opening_date":opened.isoformat() if opened else None,"active_fractions":fractions,
                     "assumed_effect_fraction":a.get("infrastructure_effect_fraction",0),
                     "hypothetical":bool(event.get("hypothetical_demo"))})
    return rows


def dayparts(site, inputs):
    weights=inputs["weights"]; pois=inputs["pois"]
    ds=distances(site["latitude"],site["longitude"],pois)
    supported=[(p,float(d)) for p,d in zip(pois,ds) if d<=weights["catchment_radius_m"] and p["category"] in weights["category_weights"]]
    # Hours per bin times days per week; no claim of measured visits.
    duration=[25,20,25,50,24,24]; rows=[]
    for time_bin,hours in zip(weights["time_bins"],duration):
        cats={}
        for p,d in supported:
            category=p["category"]; row=cats.setdefault(category,{"category":category,"count":0,"weighted_opportunity":0.0})
            row["count"]+=1
            row["weighted_opportunity"]+=weights["category_weights"][category][time_bin]*math.exp(-d/weights["decay_scale_m"])*hours
        raw=sum(x["weighted_opportunity"] for x in cats.values()) if supported else None
        rows.append({"time_bin":time_bin,"opportunity_index":None,"raw_opportunity":raw,"support_count":len(supported),
                     "categories":list(cats.values()),"source_ids":sorted({p["source_id"] for p,_ in supported}),
                     "source_status":"ASSUMED","reliability":"Illustrative category weights; synthetic POIs; opening hours assumed available.",
                     "observed_at":None,"reason":None if supported else "No supported POI evidence within the catchment."})
    total=sum(r["raw_opportunity"] or 0 for r in rows)
    for row in rows:
        if row["raw_opportunity"] is not None:
            row["opportunity_index"]=100*row["raw_opportunity"]/total if total else 0.0
    return rows


def calibrate(target, distance, area, wallets, external):
    basis=(area/100)**PARAMETERS["area_exponent"]*np.exp(-distance/PARAMETERS["distance_decay_m"])
    def revenue(theta):
        attraction=math.exp(theta)*basis
        return float(np.sum(wallets*attraction/(external+attraction)))
    lo,hi=-30.0,30.0
    if target<=0:
        return np.zeros(len(wallets)),0.0,True
    for _ in range(100):
        mid=(lo+hi)/2
        if revenue(mid)<target: lo=mid
        else: hi=mid
    theta=(lo+hi)/2; achieved=revenue(theta)
    return math.exp(theta)*basis,achieved,abs(achieved-target)<=PARAMETERS["calibration_tolerance_inr"]


def prepare_context(project, scenario):
    inputs=project.get("inputs")
    if not inputs or not all(k in inputs for k in ["cells","pois","weights","infrastructure","source_manifest"]):
        raise ValueError("A complete frozen input snapshot is required")
    cells=inputs["cells"]
    if not cells or len(cells)>2000: raise ValueError("Expected 1–2000 wallet cells")
    a=scenario["assumptions"]; years=project["projection_years"]
    base=np.array([c["annual_wallet_inr"] for c in cells],dtype=float)
    if not np.all(np.isfinite(base)) or np.any(base<0): raise ValueError("Invalid wallet values")
    wallets=base*a.get("demand_multiplier",1)
    external=np.full(len(cells),PARAMETERS["outside_attraction"]+PARAMETERS["external_attraction"]*a.get("competition_multiplier",1))
    branches=np.array([math.exp(b["theta"])*(b["store_size_sqm"]/100)*np.exp(-distances(b["latitude"],b["longitude"],cells)/750) for b in project["stores"]])
    if not len(branches): branches=np.zeros((0,len(cells)))
    sites=[]; frozen=[]
    for site in project["sites"]:
        override=a.get("site_overrides",{}).get(site["site_id"],{})
        def choice(key, default):
            return override[key] if override.get(key) is not None else default
        effective={"monthly_rent_inr":choice("monthly_rent_inr",site["monthly_rent_inr"]*a.get("rent_multiplier",1)),
                   "annual_opex_inr":choice("annual_opex_inr",site["annual_opex_inr"]*a.get("operating_cost_multiplier",1)),
                   "gross_margin_fraction":choice("gross_margin_fraction",a.get("gross_margin_fraction") if a.get("gross_margin_fraction") is not None else site["gross_margin_fraction"]),
                   "sales_multiplier":choice("sales_multiplier",1),
                   "competition_multiplier":a.get("competition_multiplier",1)*choice("competition_multiplier",1)}
        ds=distances(site["latitude"],site["longitude"],cells)
        local=float(np.sum(wallets*np.where(ds<=3000,np.exp(-ds/1500),0)))
        target=local*PARAMETERS["reference_wallet_share"]*math.sqrt(site["store_size_sqm"]/100)*effective["sales_multiplier"]
        # A site-specific competition adjustment changes its reference target once.
        target*= (1+a.get("competition_multiplier",1))/(1+effective["competition_multiplier"])
        exposure=infrastructure(site,inputs,a,years); attractions=[]; calibrations=[]
        for y in range(years):
            factor=max(0,1+sum(e["exposure_fraction"]*e["assumed_effect_fraction"]*e["active_fractions"][y] for e in exposure))
            att,achieved,valid=calibrate(target*factor,ds,site["store_size_sqm"],wallets,external)
            attractions.append(att.tolist());calibrations.append({"target_revenue_inr":target*factor,"achieved_reference_revenue_inr":achieved,"within_tolerance":valid})
        sites.append({**site,"effective_inputs":effective,"infrastructure_exposure":exposure,"calibrations":calibrations,"dayparts":dayparts(site,inputs)})
        frozen.append(attractions)
    return {"project":{k:v for k,v in project.items() if k!="inputs"},"scenario":deepcopy(scenario),"inputs":deepcopy(inputs),
            "wallets":wallets.tolist(),"external":external.tolist(),"branches":branches.tolist(),"sites":sites,"attractions":frozen}


def evaluate_subset(context, site_ids, *, wallet_multiplier=1.0, rent_multiplier=1.0):
    """One common network denominator; existing losses deducted once; overlap implicit."""
    project=context["project"]; sites=context["sites"]; stores=project["stores"]
    wallets=np.asarray(context["wallets"])*wallet_multiplier; external=np.asarray(context["external"])
    branches=np.asarray(context["branches"]).reshape((len(stores),len(wallets)))
    base_denom=external+branches.sum(axis=0)
    baseline=branches/base_denom*wallets
    indices=[i for i,s in enumerate(sites) if s["site_id"] in site_ids]
    if len(site_ids)!=len(set(site_ids)) or len(indices)!=len(site_ids): raise ValueError("Unknown or duplicate candidate ID")
    cashflows=[]; candidate_revenue=[]; operating=[]; losses=[]; after_first=None
    capex=sum(sites[i]["capex_inr"] for i in indices)
    for y in range(project["projection_years"]):
        attrs=np.array([context["attractions"][i][y] for i in indices]).reshape((len(indices),len(wallets)))
        denom=base_denom+attrs.sum(axis=0)
        after=branches/denom*wallets
        revenue=(attrs/denom*wallets).sum(axis=1)
        profit=sum(float(revenue[j])*sites[i]["effective_inputs"]["gross_margin_fraction"]-12*sites[i]["effective_inputs"]["monthly_rent_inr"]*rent_multiplier-sites[i]["effective_inputs"]["annual_opex_inr"] for j,i in enumerate(indices))
        loss=sum(float((baseline[k]-after[k]).sum())*b["variable_contribution_margin"] for k,b in enumerate(stores))
        candidate_revenue.append(float(revenue.sum()));operating.append(profit);losses.append(loss);cashflows.append(profit-loss)
        if after_first is None: after_first=after
    finance=evaluate_cashflows(capex,cashflows,project["discount_rate_fraction"])
    return {"annual_revenue_inr":candidate_revenue[0],"operating_profit_inr":operating[0],"lost_existing_contribution_inr":losses[0],
            "annual_cashflows_inr":cashflows,"npv_inr":finance.npv_inr,"roi_fraction":finance.horizon_roi,"payback_years":finance.payback_years,
            "capex_inr":capex,"branch_impacts":[{"store_id":b["store_id"],"baseline_revenue_inr":float(baseline[k].sum()),"after_revenue_inr":float(after_first[k].sum()),"lost_contribution_inr":float((baseline[k]-after_first[k]).sum())*b["variable_contribution_margin"]} for k,b in enumerate(stores)]}


def diagnose(context, site, result, low):
    rules=[];reasons=[];hard=False;review=False
    if site["capex_inr"]>context["scenario"]["budget_inr"]:
        rules.append("CAPEX_OVER_BUDGET");reasons.append("Initial investment exceeds this scenario’s budget.");hard=True
    cells=context["inputs"]["cells"]
    if not (min(c["latitude"] for c in cells)<=site["latitude"]<=max(c["latitude"] for c in cells) and min(c["longitude"] for c in cells)<=site["longitude"]<=max(c["longitude"] for c in cells)):
        rules.append("OUTSIDE_COVERAGE");reasons.append("Location is outside the supported wallet-cell coverage.");hard=True
    if not all(c["within_tolerance"] for c in site["calibrations"]):
        rules.append("UNATTAINABLE_REFERENCE_TARGET");reasons.append("Requested sales exceed the supported calibration range.");review=True
    if not any(d["support_count"] for d in site["dayparts"]):
        rules.append("MISSING_POI_EVIDENCE");reasons.append("No supporting POI categories were found in the catchment.");review=True
    a=context["scenario"]["assumptions"]
    if a.get("infrastructure_state")!="current" and a.get("infrastructure_effect_fraction",0)!=0 and any(e["distance_m"] is None or e["opening_date"] is None for e in site["infrastructure_exposure"]):
        rules.append("INCOMPLETE_EVENT_EVIDENCE");reasons.append("Infrastructure timing or geographic exposure needs review.");review=True
    if result["npv_inr"]<0:
        rules.append("NEGATIVE_NPV");reasons.append("Expected network cash flows do not recover investment at the selected discount rate.")
    if low["npv_inr"]<0:
        rules.append("DOWNSIDE_NEGATIVE_NPV");reasons.append("The lower-demand, higher-rent case has negative NPV.")
    status="REJECTED" if hard else "REVIEW_REQUIRED" if review else "REJECTED" if result["npv_inr"]<0 else "AT_RISK" if low["npv_inr"]<0 else "VIABLE"
    return {"status":status,"failed_rule_ids":rules,"reasons":reasons,"max_viable_monthly_rent_inr":None,"required_sales_multiplier":None,"rescue_status":"NOT_REQUESTED"}


def run_evaluation(project, scenario):
    context=prepare_context(project,scenario); analyses=[]
    keys=["annual_revenue_inr","operating_profit_inr","lost_existing_contribution_inr","npv_inr","roi_fraction","payback_years"]
    for site in context["sites"]:
        sid=site["site_id"]; base=evaluate_subset(context,[sid]); low=evaluate_subset(context,[sid],wallet_multiplier=.8,rent_multiplier=1.1); high=evaluate_subset(context,[sid],wallet_multiplier=1.2)
        analysis={"site_id":sid,**{k:v for k,v in base.items() if k!="capex_inr"},"failfast":diagnose(context,site,base,low),
                  "effective_inputs":site["effective_inputs"],"infrastructure_exposure":site["infrastructure_exposure"],"calibration":site["calibrations"][0],"dayparts":site["dayparts"],
                  "sensitivity":{name:{k:value[k] for k in keys} for name,value in [("low",low),("base",base),("high",high)]},
                  "drivers":[f"Annual operating profit before branch displacement: INR {base['operating_profit_inr']:,.0f}.",f"Existing-branch contribution displaced: INR {base['lost_existing_contribution_inr']:,.0f} in year one.",f"Downside NPV: INR {low['npv_inr']:,.0f} with 20% lower wallet spending and 10% higher rent."],
                  "source_ids":list(context["inputs"]["source_manifest"]["source_ids"])}
        analyses.append(analysis)
    rankings=[s["site_id"] for s in sorted(analyses,key=lambda s:(-s["npv_inr"],next(x["capex_inr"] for x in context["sites"] if x["site_id"]==s["site_id"]),s["site_id"])) if s["failfast"]["status"] in {"VIABLE","AT_RISK"}]
    inputs=context["inputs"]
    return {"method_mode":"scenario_assumptions","model_artifact_id":MODEL_ARTIFACT_ID,"site_analyses":analyses,"rankings":rankings,
            "evidence":{"feature_snapshot_id":inputs["source_manifest"]["feature_snapshot_id"],"source_snapshot_id":inputs.get("snapshot_id",inputs["source_manifest"]["fixture_id"]),"finance_version":FINANCE_VERSION,"rule_version":RULE_VERSION,"weight_version":inputs["weights"]["weight_version"],"estimator_version":ENGINE_VERSION,"valuation_date":scenario["assumptions"].get("valuation_date","2026-10-24"),"limitations":LIMITATIONS,"assumed_parameters":PARAMETERS},"_context":context}


def run_rescue(context, site_id, lever, lower_bound=None, upper_bound=None):
    site=next((s for s in context["sites"] if s["site_id"]==site_id),None)
    if site is None: raise ValueError("Unknown site")
    lower=float(lower_bound if lower_bound is not None else (0 if lever=="rent" else .5))
    upper=float(upper_bound if upper_bound is not None else (max(site["effective_inputs"]["monthly_rent_inr"]*3,1000000) if lever=="rent" else 3))
    if lower<0 or upper<=lower or (lever=="sales" and (lower<.5 or upper>3)): raise ValueError("Use increasing nonnegative rent bounds, or sales bounds within 0.5–3.0")
    def compute(value):
        if lever=="rent":
            copy=deepcopy(context);next(s for s in copy["sites"] if s["site_id"]==site_id)["effective_inputs"]["monthly_rent_inr"]=value
        else:
            scenario=deepcopy(context["scenario"]);scenario["assumptions"].setdefault("site_overrides",{}).setdefault(site_id,{})["sales_multiplier"]=value
            copy=prepare_context({**context["project"],"inputs":context["inputs"]},scenario)
        return evaluate_subset(copy,[site_id])["npv_inr"]
    if lever=="rent":
        zero=compute(0)
        annuity=sum(1/(1+context["project"]["discount_rate_fraction"])**y for y in range(1,context["project"]["projection_years"]+1))
        exact=zero/(12*annuity)
    samples=[compute(lower+(upper-lower)*i/12) for i in range(13)]
    monotonic=all((b<=a+1e-5 if lever=="rent" else b>=a-1e-5) for a,b in zip(samples,samples[1:]))
    result={"site_id":site_id,"lever":lever,"lower_bound":lower,"upper_bound":upper,"threshold":None,"verified":False,"npv_at_threshold":None,"reasons":[],"remaining_failed_rule_ids":[]}
    if not monotonic: return {**result,"status":"NON_MONOTONIC","reasons":["The selected lever is not monotonic within these bounds."]}
    if (samples[0]<-0.01 if lever=="rent" else samples[-1]<-0.01):
        return {**result,"status":"NOT_RECOVERABLE_WITHIN_BOUNDS","reasons":["No nonnegative NPV threshold exists within the selected bounds."]}
    if lever=="rent" and exact>upper+1e-8:
        return {**result,"status":"NOT_RECOVERABLE_WITHIN_BOUNDS","reasons":["The site remains financially viable at the upper rent bound. Widen the upper bound to find the actual break-even crossing."]}
    if lever=="sales" and samples[0]>1:
        return {**result,"status":"NOT_RECOVERABLE_WITHIN_BOUNDS","reasons":["The site is already financially viable at the lower sales bound; no break-even crossing lies inside this range."]}
    lo,hi=lower,upper
    if lever=="rent": threshold=min(upper,max(lower,exact-1e-8))
    elif lever=="sales" and samples[0]>=0: threshold=lower
    else:
        for _ in range(65):
            mid=(lo+hi)/2; value=compute(mid)
            if (value>=0 if lever=="rent" else value<0): lo=mid
            else: hi=mid
        threshold=lo if lever=="rent" else hi
    value=compute(threshold)
    original=evaluate_subset(context,[site_id]); downside=evaluate_subset(context,[site_id],wallet_multiplier=.8,rent_multiplier=1.1)
    diagnosis=diagnose(context,site,original,downside)
    # This threshold addresses NPV only; budget/coverage/evidence/downside require recomputation.
    remaining=[r for r in diagnosis["failed_rule_ids"] if r!="NEGATIVE_NPV"]
    return {**result,"status":"SOLVED","threshold":threshold,"verified":value>=-0.01,"npv_at_threshold":value,"remaining_failed_rule_ids":remaining,"reasons":["Verified against the same saved network. Saving and evaluating the change rechecks all other rules."]}


def run_portfolio(project, evaluation, max_stores, acknowledged_risk_site_ids):
    from .portfolio.optimize import optimise_portfolio
    return optimise_portfolio(project,evaluation,max_stores,acknowledged_risk_site_ids)


def catchment_ring(latitude, longitude, radius_m):
    """Spherical display catchment, not a road/travel-time isochrone."""
    lat=math.radians(latitude);lon=math.radians(longitude);angle=radius_m/6371008.8;points=[]
    for i in range(65):
        bearing=2*math.pi*i/64
        lat2=math.asin(math.sin(lat)*math.cos(angle)+math.cos(lat)*math.sin(angle)*math.cos(bearing))
        lon2=lon+math.atan2(math.sin(bearing)*math.sin(angle)*math.cos(lat),math.cos(angle)-math.sin(lat)*math.sin(lat2))
        points.append([math.degrees(lon2),math.degrees(lat2)])
    return {"type":"Polygon","coordinates":[points]}
