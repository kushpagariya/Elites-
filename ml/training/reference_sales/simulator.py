"""Controlled spending-allocation simulator, not a production Huff engine.

All geometry is independently generated in local metric coordinates. Alternative
sites are considered one at a time; no own-company branches exist in this model.
No Bengaluru data is read by this module.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

from .features import DAYPART, POIS, TARGET

CONFIG_PATH=Path(__file__).with_name('config.json')
# Approved category weights, explicitly versioned here, not a shared-fixture edit.
CATEGORY_WEIGHTS=np.array([
    [3,4,2,.2,.5,.3], [1,2,4,.3,4,4], [.3,1,3,1,3,4],
    [4,2,1,.1,.2,.1], [2,2,2,1,2,1], [4,2,4,1,2,2],
],dtype=float)
# Matrix order office/shopping/leisure/school/hospital/transit.
COUNT_MAP=(0,3,4,5,1,2)
WEEKLY_HOURS=np.array([25,20,25,50,24,24],dtype=float)


def config():
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))


def distances(a,b):
    return np.sqrt(((a[:,None,:]-b[None,:,:])**2).sum(axis=2))


def allocate_reference(wallets,candidate_attraction,external_attraction,outside_attraction,capacity):
    """One candidate plus external competitors and a positive outside option.

    Capacity-constrained unserved candidate demand returns to the outside
    option. Stochastic variation occurs upstream in attraction, never as an
    unconstrained additive perturbation to sales.
    """
    wallets=np.asarray(wallets,dtype=float)
    cand=np.asarray(candidate_attraction,dtype=float)
    comp=np.asarray(external_attraction,dtype=float)
    outside=np.broadcast_to(np.asarray(outside_attraction,dtype=float),wallets.shape)
    if not (wallets.shape==cand.shape==comp.shape) or not all(np.isfinite(v).all() for v in [wallets,cand,comp,outside]):
        raise ValueError('Finite, matching cell arrays required')
    if np.any(wallets<0) or np.any(cand<0) or np.any(comp<0) or np.any(outside<=0) or not np.isfinite(capacity) or capacity<0:
        raise ValueError('Invalid wallet/attraction/capacity')
    denom=cand+comp+outside
    initial=wallets*cand/denom
    raw=float(initial.sum())
    served=min(1.,capacity/raw) if raw else 1.
    candidate=initial*served
    external=wallets*comp/denom
    outside_amount=wallets-candidate-external
    return dict(reference_annual_sales_inr=float(candidate.sum()),allocated_external_inr=float(external.sum()),
        allocated_outside_inr=float(outside_amount.sum()),addressable_wallet_bound_inr=float(wallets.sum()),
        unconstrained_candidate_sales_inr=raw,capacity_limit_inr=float(capacity),purchase_completion_fraction=served,
        max_cell_conservation_error_inr=float(np.max(np.abs(candidate+external+outside_amount-wallets))) if len(wallets) else 0.)


def generate_market(index,shifted=False,cfg=None):
    cfg=cfg or config();regime='shifted' if shifted else 'regular';p=cfg[regime]
    rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],int(shifted),index]))
    uniform=lambda key:float(rng.uniform(*p[key]))
    market_id=('ood' if shifted else 'sim')+f'-m{index:04d}'
    side=cfg['cell_grid_side'];half=cfg['market_half_width_m'];step=2*half/side
    axis=np.linspace(-half+step/2,half-step/2,side)
    cells=np.array([(x,y) for x in axis for y in axis])
    density=uniform('population_per_cell_range');spend=uniform('annual_wallet_per_person_inr_range')
    pop=density*np.clip(rng.lognormal(-.08,.4,len(cells)),.35,2.5)
    spending=spend*np.clip(rng.lognormal(-.005,.1,len(cells)),.75,1.3)
    wallets=pop*spending
    tau=uniform('allocation_decay_m_range');outside=uniform('outside_attraction_range');appeal=uniform('market_appeal_range')
    capacity_density=uniform('annual_capacity_inr_per_sqm_range')
    ncomp=int(rng.integers(p['external_competitors_range'][0],p['external_competitors_range'][1]+1))
    comp_xy=rng.uniform(-half,half,(ncomp,2))
    comp_mass=rng.uniform(*p['competitor_mass_range'],ncomp)
    cell_comp=np.exp(-distances(cells,comp_xy)/tau)*comp_mass[None,:]
    npoi=int(rng.integers(p['poi_count_range'][0],p['poi_count_range'][1]+1))
    poi_xy=rng.uniform(-half,half,(npoi,2));categories=rng.choice(6,npoi,p=rng.dirichlet(np.ones(6)*2))
    # Missing schedules retain the same explicit 0.5 availability/evidence role;
    # supported schedules vary by bin. These are synthetic schedules throughout.
    parsed=rng.random(npoi)<rng.uniform(.03,.35)
    availability=rng.uniform(.05,1,(npoi,6))
    availability[~parsed]=.5
    evidence=np.where(parsed,1.,.5)
    poi_contribution=CATEGORY_WEIGHTS[categories]*availability*evidence[:,None]
    candidates=rng.uniform(-cfg['candidate_half_width_m'],cfg['candidate_half_width_m'],(cfg['alternatives_per_market'],2))
    rows=[]
    for j,xy in enumerate(candidates):
        cell_d=np.linalg.norm(cells-xy,axis=1);mask=cell_d<=cfg['catchment_radius_m']
        fmt=str(rng.choice(list(cfg['formats'])));fp=cfg['formats'][fmt]
        area=float(rng.uniform(*fp['area_range_sqm']))
        cd=np.linalg.norm(comp_xy-xy,axis=1);near_comp=cd<=cfg['catchment_radius_m']
        pd=np.linalg.norm(poi_xy-xy,axis=1);near_poi=pd<=cfg['catchment_radius_m']
        feature_tau=cfg['feature_distance_decay_m']
        raw=(np.exp(-pd[near_poi]/feature_tau)[:,None]*poi_contribution[near_poi]).sum(axis=0)
        counts=np.bincount(categories[near_poi],minlength=6)
        wallet=float(wallets[mask].sum());population=float(pop[mask].sum())
        weighted_distance=float(np.average(cell_d[mask],weights=wallets[mask]))
        strength=float(np.dot(raw,WEEKLY_HOURS*np.asarray(fp['daypart_preferences']))/WEEKLY_HOURS.sum())
        temporal_appeal=np.exp(cfg['daypart_utility_coefficient']*np.tanh(strength/cfg['daypart_utility_scale']))
        noise=float(np.clip(rng.lognormal(0,cfg['noise']['appeal_lognormal_sigma']),*cfg['noise']['appeal_multiplier_bounds']))
        attraction=(area/100)*fp['appeal']*appeal*noise*temporal_appeal*np.exp(-cell_d[mask]/tau)
        allocation=allocate_reference(wallets[mask],attraction,cell_comp[mask][:,near_comp].sum(axis=1),outside,area*capacity_density)
        r=dict(market_id=market_id,observation_id=market_id+f'-alt{j:02d}',regime=regime,
            source_status='SYNTHETIC',method_mode='model_simulated',store_size_sqm=area,annual_wallet_inr=wallet,
            population_1500m_est=population,competitor_count_1500m=int(near_comp.sum()),
            competitor_attraction_index=float(np.exp(-cd[near_comp]/feature_tau).sum()),
            nearest_competitor_distance_m=float(cd[near_comp].min()) if near_comp.any() else None,
            mean_wallet_weighted_distance_m=weighted_distance,store_format=fmt,
            **{name:int(counts[k]) for name,k in zip(POIS,COUNT_MAP)},**{name:float(x) for name,x in zip(DAYPART,raw)},**allocation)
        rows.append(r)
    summary=dict(market_id=market_id,regime=regime,seed_components=[cfg['seed'],int(shifted),index],
        cell_count=len(cells),market_population=float(pop.sum()),market_wallet_inr=float(wallets.sum()),external_competitors=ncomp,
        poi_count=npoi,allocation_decay_m=tau,outside_attraction=outside,market_appeal=appeal,
        annual_capacity_inr_per_sqm=capacity_density,own_company_branches=0,
        alternatives_simultaneously_open=False,origin='SYNTHETIC_NOT_OBSERVED')
    return rows,summary


def generate(cfg=None):
    cfg=cfg or config();regular=[];shifted=[];markets=[]
    for is_shifted,count in [(False,cfg['regular_markets']),(True,cfg['shifted_markets'])]:
        for index in range(count):
            rows,summary=generate_market(index,is_shifted,cfg)
            (shifted if is_shifted else regular).extend(rows);markets.append(summary)
    ids=np.array(sorted({r['market_id'] for r in regular}))
    ids=np.random.default_rng(cfg['split_seed']).permutation(ids)
    ntrain=int(.6*len(ids));nval=int(.2*len(ids))
    splits=[dict(market_id=str(mid),split='train' if i<ntrain else 'validation' if i<ntrain+nval else 'test') for i,mid in enumerate(ids)]
    splits += [dict(market_id=mid,split='ood') for mid in sorted({r['market_id'] for r in shifted})]
    return pd.DataFrame(regular),pd.DataFrame(shifted),pd.DataFrame(splits),markets
