# Swimming-Cell Speed Data

This folder contains processed swimming-speed data from free-swimming *E. coli* cells imaged by phase-contrast microscopy. Raw video files are not included in this repository, but are available on Zenodo. The CSVs here are outputs of particle-tracking analysis using a custom Fiji/TrackMate script (`code/Swimming-Tracks.py`) and downstream Python processing.

---

## Strains

| Code | Strain | Description |
|---|---|---|
| `D` | NW166 | MG1655 Δ*motAB* + pBAD33(*motAB*). Stator expression is induced by arabinose. |
| `W` | MG1655 | Wild-type *E. coli*. Swimming speed is approximately independent of arabinose. |

---

## Experimental conditions

| Variable | Levels |
|---|---|
| Arabinose (% w/v) | 0.002, 0.020, 0.200, 2.000 (plus a 0.000% uninduced control for strain D) |
| Ficoll 400 (% w/v) | 0, 10, 15 |

Ficoll 400 was added to motility buffer as a viscous agent to increase flagellar motor load.

---

## Folder structure

```
swimming-cells/
├── NormalMB/       # Strain D (NW166), 0% Ficoll — 5 biological replicates
│   ├── V/
│   ├── W/
│   ├── X/
│   ├── Y/
│   └── Z/
├── NormalMB-WT/    # Strain W (MG1655), 0% Ficoll — 5 biological replicates
│   ├── WV/
│   ├── WW/
│   ├── WX/
│   ├── WY/
│   └── WZ/
├── 10/             # 10% Ficoll — 3 biological replicates; contains both D and W files
│   ├── Q/
│   ├── S/
│   └── T/
├── 15/             # 15% Ficoll — 3 biological replicates; contains both D and W files
│   ├── P/
│   ├── R/
│   └── U/
└── All_Data.csv    # Cross-condition summary (see below)
```

Each replicate subfolder contains one CSV per arabinose condition and a `master.csv` pooling all conditions for that replicate.

---

## Individual condition CSVs

**Filename format:** `{strain}_{arabinose}_{replicate}_{index}.csv`

- `D_0.020_V_0.csv` — strain D, 0.020% arabinose, replicate V
- `W_0.200_Q_0.csv` — strain W, 0.200% arabinose, replicate Q

When more than one video was recorded for the same condition and replicate, the index increments (e.g., `D_0.200_V_1.csv`).

**Columns:**

| Column | Description |
|---|---|
| *(unnamed)* | Row index |
| `0` | Mean swimming speed of one tracked cell trajectory (µm/s) |
| `strain` | Strain code (`D` or `W`) |
| `replicate` | Biological replicate letter |
| `concentration` | Arabinose concentration (% w/v, numeric) |

One row = one tracked cell.

---

## master.csv (per replicate folder)

Pools all arabinose conditions for one replicate. Columns are identical to the individual CSVs. This file is the direct input to the analysis notebooks.

---

## All_Data.csv

A condition-level summary. Each non-`AVG` row is the mean speed for one (strain, arabinose, Ficoll, replicate) combination. Blank rows are left in this file to allow for ease of reading.

**Columns:**

| Column | Description |
|---|---|
| `Strain` | `D` (NW166) or `W` (MG1655) |
| `Average Speed (µm/s)` | Mean speed across all tracked cells, including slow/non-motile cells |
| `Arabinose Conc` | Arabinose concentration as a percentage string |
| `Replicate` | Replicate letter, or `AVG` for the cross-replicate mean |
| `Ficoll` | Ficoll 400 concentration (% w/v): 0, 10, or 15 |
| `Filtered` | Mean speed after excluding cells ≤ 4 µm/s. The 4 µm/s cutoff is the Brownian-motion speed of non-motile Δ*motAB* cells and is the primary metric used in the paper's figures. |

**Notes on contents:**

- `AVG` rows are means across biological replicates and are not independent observations.
- Arabinose concentrations use a shortened display format in this file: `0.00%` = 0.002% w/v, `0.02%` = 0.020%, `0.20%` = 0.200%, `2%` = 2.000%.
- For strain D at Ficoll = 0, a separate block of rows labeled `0.00%` arabinose with speeds ~4 µm/s represents the truly uninduced control (0.000% arabinose). These rows have no `Filtered` value and are not part of the main arabinose-dose series.
- Wild-type (W) data at 10% and 15% Ficoll are present as individual CSVs in the `10/` and `15/` folders (files starting with `W_`) but are not included in `All_Data.csv`. They correspond to the WT control panels in the supplementary figures.
