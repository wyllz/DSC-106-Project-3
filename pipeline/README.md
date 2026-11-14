# Data pipeline

These scripts turn raw CMIP6 model output into `data/warming.bin` and `data/meta.json`, the files the map loads. They run in order:

| Script | What it does |
|---|---|
| `00_select_models.py` | Picks one model per institution that has monthly `tas` for historical, SSP1-2.6 and SSP5-8.5, using the same run in all three. |
| `01_fetch_cmip6.py` | Streams each run from the public CMIP6 archive on Google Cloud, makes month-length-weighted annual means, and regrids to 2.5 degrees. |
| `02_build_dataset.py` | Converts to warming relative to each model's own 1995-2014 average, takes 20-year averages every 5 years, and writes the ensemble mean and 10th/90th percentiles. |
| `03_exploratory_graphs.py` | Draws the six exploratory graphs from the checkpoint. These use Matplotlib and are not part of the website. |

## Run it

```bash
python -m venv .venv && .venv/bin/pip install -r pipeline/requirements.txt
mkdir -p data_cache && curl -o data_cache/cmip6_catalog.csv https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv
.venv/bin/python pipeline/00_select_models.py
.venv/bin/python pipeline/01_fetch_cmip6.py   # streams about 2 GB
.venv/bin/python pipeline/02_build_dataset.py
```

The page's write-up describes each transformation and its caveats.
