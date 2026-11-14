"""Stream monthly near-surface air temperature (tas) from the public CMIP6 Zarr stores on
Google Cloud, compute month-length-weighted annual means, regrid every model onto a common
2.5-degree grid (bilinear) and cache one .npz per model/experiment.

Usage: python 01_fetch_cmip6.py [MODEL ...]   (no args = the full ensemble)
"""
import sys, time, pathlib, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np, pandas as pd, xarray as xr, gcsfs

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT/'data_cache'/'annual'; CACHE.mkdir(parents=True, exist_ok=True)

# One model per institution, so no modelling centre gets counted twice.
ENSEMBLE = ['ACCESS-CM2','BCC-CSM2-MR','CESM2-WACCM','CMCC-ESM2','CNRM-CM6-1','CanESM5',
            'EC-Earth3-Veg-LR','FGOALS-g3','GFDL-ESM4','GISS-E2-1-G','INM-CM5-0','IPSL-CM6A-LR',
            'MIROC6','MPI-ESM1-2-LR','MRI-ESM2-0','NorESM2-LM','UKESM1-0-LL','TaiESM1']
PERIODS = {'historical':('1950','2014'), 'ssp126':('2015','2100'), 'ssp585':('2015','2100')}

TGT_LAT = np.arange(-88.75, 90, 2.5)    # 72 rows
TGT_LON = np.arange(-178.75, 180, 2.5)  # 144 columns
gcs = gcsfs.GCSFileSystem(token='anon')

def fetch(model, exp, zstore):
    out = CACHE/f'{model}__{exp}.npz'
    if out.exists(): return f'{model} {exp}: cached'
    t0 = time.time()
    ds = xr.open_zarr(gcs.get_mapper(zstore), consolidated=True, chunks=None,
                      decode_times=xr.coders.CFDatetimeCoder(use_cftime=True))
    ds = ds.rename({k:v for k,v in {'latitude':'lat','longitude':'lon'}.items() if k in ds.variables})
    start, end = PERIODS[exp]
    # A few stores concatenate their 20-year files out of order, so sort before slicing.
    tas = ds['tas'].sortby('time').sel(time=slice(start, end)).squeeze(drop=True)
    assert tas.lat.ndim == 1 and tas.lon.ndim == 1, 'not a rectilinear grid'
    tas = tas.drop_duplicates('time').load()
    nyears, nmonths = int(end)-int(start)+1, tas.sizes['time']
    assert nmonths == 12*nyears, f'expected {12*nyears} months, found {nmonths}'

    w = tas.time.dt.days_in_month
    annual = (tas*w).groupby('time.year').sum('time') / w.groupby('time.year').sum('time')
    annual = annual.assign_coords(lon=((annual.lon+180)%360)-180).sortby('lon').sortby('lat')

    # Native-grid global mean, kept so the regridding can be checked against it later.
    wlat = np.cos(np.deg2rad(annual.lat))
    native_gm = annual.weighted(wlat).mean(('lat','lon')).values

    # Wrap longitude so interpolation is periodic; clamp target lats to the source range so the
    # polar rows use the nearest available row rather than turning into NaN.
    wrapped = xr.concat([annual.isel(lon=-1).assign_coords(lon=annual.lon[-1].item()-360),
                         annual,
                         annual.isel(lon=0).assign_coords(lon=annual.lon[0].item()+360)], dim='lon')
    lat_q = np.clip(TGT_LAT, float(annual.lat.min()), float(annual.lat.max()))
    regridded = wrapped.interp(lat=lat_q, lon=TGT_LON, method='linear').transpose('year','lat','lon')
    data = regridded.values.astype('float32')
    assert np.isfinite(data).all(), 'NaNs after regridding'
    assert 180 < data.min() and data.max() < 340, f'implausible temperatures {data.min()} {data.max()}'
    np.savez_compressed(out, years=annual.year.values, tas=data, native_gm=native_gm.astype('float32'),
                        native_shape=np.array([annual.sizes['lat'], annual.sizes['lon']]))
    return f'{model} {exp}: {nmonths} months, native {annual.sizes["lat"]}x{annual.sizes["lon"]}, {time.time()-t0:.0f}s'

def main(models):
    cat = pd.read_csv(ROOT/'data_cache/candidates.csv').set_index('source_id')
    jobs = [(m,e,cat.loc[m,e]) for m in models for e in PERIODS]
    failures = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch,*j):j for j in jobs}
        for i,f in enumerate(as_completed(futs),1):
            m,e,_ = futs[f]
            try: print(f'[{i}/{len(jobs)}]', f.result(), flush=True)
            except Exception as err:
                failures.append((m,e,repr(err))); print(f'[{i}/{len(jobs)}] FAILED {m} {e}: {err!r}', flush=True)
    print('done. failures:', failures if failures else 'none', flush=True)

if __name__ == '__main__':
    main(sys.argv[1:] or ENSEMBLE)
