"""Source-grounded synthetic templates; no candidate row or outcome ingestion."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from ml.training.reference_sales.features import FEATURES,POIS,DAYPART
from ml.training.reference_sales.simulator import CATEGORY_WEIGHTS,COUNT_MAP,WEEKLY_HOURS

ROOT=Path(__file__).resolve().parents[3]

def config():return json.loads(Path(__file__).with_name('config.json').read_text())

def xy(frame):
    # Local synthetic-template projection; metric, not Euclidean degrees.
    return np.column_stack(((frame.longitude.to_numpy()-77.6625)*111195*np.cos(np.deg2rad(12.8775)),(frame.latitude.to_numpy()-12.8775)*111195))

def sources():
    p=ROOT/'data/bengaluru/final';pois=pd.read_csv(p/'pois.csv',keep_default_na=False)
    cells=pd.read_csv(p/'spending_cells.csv');availability=pd.read_csv(p/'poi_daypart_availability.csv')
    lookup={(r.poi_id,r.time_bin):(r.availability_fraction*r.evidence_weight) for r in availability.itertuples()}
    category={'office':0,'shopping':1,'leisure':2,'school':3,'hospital':4,'transit':5}
    pp=pois[pois.category.isin(category)].copy();cats=pp.category.map(category).to_numpy(int)
    effective=np.array([[lookup[(pid,b.removesuffix('_raw'))] for b in DAYPART] for pid in pp.poi_id])
    # Sixteen quadrature subcells per source grid cell; original totals conserved.
    offsets=np.array([(x,y) for x in [-.375,-.125,.125,.375] for y in [-.375,-.125,.125,.375]])
    sub=(xy(cells)[:,None,:]+np.sqrt(cells.area_sqm.to_numpy())[:,None,None]*offsets).reshape(-1,2)
    population=np.repeat(cells.population_est.to_numpy()/16,16)
    wallets=np.repeat(cells.annual_wallet_inr.to_numpy()/16,16)
    return dict(poi_xy=xy(pp),poi_category=cats,poi_opportunity=CATEGORY_WEIGHTS[cats]*effective,
        competitor_xy=xy(pois[pois.category=='competitor']),cell_xy=sub,population=population,wallets=wallets,
        bbox=np.array([xy(cells).min(axis=0),xy(cells).max(axis=0)]))

def allocation(wallets,distance,competitor_distances,area,theta,tau=750,outside=1):
    wallets=np.asarray(wallets,dtype=float)
    attraction=np.exp(theta)*(area/100)*np.exp(-np.asarray(distance)/tau)
    external=np.exp(-np.asarray(competitor_distances)/tau).sum(axis=1)
    denominator=outside+external+attraction
    candidate=wallets*attraction/denominator;comp=wallets*external/denominator;other=wallets*outside/denominator
    return dict(reference_annual_sales_inr=float(candidate.sum()),allocated_external_inr=float(comp.sum()),allocated_outside_inr=float(other.sum()),
        annual_wallet_inr=float(wallets.sum()),raw_pre_bound_sales_inr=float(candidate.sum()),capacity_applied=False,
        max_cell_conservation_error_inr=float(np.max(np.abs(candidate+comp+other-wallets))))

def generate_market(index,shifted=False,cfg=None,src=None):
    cfg=cfg or config();src=src or sources();rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],int(shifted),index]))
    regime=cfg['shifted'] if shifted else {};mid=('v2-ood-' if shifted else 'v2-market-')+f'{index:03d}'
    angle=rng.uniform(0,2*np.pi);rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    scale=rng.uniform(*cfg['geometry_scale']);transform=lambda x:x@rotation.T*scale
    cell_xy=transform(src['cell_xy']);people=src['population']*rng.uniform(*cfg['population_multiplier'])
    wallets=src['wallets']*(people/src['population'])*rng.uniform(.85,1.15)*regime.get('wallet_multiplier',1)
    intensity=rng.uniform(*cfg['poi_intensity_multiplier'])
    # Poisson multiplicities create synthetic copies/omissions, never new observations.
    pi=np.repeat(np.arange(len(src['poi_xy'])),rng.poisson(intensity,len(src['poi_xy'])))
    ci=np.repeat(np.arange(len(src['competitor_xy'])),rng.poisson(intensity*regime.get('competitor_multiplier',1),len(src['competitor_xy'])))
    poi_xy=transform(src['poi_xy'][pi]+rng.normal(0,cfg['source_position_jitter_m'],(len(pi),2)))
    comp_xy=transform(src['competitor_xy'][ci]+rng.normal(0,cfg['source_position_jitter_m'],(len(ci),2)))
    tau=regime.get('tau_m',cfg['tau_m']);outside=regime.get('outside',cfg['outside'])
    market_theta=rng.normal(0,cfg['market_theta_sd'])+regime.get('theta_offset',0)
    cell_comp=np.linalg.norm(cell_xy[:,None,:]-comp_xy[None,:,:],axis=2)
    positions=transform(rng.uniform(src['bbox'][0],src['bbox'][1],(cfg['alternatives_per_market'],2)))
    rows=[]
    for j,position in enumerate(positions):
        d=np.linalg.norm(cell_xy-position,axis=1);mask=d<=1500
        pdist=np.linalg.norm(poi_xy-position,axis=1);pnear=pdist<=1500
        cd=np.linalg.norm(comp_xy-position,axis=1);cnear=cd<=1500
        raw=(np.exp(-pdist[pnear]/750)[:,None]*src['poi_opportunity'][pi[pnear]]).sum(axis=0)
        counts=np.bincount(src['poi_category'][pi[pnear]],minlength=6)
        fmt=str(rng.choice(list(cfg['format_area_ranges'])));area=float(rng.uniform(*cfg['format_area_ranges'][fmt]))
        temporal=float(np.dot(raw,WEEKLY_HOURS)/168)
        theta=cfg['format_theta'][fmt]+market_theta+rng.uniform(*cfg['bounded_individual_theta_noise'])+cfg['daypart_theta_strength']*np.tanh(temporal/cfg['daypart_scale'])
        result=allocation(wallets[mask],d[mask],cell_comp[mask][:,cnear],area,theta,tau,outside)
        rows.append(dict(market_id=mid,observation_id=mid+f'-alternative-{j:02d}',regime='ood' if shifted else 'ordinary',source_status='SYNTHETIC',method_mode='model_simulated',
            store_size_sqm=area,population_1500m_est=float(people[mask].sum()),competitor_count_1500m=int(cnear.sum()),
            competitor_attraction_index=float(np.exp(-cd[cnear]/750).sum()),nearest_competitor_distance_m=float(cd[cnear].min()) if cnear.any() else None,
            mean_wallet_weighted_distance_m=float(np.average(d[mask],weights=wallets[mask])),store_format=fmt,
            **{name:int(counts[k]) for name,k in zip(POIS,COUNT_MAP)},**{name:float(v) for name,v in zip(DAYPART,raw)},**result,
            generator_theta=theta,candidate_x_m=float(position[0]),candidate_y_m=float(position[1])))
    return rows,dict(market_id=mid,source_geometry_scale=scale,tau_m=tau,outside=outside,market_theta=market_theta,
        own_branches=0,alternatives_simultaneously_open=False,cell_count=len(cell_xy))

def generate(cfg=None):
    cfg=cfg or config();src=sources();regular=[];ood=[];markets=[]
    for shift,count in [(False,cfg['ordinary_markets']),(True,cfg['shifted_markets'])]:
        for i in range(count):
            rows,meta=generate_market(i,shift,cfg,src);(ood if shift else regular).extend(rows);markets.append(meta)
    ids=np.random.default_rng(cfg['split_seed']).permutation(sorted({r['market_id'] for r in regular}))
    splits=[dict(market_id=str(mid),split='train' if i<60 else 'validation' if i<80 else 'test') for i,mid in enumerate(ids)]
    splits += [dict(market_id=mid,split='ood') for mid in sorted({r['market_id'] for r in ood})]
    return pd.DataFrame(regular),pd.DataFrame(ood),pd.DataFrame(splits),markets
