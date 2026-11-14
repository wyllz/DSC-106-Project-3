"""Pick the CMIP6 ensemble: one member per model, with tas in historical, ssp126 AND ssp585."""
import pandas as pd, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT/'data_cache/cmip6_catalog.csv', low_memory=False)
q = df[(df.table_id=='Amon')&(df.variable_id=='tas')&df.experiment_id.isin(['historical','ssp126','ssp585'])]
rows=[]
for src,g in q.groupby('source_id'):
    # same member across all three experiments, preferring the lowest r/i/p/f
    sets=[set(g[g.experiment_id==e].member_id) for e in ['historical','ssp126','ssp585']]
    common=set.intersection(*sets)
    if not common: continue
    key=lambda m:[int(x) for x in m.replace('r',' ').replace('i',' ').replace('p',' ').replace('f',' ').split()]
    mem=sorted(common,key=key)[0]
    sel=g[g.member_id==mem]
    # one grid only, and one store per experiment (latest version)
    grids=[set(sel[sel.experiment_id==e].grid_label) for e in ['historical','ssp126','ssp585']]
    cg=set.intersection(*grids)
    if not cg: continue
    grid=sorted(cg)[0]
    sel=sel[sel.grid_label==grid].sort_values('version').groupby('experiment_id').tail(1)
    rows.append(dict(source_id=src,institution=sel.institution_id.iloc[0],member=mem,grid=grid,**{e:sel[sel.experiment_id==e].zstore.iloc[0] for e in ['historical','ssp126','ssp585']}))
out=pd.DataFrame(rows)
print(len(out),'models have all three experiments')
print(out[['source_id','institution','member','grid']].to_string())
out.to_csv(ROOT/'data_cache/candidates.csv',index=False)
