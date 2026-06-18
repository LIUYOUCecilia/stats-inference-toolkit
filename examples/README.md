# Examples

Optional larger-data examples live here so the project root stays focused on the main Streamlit app, CLI pipeline, and sample report generator.

## Udacity-Style A/B Test Example

```bash
python examples/udacity_ab_test.py
```

This example uses `examples/ab_data.csv` when present. If the file is missing, the script attempts to download a public A/B testing dataset and falls back to simulated data when offline.

The generated PDF is written to:

```text
ab_test_report.pdf
```
