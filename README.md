# Groundwater Potential Index (GPI)

## A Physics-Informed Meteorology-Driven Proxy for Aquifer Recharge Dynamics

This repository contains the source code, configuration files, environmental data, and reproducibility material associated with the study:

> **The Groundwater Potential Index: A Physics-Informed Meteorology-Driven Proxy for Aquifer Recharge Dynamics**

The **Groundwater Potential Index (GPI)** is a standardized, meteorology-driven proxy designed to characterize temporal variations in effective recharge and their relationship with groundwater-level observations.

The method combines daily precipitation and potential evapotranspiration with two physically interpretable parameters:

* the **hydrological memory window** \(N\), which represents the period over which antecedent effective recharge is accumulated; and
* the **groundwater response lag** \(L\), which represents the delay between meteorological recharge forcing and the observed groundwater response.

Groundwater-level observations are used during calibration to identify the optimal (N*, L*) configuration. Once calibrated, the GPI can be computed from precipitation and potential evapotranspiration without requiring continuous groundwater-level observations.

The repository is designed to reproduce the computational analysis using the environmental data files supplied with the repository. 

## Overview

Groundwater monitoring relies on costly, sparse piezometric networks. The
Groundwater Potential Index (GPI) is a physics-informed, meteorology-driven
proxy for aquifer recharge dynamics, built from rainfall and potential
evapotranspiration alone. It combines two physically interpretable,
site-calibrated parameters:

- **Hydrological memory (N)**: the length, in months, of the trailing
  window over which effective recharge is integrated.
- **Geological lag (L)**: the delay, in months, between a recharge signal
  and its expression in the observed groundwater level.


The computational steps are:

1. Load and clean local rainfall and groundwater-level observations
   (`src/preprocess_data.py`).
2. Build a daily potential-evapotranspiration series from a monthly
   climatology (`src/pet.py`).
3. Compute the effective recharge balance, `Reff = max(0, P - Kc*PET)`
   (`src/effective_recharge.py`).
4. Integrate `Reff` over a hydrological-memory window and standardize it
   into a dimensionless GPI (`src/gpi.py`).
5. Align the GPI with the groundwater level at lag L and run the (N, L)
   sweep (`src/calibration.py`).

## Repository structure

```
groundwater-potential-index/
├── README.md
├── CITATION.cff
├── requirements.txt /
│   ├──requirements-dev.txt / 
├── pyproject.toml            
├── .gitignore
│
├── config/
│   ├── stations.yaml   
│   └── parameters.yaml      
│
├── data/
│   ├── README.md              
│   ├── checksums.sha256
│   ├── Chilgrove/
│   ├──Kemps/
│   ├──Roman road/
│   ├──Hyde/   
│   ├── HadEWP_daily_totals/     
│   └── station_pet_averages.csv 
│
├── src/
│   ├── preprocess_data.py   
│   ├── pet.py                 
│   ├── effective_recharge.py  
│   ├── gpi.py               
│   ├── calibration.py         
│   ├── pipeline.py            
│   ├── visualization.py     
│   └── utils.py              
│
├── scripts/
│   ├── run_calibration.py        
│   ├── generate_figures.py        
│   └── run_sensitivity_analysis.py 
│
├── notebooks/
│   └── GPI.ipynb              
│
├── results/                  
├── figures/                   
└── tests/                    
```


## Requirements

- Python 3.12 (the pinned dependency versions in `requirements.txt` target
  this version; see `environment.yml` for a matching Conda environment).
- No GPU or non-Python system dependency is required.

## Installation

```bash
git clone <this-repository>
cd groundwater-potential-index
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Or, with Conda:

```bash
conda env create -f environment.yml
conda activate gpi
```

For running the test suite, also install `requirements-dev.txt`
(`pip install -r requirements-dev.txt`).

## Dataset

The four stations' raw rainfall and groundwater-level series, the HadEWP
regional precipitation series, and the PET climatology table are included
under `data/` (see `data/README.md` for the full inventory, provenance, and
known characteristics of these files). 

## Configuration

All methodological parameters live in `config/parameters.yaml` (Kc, the N
and L candidate sets, the minimum-valid-data-fraction threshold), and all
station metadata (coordinates, file paths, native resolution, PET
overrides) lives in `config/stations.yaml`.

## Running the experiments

```bash
python scripts/run_calibration.py          
python scripts/generate_figures.py        
python scripts/run_sensitivity_analysis.py 
```

Each script can also be run from `notebooks/GPI.ipynb`, which walks through
the same steps interactively.

## Evaluation

For each station, the pipeline reports the full 18-configuration (N, L)
Pearson-correlation sweep (`results/calibration_long_<station_id>.csv`) and
the optimal configuration.

## Results

Running `scripts/run_calibration.py` writes `results/calibration_optimal.csv`
(one row per station: N\*, L\*, r\*, n_obs) and one
`results/calibration_long_<station_id>.csv` per station. Running
`scripts/generate_figures.py` and `scripts/run_sensitivity_analysis.py`
writes the corresponding figures to `figures/`. These outputs are not
committed to version control (they are fully reproducible from `data/` and
`config/`); see `results/README.md` and `figures/README.md`.

## Reproducibility notes

For reproducibility:

* use the repository version associated with the study;
* preserve the supplied files under `data/` without modification;
* use the configuration files under `config/`;
* use the dependency versions specified by the repository;

## Authors

**Dorsaf Sebai**
Conceptualization, methodology, scientific analysis, supervision, validation, writing

**Manel Zouaoui**
Methodology, data processing, implementation, analysis, validation, visualization


## Contact

For questions concerning the methodology, implementation, data processing, or reproducibility of this repository, please use the repository issue tracker or contact the corresponding author identified in the associated publication.
