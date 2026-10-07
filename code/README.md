# Code

This folder contains the analysis scripts and notebooks used to produce most figures in the paper. Scripts are standard Python unless noted otherwise.

---

## Tethered-cell pipeline

These scripts process individual tethered-cell videos and aggregate the results.

- **Object-Detection.py** — interactive script; detects the rotating cell body in a single video using multi-Otsu thresholding and fits a circle to the centroid trajectory to find the center of rotation
- **Object-Detection-Loop.py** — batch version of Object-Detection.py; processes a folder of videos unattended
- **Frequency.py** — computes instantaneous rotation frequency from Object-Detection output for a single video; applies a median filter and saves `freq.csv`
- **Frequency-Loop.py** — batch version of Frequency.py
- **tethered-cell-batch.py** — combines object detection and frequency analysis in a single batch run; produces `tethered-cells/results.csv`
- **tethered-cells.ipynb** — filters `results.csv` (size and frequency thresholds) and generates the tethered-cell figures, p-values, ∆s values, and cell counts.

---

## Swimming-cell pipeline

- **Swimming-Tracks.py** — **Fiji/Jython script**; must be run from the Fiji Script Editor, not from the command line; tracks cell trajectories using TrackMate and exports per-cell mean speed CSVs
- **swimming-figures.ipynb** — loads `swimming-cells/` CSVs and generates the swimming-speed figures. Additionally calculates the ∆s values, p-values, and prints cell/replicate counts.

---

## Simulation & theory

- **gillespie.py** — module implementing a Gillespie stochastic simulation and analytic solution for stator binding/unbinding kinetics; imported by the notebooks below
- **gillespie-sim.ipynb** — runs and visualizes stochastic simulation outputs
- **mechanosensing-plots.ipynb** — generates the mechanosensing theory figures using analytical functions from `gillespie.py`
- **swimming-simulation.ipynb** — generates swimming experiment prediction plot

---

## Supplementary

- **track-heatmap.ipynb** — generates trajectory heatmap figures from TrackMate spot exports for figure 2.
- **arabinose-saturation-figure.ipynb** - loads `arabinose-saturation-data.csv` and generates the plot for figure S4. 

