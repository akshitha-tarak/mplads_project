# Anomaly Detection Module

## Overview

This module identifies potentially suspicious MPLADS projects using multiple anomaly detection techniques and combines the results into a final ML risk score.

---

# Input File Used

Primary dataset:

```text
data/cleaned/master_projects_features.csv
```

This dataset contains engineered project-level features created from:

- Works Sanctioned
- Works Completed
- Expenditure on Completed and On-going Works
- Works Recommended

---

# Features Used

The following features are used for anomaly detection:

| Feature | Description |
|----------|-------------|
| fund_utilization | Amount disbursed / sanctioned amount |
| expenditure_ratio | Total expenditure / sanctioned amount |
| payment_count | Number of expenditure transactions |
| project_age_days | Days since project sanction |
| over_budget | 1 if expenditure exceeds sanctioned amount, else 0 |

---

# Isolation Forest

## Purpose

Detect unusual project spending patterns that differ from normal projects.

## Model

```python
IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)
```

## Parameters

| Parameter | Value |
|------------|---------|
| n_estimators | 100 |
| contamination | 0.05 |
| random_state | 42 |

## Output

| Value | Meaning |
|---------|----------|
| -1 | Anomaly |
| 1 | Normal |

Generated Columns:

- anomaly_prediction
- cost_anomaly_flag
- anomaly_score
- anomaly_reason

---

# Z-Score Detection

## Purpose

Detect projects with unusually high expenditure.

## Formula

\[
Z = \frac{X - \mu}{\sigma}
\]

Where:

- X = project expenditure
- μ = mean expenditure
- σ = standard deviation

## Threshold

```text
Z-Score > 3
```

Projects above this threshold are flagged as anomalies.

---

# IQR Detection

## Purpose

Detect expenditure outliers using quartiles.

## Formula

```text
IQR = Q3 - Q1
```

```text
Upper Bound = Q3 + (1.5 × IQR)
```

Projects above the upper bound are flagged as anomalies.

---

# Duplicate Detection

## Purpose

Detect potentially duplicated project descriptions.

## Method

1. Text cleaning
2. TF-IDF vectorization
3. Cosine similarity calculation

## Grouping

Projects are compared only within:

- State
- Constituency
- Work Category

## Similarity Threshold

```text
Cosine Similarity ≥ 0.95
```

Projects above this threshold are considered potential duplicates.

---

# ML Risk Score

The final risk score combines all anomaly detection methods.

## Formula

```text
ML Risk Score =
(Isolation Forest × 40)
+ (Z-Score × 25)
+ (IQR × 20)
+ (Duplicate Detection × 15)
```

Maximum score:

```text
100
```

---

# Risk Levels

| Score Range | Risk Level |
|-------------|------------|
| 0 | Normal |
| 1 – 19 | Low |
| 20 – 49 | Medium |
| 50 – 79 | High |
| 80 – 100 | Critical |

---

# Output Files

Generated outputs:

```text
src/anomaly_detection/outputs/
```

Files:

- isolation_forest_results.csv
- zscore_results.csv
- iqr_results.csv
- duplicate_detection_optimized.csv
- final_ml_output.csv

---

# Project Statistics

| Metric | Value |
|---------|---------|
| Projects Analysed | 507 |
| Isolation Forest Anomalies | 26 |
| Z-Score Anomalies | 8 |
| IQR Anomalies | 30 |
| Potential Duplicate Projects | 995 |
| Critical Risk Projects | 1 |
| High Risk Projects | 3 |

---

# Author

Smart India Hackathon (SIH) Project  
MPLADS Fraud Detection & Monitoring System