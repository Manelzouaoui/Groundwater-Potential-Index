# Data documentation

This directory contains the raw environmental data used to compute the
Groundwater Potential Index (GPI) for the four monitoring stations analyzed
in the paper. All files are exports from the UK Environment Agency (EA)
Hydrology API and EA Flood Monitoring API, plus one national precipitation
series (HadEWP). 


## Layout and file inventory

| File (under `data/`) | Content | Rows | Period | Native resolution | SHA-256 (first 16) |
|---|---|---:|---|---|---|
| `Chilgrove/Piézométrie/Chilgrove-House-level-15min-Qualified.csv` | groundwater level, mAOD | 81,696 | 2024-01-01 → 2026-04-30 | 15 min | `29c5f0d16b1d68fc` |
| `Chilgrove/Rainfall/Chilgrove-House-rainfall-daily-Qualified.csv` | daily rainfall total, mm | 9,709 | 1999-10-01 → 2026-04-30 | daily (stamped 09:00) | `18815cf552ca7203` |
| `Hyde/Piézométrie/ea15dfcd-00b7-41d9-91b6-c4fc325d9cb8-gw-dipped-i-mAOD-qualified.csv` | groundwater level, mAOD | 561 | 1967-11-23 → 2026-04-10 | irregular (manual dips) | `4b83558360ac10e8` |
| `Hyde/Rainfall/Mildenhall-rainfall-daily-Qualified.csv` | daily rainfall total, mm | 11,047 | 1996-02-01 → 2026-04-30 | daily (stamped 09:00) | `24f197111c921737` |
| `Kemps/Piézométrie/9610f73b-f3af-4ede-b4e7-ec615e7ab5a2-gw-dipped-i-mAOD-qualified.csv` | groundwater level, mAOD | 366 | 1992-07-20 → 2025-05-29 | irregular (manual dips) | `89c8ff8aa2f9df59` |
| `Kemps/Rainfall/Lower-Dunsforth-rainfall-daily-Qualified.csv` | daily rainfall total, mm | 14,943 | 1985-06-02 → 2026-04-30 | daily (stamped 09:00) | `b0017aa2d9bc5299` |
| `Roman road/Piézométrie/Roman-Road-level-15min-Qualified.csv` | groundwater level, mAOD | 20,003 | 2024-01-01 → 2026-04-13 | 1 h (observed in delivered file) | `212bd04ffeba6f31` |
| `Roman road/Rainfall/Broomy-Hill-rainfall-daily-Qualified.csv` | daily rainfall total, mm | 12,058 | 1993-04-26 → 2026-04-30 | daily (stamped 09:00) | `06d1dc9bd9370b2c` |
| `station_pet_averages.csv` | mean daily PET per station and month | 41,508 | n/a (climatology) | 12 monthly values / station | `a8f64014b05c78fe` |
| `HadEWP_daily_totals/HadEWP_daily_totals.txt` | daily England & Wales precipitation, mm | 34,905 | 1931-01-01 → 2026-07-25 | daily | `bdbcb8cca7bdeacd` |

Each station folder also contains one `.txt` or `.json` metadata file per
series (borehole depth, datum, opening date, station coordinates, etc.),
as exported directly from the EA APIs. `config/stations.yaml` extracts the
fields actually used by the pipeline from these metadata files.

Row counts and date ranges above were verified directly against the files
in this delivery (`data/checksums.sha256` records the SHA-256 of every
file).

## Groundwater levels

| Station | Measure type | Native resolution in delivered file | Readings in analysis window | Days with a reading |
|---|---|---:|---:|---:|
| Chilgrove House | Logger (`gw-logged`) | 15 min | 81,696 | 851 |
| Hyde Cottages Risby | Manual dips (`gw-dipped`) | Irregular | 26 | 26 |
| Kemps Drift | Manual dips (`gw-dipped`) | Irregular | 17 | 17 |
| Roman Road | Logger (`gw-logged`) | 1 h (observed in delivered file) | 20,003 | 834 |


### Data-quality and temporal-resolution notes

**Roman Road temporal resolution:** The file `Roman-Road-level-15min-Qualified.csv` is named as a 15-minute series, and the available metadata specifies a 900-second period. However, inspection of the delivered observations shows an hourly temporal spacing: all consecutive observations in the delivered file are separated by one hour. The analysis therefore uses the observations as provided, without resampling or interpolation.

**Sparse manual observations:** Hyde Cottages Risby and Kemps Drift contain only 26 and 17 groundwater observations, respectively, within the configured analysis window. 

**Quality flags:** Within the configured analysis window, the delivered groundwater records contain:

* Chilgrove House: 81,696 `Good` observations;
* Hyde Cottages Risby: 24 `Good` and 2 `Unchecked` observations;
* Kemps Drift: 17 `Good` observations;
* Roman Road: 20,003 `Good` observations.

## Local precipitation

Local precipitation data are obtained from rainfall gauges associated with the four groundwater monitoring stations. The delivered files contain daily rainfall totals from the Environment Agency Hydrology data service. The Environment Agency describes its Hydrology service as a source of historical quality-checked and qualified hydrological data.

| Field               | Description                                                                                                                                                                        |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Provider            | UK Environment Agency                                                                                                                                                              |
| Data resource       | Environment Agency Hydrology API                                                                                                                                                   |
| Measurement type    | Daily rainfall total (`rainfall-t-86400-mm-qualified`)                                                                                                                             |
| Variable / unit     | Rainfall total, mm                                                                                                                                                                 |
| Temporal resolution | Daily (24-hour total)                                                                                                                                                              |
| Time convention     | Observations are timestamped at 09:00; the delivered files do not explicitly specify whether this timestamp represents the beginning or the end of the 24-hour accumulation period |
| Quality information | `completeness` and `quality` fields                                                                                                                                              |

The rainfall records supplied with the repository are already provided as daily totals. The analysis therefore does not perform any additional sub-daily rainfall aggregation. The `date` field is used as the daily observation label.

Missing observations are identified by the `Missing` quality flag and, in the delivered files, correspond to missing values in the `value` field. 

Across the complete rainfall records, the number of observations flagged as `Missing` is:

| Station             | Missing observations |
| ------------------- | -------------------: |
| Chilgrove House     |                  180 |
| Hyde Cottages Risby |                  280 |
| Kemps Drift         |                  176 |
| Roman Road          |                  287 |

No rainfall observations are flagged as `Missing` from 2023-01-01 onward in the supplied files. Consequently, there are no `Missing` quality-flagged rainfall observations during the configured groundwater analysis period.

The quality flags observed from 2023-01-01 onward are summarized below:

| Station             |  Good | Unchecked | Suspect |
| ------------------- | ----: | --------: | ------: |
| Chilgrove House     |   549 |       667 |       0 |
| Hyde Cottages Risby |   992 |        12 |     212 |
| Kemps Drift         |   611 |       324 |     281 |
| Roman Road          | 1,072 |         1 |     143 |

The quality categories are retained as provided by the Environment Agency. The Environment Agency defines `Good` as data that have been manually inspected with no obvious or known data issues, `Unchecked` as raw input data that have not been manually inspected, `Suspect` as data considered inaccurate when no correction can be made, and `Missing` as data that have been deleted or did not arrive in the archive.

## Potential evapotranspiration (PET)

Potential evapotranspiration data used in the repository are provided in `data/station_pet_averages.csv`.

| Field                        | Description                                      |
| ---------------------------- | ------------------------------------------------ |
| File                         | `data/station_pet_averages.csv`                  |
| Columns                      | `stationReference`, `month`, `avg_daily_pet`     |
| Temporal representation      | Monthly values for each station reference        |
| Number of station references | 3,452                                            |
| Unit                         | mm day⁻¹                                         |
| Role                         | Input used to estimate actual evapotranspiration |

The file contains 41,508 rows and does not contain daily dates or geographic coordinates. The `month` field provides the monthly temporal representation of the PET values.

Seven station references (`4063TH`, `4171TH`, `E2900`, `E6120`, `E70139`, `E73439`, and `E73639`) contain duplicate records for some months. These duplicate records account for 84 additional rows in the file and are averaged during preprocessing.

Actual evapotranspiration is estimated using:

```text
AET(t) = Kc × PET(t)
```

with `Kc = 0.5`, as specified in the GPI implementation.

The PET value corresponding to each calendar month is assigned to the days of that month to construct the daily PET values used by the GPI computation.

## Regional precipitation (HadEWP)

Regional precipitation is provided through the HadEWP daily England and Wales precipitation series.

| Field               | Description                                                                 |
| ------------------- | --------------------------------------------------------------------------- |
| File                | `data/HadEWP_daily_totals/HadEWP_daily_totals.txt`                          |
| Dataset             | HadEWP / HadUKP daily England and Wales precipitation series                |
| Variable / unit     | Daily precipitation total, mm day⁻¹                                         |
| Temporal resolution | Daily                                                                       |
| Available period    | 1931-01-01 to 2026-07-25                                                    |
| Number of records   | 34,905                                                                      |

The delivered file contains a textual header followed by a whitespace-separated table with `Date` and `Value` fields. The file contains daily England and Wales precipitation observations.

The Met Office identifies HadUKP as the UK regional precipitation dataset and states that the HadEWP series provides England and Wales precipitation totals. The daily HadUKP series begins in 1931. Recent values can be revised as part of the quality-control process.

## Rainfall gauges

The rainfall gauges used in the analysis are listed below. The table provides the gauge reference, geographic coordinates, grid reference, EA station identifier, and time-series measure identifier.

| Gauge           | EA reference |  Latitude | Longitude | Grid reference | EA station GUID                        | Time-series measure ID                                               |
| --------------- | ------------ | --------: | --------: | -------------- | -------------------------------------- | -------------------------------------------------------------------- |
| Chilgrove House | E11191       | 50.922660 | -0.813097 | SU8352014360   | `3a00d049-d6fa-4f73-aa3c-b521454ee422` | `3a00d049-d6fa-4f73-aa3c-b521454ee422-rainfall-t-86400-mm-qualified` |
| Mildenhall      | E24591       | 52.345447 |  0.484290 | TL6932074836   | `9b495091-97a1-42b4-9b04-f4eff295cd5d` | `9b495091-97a1-42b4-9b04-f4eff295cd5d-rainfall-t-86400-mm-qualified` |
| Lower Dunsforth | 056505       | 54.072851 | -1.336780 | SE4349664307   | `127f4da7-2dab-4e69-b7cf-f1a6de03837a` | `127f4da7-2dab-4e69-b7cf-f1a6de03837a-rainfall-t-86400-mm-qualified` |
| Broomy Hill     | 1602         | 52.053059 | -2.736469 | SO4959639665   | `9153f95f-8402-4c9a-ae03-fe03dec1ee31` | `9153f95f-8402-4c9a-ae03-fe03dec1ee31-rainfall-t-86400-mm-qualified` |

## Observation period

The four groundwater records do not cover the same observation period:

| Station             | First                   | Last                   | 
| ------------------- | ----------------------- | ---------------------- | 
| Chilgrove House     | 2024-01-01              | 2026-04-10             |                
| Hyde Cottages Risby | 2024-01-01              | 2026-04-10             |              
| Kemps Drift         | 2024-01-01              | 2025-05-29             |             
| Roman Road          | 2024-01-01              | 2026-04-10             |     

## File formats

The repository uses the following file formats:

* **Groundwater and rainfall data:** CSV files provided by the Environment Agency, using comma-separated fields and UTF-8 encoding. The exported files contain measurement metadata and observation values.
* **Station-level PET data:** `station_pet_averages.csv`, stored as a comma-delimited CSV file with decimal values.
* **Regional precipitation:** `HadEWP_daily_totals.txt`, stored as a text file with a header followed by whitespace-delimited daily observations.
* **Generated data products:** UTF-8 CSV files with comma-separated fields, ISO 8601 dates, decimal values, and empty fields for missing observations.
* **Configuration files:** YAML files stored under `config/`, including `stations.yaml` and `parameters.yaml`, where applicable.
* **Metadata and audit files:** CSV, Markdown, JSON, or other formats corresponding to the source metadata and validation procedures.



