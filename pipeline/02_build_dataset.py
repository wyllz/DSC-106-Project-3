"""Turn the cached annual fields into (a) per-model anomaly cubes for exploration and
(b) the compact binary the D3 page loads.

Method
  anomaly   = each model's temperature minus THAT MODEL's own 1995-2014 mean
  windows   = trailing 20-year means sampled every 5 years. A frame labelled F covers (F-19)..F,
              so 2040/2060/2100 are exactly the IPCC AR6 near/mid/long-term periods.
  ensemble  = unweighted mean of the models, one model per institution
  band      = 10th-90th percentile across models (computed per cell, per frame)
  gap       = SSP5-8.5 minus SSP1-2.6, differenced WITHIN each model before averaging
"""
import json, pathlib, numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[1]
# The site lives in docs/ in the working folder, and directly in project3/ in the published repo.
CACHE = ROOT/'data_cache'/'annual'; SITE = (ROOT/'docs' if (ROOT/'docs').is_dir() else ROOT)/'data'
LAT = np.arange(-88.75, 90, 2.5); LON = np.arange(-178.75, 180, 2.5)
W = np.cos(np.deg2rad(LAT))[None,:,None]; WSUM = W.sum()*LON.size
gm = lambda a: (a*W).sum((-1,-2))/WSUM
FRAMES = list(range(2015, 2101, 5))
BASE = (1995, 2014)

models = sorted({p.name.split('__')[0] for p in CACHE.glob('*.npz')})
models = [m for m in models if all((CACHE/f'{m}__{e}.npz').exists() for e in ('historical','ssp126','ssp585'))]
print(len(models),'models:',', '.join(models))

years = np.arange(1950, 2101)
cube = {e: np.empty((len(models), years.size, LAT.size, LON.size), 'float32') for e in ('ssp126','ssp585')}
abs_base = np.empty((len(models), LAT.size, LON.size), 'float32')
for i,m in enumerate(models):
    h = np.load(CACHE/f'{m}__historical.npz')
    assert h['years'][0]==1950 and h['years'][-1]==2014, m
    base = h['tas'][(h['years']>=BASE[0])&(h['years']<=BASE[1])].mean(0)
    abs_base[i] = base
    for e in cube:
        s = np.load(CACHE/f'{m}__{e}.npz')
        assert s['years'][0]==2015 and s['years'][-1]==2100, (m,e)
        cube[e][i] = np.concatenate([h['tas'], s['tas']])-base
np.savez(ROOT/'data_cache/anomalies.npz', models=np.array(models), years=years, lat=LAT, lon=LON,
         ssp126=cube['ssp126'], ssp585=cube['ssp585'], abs_base=abs_base)

def windows(c):
    out = np.empty((c.shape[0], len(FRAMES), LAT.size, LON.size), 'float32')
    for j,F in enumerate(FRAMES):
        out[:,j] = c[:, (years>=F-19)&(years<=F)].mean(1)
    return out
w126, w585 = windows(cube['ssp126']), windows(cube['ssp585'])
fields = {'ssp126':w126, 'ssp585':w585, 'gap':w585-w126}

blob, summary = [], {}
for name,f in fields.items():
    # Percentiles across models, per cell and per frame
    mean, low, high = f.mean(0), np.percentile(f,10,axis=0), np.percentile(f,90,axis=0)
    for a in (mean,low,high): blob.append(np.round(a*100).astype('<i2'))
    g = gm(f)   # model x frame global means
    summary[name] = dict(mean=np.round(g.mean(0),3).tolist(), low=np.round(np.percentile(g,10,axis=0),3).tolist(),
                         high=np.round(np.percentile(g,90,axis=0),3).tolist())
payload = np.stack(blob)
assert abs(payload).max() < 32000
(SITE/'warming.bin').write_bytes(payload.tobytes())
json.dump(dict(models=models, frames=FRAMES, window=20, baseline=list(BASE), scale=0.01,
               lat={'start':float(LAT[0]),'step':2.5,'n':int(LAT.size)}, lon={'start':float(LON[0]),'step':2.5,'n':int(LON.size)},
               fields=list(fields), stats=['mean','low','high'], band='p10-p90 across models', global_mean=summary),
          open(SITE/'meta.json','w'), indent=1)
print('wrote warming.bin %.2f MB, shape %s'%((SITE/'warming.bin').stat().st_size/1e6, payload.shape))

# Sanity numbers, to compare with published CMIP6 ranges
for n in ('ssp126','ssp585','gap'):
    i = FRAMES.index(2100); print(f"{n:7s} 2081-2100 global: {summary[n]['mean'][i]:.2f} (p10-p90 {summary[n]['low'][i]:.2f} to {summary[n]['high'][i]:.2f})")
print('window label check', FRAMES[0], f'= {FRAMES[0]-19}-{FRAMES[0]}', '| global ssp126 at first frame', summary['ssp126']['mean'][0])
