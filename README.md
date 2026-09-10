# MPLADS Monitoring Prototype

AI-assisted monitoring for MPLADS works (SIH 2026). The pipeline flags delay, stalled works, cost outliers, and similar/duplicate descriptions so a reviewer can check them. **Flags are not confirmed fraud.**

## What runs where

| Stage | Module | Output |
| --- | --- | --- |
| M1 preprocessing | `src/preprocessing/datapreprocessing.py` | `data/cleaned/master_projects.csv` |
| M2 cost anomaly + duplicates | `src/ml/` | `data/processed/m2_ml_outputs.csv` |
| M3 rules / risk score | `src/rules/rule_engine.py` | `data/cleaned/risk_output.csv` |
| M4 API | `src/api/` | FastAPI on port 8000 |

Do not use `notebooks/rule.py`, `notebooks/rule1.py`, or `archive/` for scoring. Live M3 is `src/rules/rule_engine.py` (teammate engine, with path and awaiting-sanction fixes).

Raw portal extracts live in `dataset/`. `data/cleaned/` is gitignored; generate it locally with M1.

## Setup

From the project root, with Python 3.11+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to run

All commands below are from the **project root**.

### 1. Build the master table (M1)

```powershell
python -m src.preprocessing.datapreprocessing
```

### 2. Run ML detectors and merge (M2)

```powershell
python -m src.ml.run_cost_anomaly
python -m src.ml.run_duplicate_detection
python -m src.ml.merge_m2_outputs
```

### 3. Score risk (M3)

```powershell
python -m src.rules.rule_engine
```

### Combined pipeline

Rebuild everything:

```powershell
python src/run_pipeline.py --with-m1
```

Reuse existing M2 CSVs and only re-run M3:

```powershell
python src/run_pipeline.py --skip-ml
```

### 4. Start the API (M4)

```powershell
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

Useful endpoints: `/filters`, `/risk-summary`, `/projects`, `/alerts`, `/projects/{project_id}`, `/risk-score/{project_id}`, `POST /analyze`.

`POST /analyze?reload_only=true` reloads CSVs already on disk. Set `reload_only=false` only if you want the server to re-run M3 first.

Allowed `alert_type` values: `delay`, `stalled`, `pending_mark`, `sanction_delay`, `over_expenditure`, `invalid_date`, `status_mismatch`, `low_amount`, `cost_anomaly`, `exact_duplicate`, `potential_duplicate`. There is no `fraud` type.

### Tests

```powershell
python -m pytest src/tests -q
```

## Notes

- Join key is the MPLADS work id (`WS/MPxxxx/YYYY-YYYY/nnnnnn`). Peer groups use `work_type`, not coarse `work_category`.
- Delay uses sanction date plus 365 days (guideline). Sanction lag uses 45 days. Low-amount uses Rs 2.5 lakh.
- Exact duplicate wording in the same constituency is common; it is a review signal, not proof of double billing.
