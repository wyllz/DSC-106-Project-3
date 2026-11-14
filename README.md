# Where does our emissions choice matter most?

DSC 106 Project 3: an interactive D3 map of CMIP6 climate projections, comparing a low-emissions future (SSP1-2.6) with a high-emissions one (SSP5-8.5).

## Put it online with GitHub Pages

1. Make the repository **public** and put these files at its root, so `index.html` is at the top level.
2. Go to **Settings > Pages**. Under "Build and deployment", choose **Deploy from a branch**, branch **main**, folder **/ (root)**, then **Save**.
3. After a minute or two the site is at `https://<your-username>.github.io/<repo-name>/`.

The page loads its data with `fetch`, so to view it on your own computer, serve the folder rather than opening the file directly:

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000.

## What is here

| Path | What it is |
|---|---|
| `index.html`, `main.js`, `style.css` | The page and its D3 code. |
| `data/` | The prepared model data (`warming.bin`, `meta.json`) and map outlines. |
| `lib/` | D3 v7.9.0 and topojson-client 3.1.0. |
| `pipeline/` | Python scripts that build `data/` from the raw CMIP6 archive. |

