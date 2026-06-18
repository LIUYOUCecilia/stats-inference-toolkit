# Automated A/B Testing & Statistical Reports - Python Toolkit

Upload CSV -> auto assumption checks -> correct test selected -> client-ready PDF in seconds.

This toolkit helps marketers, product managers, researchers, and small business owners turn experiment data into a clear statistical decision. It supports conversion rates, revenue, survey responses, and categorical outcomes.

## Live Demo & Samples

| Resource | Link |
| --- | --- |
| Live Streamlit Demo | Deploy from this repo with `app.py` as the Streamlit entry point |
| Sample PDF Report | [`ab_test_report.pdf`](ab_test_report.pdf) |
| Sample Reports Folder | [`reports/`](reports/) |
| Fiverr Gig Copy | [`FIVERR_GIG.md`](FIVERR_GIG.md) |
| Order on Fiverr | Coming soon |

> Portfolio demo. This toolkit analyzes your CSV data: conversion rates, revenue, survey responses, or experimental metrics. Sample datasets are included; no real client data is required to evaluate the workflow.

## What It Does

- Upload a CSV or run one of the included demo datasets.
- Check assumptions with Shapiro-Wilk normality and Levene variance tests.
- Route automatically to Z-test, Student's t-test, Welch's t-test, Mann-Whitney U, One-way ANOVA, or Chi-Square.
- Generate a PDF report using an AP Statistics State-Plan-Do-Conclude framework.
- Show p-values, confidence intervals, effect sizes, visual comparisons, data diagnostics, and a plain-English conclusion.
- Include PDF visual summaries for conversion rates, numeric metrics, medians, and categorical distributions.
- Customize PDF cover metadata with client/project name and prepared-by fields.
- Choose the report audience: Fiverr buyer, small business / marketer, or researcher / PhD.

## Quick Start

### 1. Install

```bash
git clone https://github.com/LIUYOUCecilia/stats-inference-toolkit.git
cd stats-inference-toolkit
pip install -r requirements.txt
```

### 2. Launch The Streamlit Demo

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

### 3. Deploy To Streamlit Cloud

Use these settings on Streamlit Cloud:

```text
Repository: LIUYOUCecilia/stats-inference-toolkit
Branch: main
Main file path: app.py
Python version: 3.11 or 3.12
Dependencies: requirements.txt
```

After deployment, replace the Live Demo row above with the Streamlit URL.

### 4. Run CLI Examples

Conversion rate A/B test:

```bash
python stats_inference_toolkit.py \
  --data demo_data/conversion_data.csv \
  --group-col group \
  --value-col converted \
  --client-name "Acme Landing Page Test" \
  --prepared-by "Tianyou Liu - Statistical Analysis" \
  --audience small_business \
  --output reports/conversion_report.pdf
```

Revenue A/B test:

```bash
python stats_inference_toolkit.py \
  --data demo_data/revenue_data.csv \
  --group-col group \
  --value-col revenue \
  --output reports/revenue_report.pdf
```

Run all demo scenarios:

```bash
python run_demo.py
```

## Included Demo Reports

| Report | Scenario | Test Route |
| --- | --- | --- |
| [`reports/conversion_z_report.pdf`](reports/conversion_z_report.pdf) | Binary conversion data | Two-sample Z-test |
| [`reports/revenue_t_report.pdf`](reports/revenue_t_report.pdf) | Continuous revenue data | T-test / Welch route |
| [`reports/session_nonparametric_report.pdf`](reports/session_nonparametric_report.pdf) | Non-normal session data | Mann-Whitney U |
| [`reports/feedback_chisquare_report.pdf`](reports/feedback_chisquare_report.pdf) | Categorical feedback data | Chi-Square |

## Streamlit App Workflow

```text
Open app -> choose sample data or upload CSV -> select group/value columns
-> run analysis -> read result -> download PDF report
```

The app is intentionally simple for portfolio review: clients can see the statistical workflow without installing Python or reading code.

The live app includes:

- Sample dataset picker for conversion, revenue, session duration, and categorical feedback examples.
- CSV upload with group/value column selectors.
- Data diagnostics for row count, usable rows, group count, missing values, duplicate ID warnings, and detected outcome type.
- 3+ group support for numeric ANOVA and multi-group Chi-Square.
- Plotly visualizations: conversion rate bars with 95% CI, numeric boxplots, and categorical percentage stacked bars.
- PDF report download after each analysis.
- Custom client/project name and prepared-by fields on the PDF cover.
- Audience-specific PDF output:
  - `fiverr_buyer`: shortest buyer-facing summary, designed for quick trust and conversion.
  - `small_business`: rollout recommendation report for marketers and business owners.
  - `researcher`: full State-Plan-Do-Conclude methodology for researchers and PhD-style review.

## Entry Points

Use these three files for normal review and deployment:

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit web demo and portfolio entry point |
| `stats_inference_toolkit.py` | Main command-line analysis pipeline |
| `run_demo.py` | Regenerates all four sample datasets and PDF reports |

Historical or larger-data examples live in [`examples/`](examples/) so the root directory stays focused.

## Recommended Fiverr Positioning

Suggested Gig title:

```text
I will analyze your A/B test data and deliver a statistical PDF report in Python
```

Suggested Gig structure:

- Problem: Not sure whether your A/B test result is real or random noise?
- Solution: I run assumption checks, select the correct statistical test, and generate a PDF report.
- Proof: Live demo, sample PDF reports, and full source code.

## Project Structure

```text
app.py                       Streamlit live demo
stats_inference_toolkit.py   Main CLI and pipeline orchestration
ab_testers.py                Statistical test implementations
assumptions_checker.py       Normality and variance checks
pdf_generator.py             PDF report generation
run_demo.py                  Generates all sample reports
demo_data/                   Included sample CSV files
reports/                     Included sample PDF outputs
examples/                    Optional larger-data examples
```

## Requirements

Main libraries:

- pandas
- numpy
- scipy
- matplotlib
- reportlab
- statsmodels
- pillow
- streamlit
- plotly

Licensed under MIT. Free to inspect code quality.
