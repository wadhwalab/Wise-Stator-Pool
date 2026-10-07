# Tethered-Cell Rotation Data

This folder contains processed single-motor rotation data from tethered-cell assays. Individual cells were attached to a glass coverslip via flagellar filament stubs, and the rotating cell body was tracked by phase-contrast microscopy at 50 fps. Raw video files are not included in this repository. The data here were produced by the batch analysis script `code/tethered-cell-batch.py`.

All tethered-cell experiments used strain **NW263** (MG1655 Δ*motAB* + pBAD33(*motAB*) + pFD313(*fliC*st)), which carries both the arabinose-inducible stator plasmid and a sticky-flagellin plasmid for surface tethering.

---

## Experimental conditions

| Variable | Levels |
|---|---|
| Arabinose (% w/v) | 0.002, 0.020, 0.200, 2.000 |
| Ficoll 400 (% w/v) | 0, 10, 15 |

---

## results.csv

Each row corresponds to one tracked cell (one source video). There are 965 data rows in total.

**Columns:**

| Column | Description |
|---|---|
| `filename` | Source video filename (see naming convention below) |
| `avg_positive_frequency` | Mean rotation frequency when rotating CCW (Hz). CCW corresponds to the run-promoting direction. |
| `avg_negative_frequency` | Mean rotation frequency when rotating CW (Hz). Values are negative by convention. |
| `percent_time_positive` | Percentage of recording time spent rotating CCW |
| `object_size` | Mean major-axis length of the tracked cell body (pixels) |
| `region_used` | Otsu threshold region selected during image segmentation (integer) |

Rows where `avg_positive_frequency` and related columns are empty indicate videos where tracking failed or the cell was not suitable for analysis (e.g., stopped rotating, object outside the accepted size range). These rows are retained for bookkeeping.

---

## Video filename convention

Filenames encode the experimental condition and source:

```
{batch}{ficoll}F_{arabinose}_{ROI}_{particle_id}.avi
```

**`{batch}`** — biological replicate batch:

| Prefix | Batch |
|---|---|
| *(none)* | First biological replicate |
| `a` | Second biological replicate |
| `b` | Third biological replicate |

**`{ficoll}F`** — Ficoll 400 concentration:
- `0F` = 0% Ficoll (motility buffer only)
- `10F` = 10% Ficoll
- `15F` = 15% Ficoll

**`{arabinose}`** — arabinose concentration code. The exponent indicates how many decades below 2% the concentration is:

| Code | Arabinose (% w/v) |
|---|---|
| `2e0` | 2.000 |
| `2e1` | 0.200 |
| `2e2` | 0.020 |
| `2e3` | 0.002 |

**`{ROI}`** — field of view within the slide (e.g., `ROI1` through `ROI5`). Multiple fields were imaged per slide to reduce sampling bias.

**`{particle_id}`** — unique integer assigned to the cell by the TrackMate tracking step.

**Examples:**
- `0F_2e2_ROI3_particle_250.avi` — first replicate, 0% Ficoll, 0.020% arabinose, field 3, particle 250
- `b10F_2e1_ROI1_particle_22.avi` — third replicate, 10% Ficoll, 0.200% arabinose, field 1, particle 22

**Note on `_1` suffix:** A small number of filenames end in `_1` (e.g., `0F_2e3_ROI1_particle_126_1.avi`). These are duplicate analysis entries for the same video and have identical values to the unsuffixed row. These duplicates are removed in the final analysis.
