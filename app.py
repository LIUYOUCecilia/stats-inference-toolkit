# -*- coding: utf-8 -*-
"""
Streamlit demo for the Stats Inference Toolkit.
"""
import os
import tempfile

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from stats_inference_toolkit import run_pipeline


SAMPLE_DATASETS = {
    "[Business] Client-style campaign data": "demo_data/client_style_campaign_data.csv",
    "[Business] Conversion A/B test": "demo_data/conversion_data.csv",
    "[Business] Revenue A/B test": "demo_data/revenue_data.csv",
    "[Business] Session duration non-parametric": "demo_data/session_data.csv",
    "[Business] Feedback Chi-Square": "demo_data/feedback_data.csv",
    "[Lab] Biology - cell viability": "demo_data/biology_cell_viability.csv",
    "[Lab] Biology - enzyme activity ANOVA": "demo_data/biology_enzyme_anova.csv",
    "[Lab] Chemistry - reaction yield": "demo_data/chemistry_yield_anova.csv",
    "[Lab] Pharmacy - adverse events": "demo_data/pharmacy_adverse_events.csv",
}

EXAMPLE_UPLOAD_CSV = """customer_id,campaign_version,purchase_completed,order_value,region
1001,Spring_Email_A,0,0,Seattle
1002,Spring_Email_A,1,79.90,Vancouver
1003,Spring_Email_A,0,0,London
1004,Spring_Email_B,1,129.00,Seattle
1005,Spring_Email_B,1,89.50,Vancouver
1006,Spring_Email_B,0,0,London
1007,Spring_Email_C,1,149.00,Seattle
1008,Spring_Email_C,1,99.00,Vancouver
1009,Spring_Email_C,0,0,London
"""


def load_sample_dataset(label):
    path = SAMPLE_DATASETS[label]
    return pd.read_csv(path), path


def inject_brand_css():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;600&display=swap');

            #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
            }

            .block-container {
                padding-top: 1.4rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }

            html, body, [class*="css"] {
                font-family: 'Outfit', sans-serif;
            }

            .stats-title {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 2.8rem;
                font-weight: 800;
                background: linear-gradient(135deg, #0F172A, #2563eb, #10B981);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.15rem;
            }

            .stats-subtitle {
                color: #475569;
                font-size: 1.08rem;
                margin-bottom: 0.8rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_csv_upload_guide():
    st.subheader("What kind of CSV can I upload?")
    st.write(
        "You do not need to rename your columns to `group` or `converted`. "
        "Upload the client's original CSV, then choose which column is the product/campaign/version "
        "and which column is the result to compare."
    )

    st.info(
        "Minimum requirement: one column that identifies the product, campaign, version, or condition; "
        "and one column that contains the result, such as purchase, revenue, signup, rating, or score."
    )

    examples = pd.DataFrame(
        [
            ["Email campaign", "campaign_version", "purchase_completed", "Spring_Email_A / Spring_Email_B", "0 or 1"],
            ["Product pricing", "pricing_plan", "order_value", "Basic / Pro / Premium", "49.99"],
            ["Landing page", "page_design", "signup", "blue_header / video_hero", "yes / no"],
            ["Survey feedback", "product_name", "satisfaction", "Product A / Product B", "Satisfied / Neutral / Unsatisfied"],
        ],
        columns=["Use case", "Example group column", "Example metric column", "Example group values", "Example metric values"],
    )
    st.dataframe(examples, width="stretch", hide_index=True)

    st.write("Example client-style CSV:")
    st.code(
        """customer_id,campaign_version,purchase_completed,order_value,region
1001,Spring_Email_A,0,0,Seattle
1002,Spring_Email_A,1,79.90,Vancouver
1003,Spring_Email_A,0,0,London
1004,Spring_Email_B,1,129.00,Seattle
1005,Spring_Email_B,1,89.50,Vancouver
1006,Spring_Email_B,0,0,London""",
        language="csv",
    )
    st.caption(
        "For this example: choose `campaign_version` as the group column, then choose "
        "`purchase_completed` for conversion analysis or `order_value` for revenue analysis."
    )

    st.download_button(
        "Download client-style example CSV",
        data=EXAMPLE_UPLOAD_CSV,
        file_name="client_ab_test_example.csv",
        mime="text/csv",
    )


def format_number(value, digits=4):
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def significance_label(p_value):
    if p_value is None:
        return ""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return "ns"


def add_significance_annotation(fig, result):
    if not result:
        return fig

    p_value = result.get("p_value")
    label = significance_label(p_value)
    if not label:
        return fig

    p_text = f"p = {p_value:.4f}" if p_value >= 0.0001 else "p < 0.0001"
    fig.add_annotation(
        text=f"{label} ({p_text})",
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.12,
        showarrow=False,
        font={"size": 14, "color": "#1f2937"},
        bgcolor="#f8fafc",
        bordercolor="#cbd5e1",
        borderwidth=1,
        borderpad=6,
    )
    fig.update_layout(margin={"t": 90})
    return fig


def is_binary_series(series):
    values = series.dropna()
    if values.empty:
        return False

    if pd.api.types.is_numeric_dtype(values):
        unique_values = set(values.astype(float).unique())
        return len(unique_values) <= 2 and unique_values.issubset({0.0, 1.0})

    normalized = set(values.astype(str).str.strip().str.lower().unique())
    binary_labels = {"0", "1", "true", "false", "yes", "no", "success", "failure"}
    return len(normalized) <= 2 and normalized.issubset(binary_labels)


def normalize_binary_success(series):
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float) == 1.0

    normalized = series.astype(str).str.strip().str.lower()
    success_labels = {"1", "true", "yes", "success"}
    return normalized.isin(success_labels)


def detect_value_type(series):
    clean = series.dropna()
    if clean.empty:
        return "empty"
    if is_binary_series(clean):
        return "binary"
    if pd.api.types.is_numeric_dtype(clean):
        return "continuous numeric"
    return "categorical"


def find_id_column(columns):
    candidates = ["user_id", "userid", "customer_id", "visitor_id", "id"]
    normalized = {col.lower().replace(" ", "_"): col for col in columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def diagnose_dataset(df, group_col, value_col):
    selected = df[[group_col, value_col]]
    complete = selected.dropna()
    total_rows = len(df)
    complete_rows = len(complete)
    missing_rows = total_rows - complete_rows
    missing_rate = missing_rows / total_rows if total_rows else 0
    group_values = complete[group_col].dropna().unique().tolist()
    group_count = len(group_values)
    value_type = detect_value_type(complete[value_col])
    id_col = find_id_column(df.columns)
    duplicate_id_count = int(df[id_col].duplicated().sum()) if id_col else 0

    issues = []
    warnings = []

    if total_rows == 0:
        issues.append("The uploaded CSV has no rows.")

    if complete_rows == 0:
        issues.append("No complete rows remain after dropping missing group/value cells.")

    if group_count < 2:
        issues.append(
            f"Your group column has only {group_count} value: {group_values}. "
            "At least 2 groups are required for statistical comparison."
        )

    if missing_rows:
        warnings.append(
            f"{missing_rows} of {total_rows} rows ({missing_rate:.1%}) have missing "
            "group/value cells and will be excluded from the analysis."
        )

    if id_col and duplicate_id_count:
        warnings.append(
            f"Detected {duplicate_id_count} duplicate values in '{id_col}'. "
            "If each row should represent one user, deduplicate before final analysis."
        )

    if value_type == "empty":
        issues.append("The selected value column is empty after missing values are removed.")
    elif value_type == "categorical":
        warnings.append("Categorical outcome detected. The app will route to Chi-Square.")
    elif value_type == "binary":
        if group_count == 2:
            warnings.append("Binary outcome detected. The app will route to a two-sample proportion Z-test.")
        elif group_count > 2:
            warnings.append("Binary outcome with 3+ groups detected. The app will route to multi-group Chi-Square.")
    elif value_type == "continuous numeric":
        if group_count == 2:
            warnings.append("Numeric outcome detected. The app will check assumptions before choosing T/Welch/Mann-Whitney.")
        elif group_count > 2:
            warnings.append("Numeric outcome with 3+ groups detected. The app will route to One-way ANOVA with Tukey post-hoc comparisons.")

    group_sizes = {}
    if complete_rows and group_count:
        group_sizes = complete[group_col].value_counts().sort_index().to_dict()
        small_groups = {name: size for name, size in group_sizes.items() if size < 3}
        if small_groups:
            warnings.append(
                f"Very small group sizes detected: {small_groups}. "
                "Results may be unstable."
            )

    return {
        "total_rows": total_rows,
        "complete_rows": complete_rows,
        "missing_rows": missing_rows,
        "missing_rate": missing_rate,
        "group_count": group_count,
        "group_values": group_values,
        "group_sizes": group_sizes,
        "value_type": value_type,
        "id_col": id_col,
        "duplicate_id_count": duplicate_id_count,
        "issues": issues,
        "warnings": warnings,
        "can_run": not issues,
    }


def show_data_diagnostics(diagnostics):
    st.subheader("Data diagnostics")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", diagnostics["total_rows"])
    col2.metric("Usable rows", diagnostics["complete_rows"])
    col3.metric("Groups", diagnostics["group_count"])
    col4.metric("Detected outcome", diagnostics["value_type"])

    if diagnostics["group_sizes"]:
        group_size_text = ", ".join(
            f"{group}: {size}" for group, size in diagnostics["group_sizes"].items()
        )
        st.caption(f"Group sizes: {group_size_text}")

    for issue in diagnostics["issues"]:
        st.error(issue)

    for warning in diagnostics["warnings"]:
        st.warning(warning)


def build_visualization_figure(df, group_col, value_col, result=None):
    clean = df[[group_col, value_col]].dropna()
    if clean.empty:
        return None

    if is_binary_series(clean[value_col]):
        chart_df = (
            clean.assign(success=normalize_binary_success(clean[value_col]))
            .groupby(group_col)["success"]
            .agg(["sum", "count", "mean"])
            .reset_index()
            .rename(columns={"sum": "successes", "count": "n", "mean": "rate"})
        )
        chart_df["ci"] = 1.96 * np.sqrt(chart_df["rate"] * (1 - chart_df["rate"]) / chart_df["n"])
        chart_df["conversion_rate"] = chart_df["rate"] * 100
        chart_df["ci_percent"] = chart_df["ci"] * 100

        fig = go.Figure()
        palette = ["#2563eb", "#0d9488", "#f59e0b", "#ef4444", "#8b5cf6"]
        fig.add_trace(go.Bar(
            x=chart_df[group_col],
            y=chart_df["conversion_rate"],
            error_y={"type": "data", "array": chart_df["ci_percent"], "visible": True},
            marker_color=palette[:len(chart_df)],
            text=[f"{rate:.1f}%" for rate in chart_df["conversion_rate"]],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Conversion: %{y:.2f}%<br>"
                "95% CI: +/- %{customdata[0]:.2f}%<br>"
                "n: %{customdata[1]}<extra></extra>"
            ),
            customdata=chart_df[["ci_percent", "n"]],
        ))
        fig.update_layout(
            title="Conversion Rate by Group with 95% CI",
            xaxis_title="Group",
            yaxis_title="Conversion rate (%)",
            yaxis_range=[0, max(5, (chart_df["conversion_rate"] + chart_df["ci_percent"]).max() * 1.2)],
        )
        return add_significance_annotation(fig, result)

    if pd.api.types.is_numeric_dtype(clean[value_col]):
        fig = px.box(
            clean,
            x=group_col,
            y=value_col,
            color=group_col,
            points="outliers",
            title=f"{value_col} Distribution by {group_col}",
            color_discrete_sequence=["#2563eb", "#0d9488", "#f59e0b", "#ef4444"],
        )
        fig.update_layout(showlegend=False, xaxis_title="Group", yaxis_title=value_col)
        return add_significance_annotation(fig, result)

    counts = clean.groupby([group_col, value_col]).size().reset_index(name="count")
    counts["percent"] = counts["count"] / counts.groupby(group_col)["count"].transform("sum") * 100
    fig = px.bar(
        counts,
        x=group_col,
        y="percent",
        color=value_col,
        text=counts["percent"].map(lambda value: f"{value:.1f}%"),
        title=f"{value_col} Distribution by {group_col}",
        color_discrete_sequence=["#2563eb", "#0d9488", "#f59e0b", "#ef4444", "#8b5cf6"],
    )
    fig.update_layout(
        barmode="stack",
        xaxis_title="Group",
        yaxis_title="Percent of responses",
        yaxis_range=[0, 100],
    )
    return add_significance_annotation(fig, result)


def show_visualization(df, group_col, value_col, result=None):
    fig = build_visualization_figure(df, group_col, value_col, result)
    if fig is None:
        st.warning("No complete rows available for visualization.")
        return

    st.subheader("Visual comparison")
    st.plotly_chart(fig, width="stretch")


def build_plain_english(result):
    group_a = result.get("group_a_name", "Group A")
    group_b = result.get("group_b_name", "Group B")
    p_value = result.get("p_value")
    alpha = result.get("alpha", 0.05)
    difference = result.get("difference")
    test_name = result.get("test_name", "statistical test")

    if p_value is None:
        return "The analysis completed, but no p-value was returned."

    direction = ""
    if isinstance(difference, (int, float)):
        if difference > 0:
            direction = f" {group_b} is higher than {group_a} in this sample."
        elif difference < 0:
            direction = f" {group_b} is lower than {group_a} in this sample."

    if p_value < alpha:
        return (
            f"The {test_name} found a statistically significant difference "
            f"(p = {p_value:.4f}).{direction}"
        )

    return (
        f"The {test_name} did not find a statistically significant difference "
        f"(p = {p_value:.4f}).{direction} The observed gap may be random noise."
    )


def show_result_summary(result, assumptions, df, group_col, value_col):
    st.subheader("Results")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Selected test", result.get("test_name", "N/A"))
    col2.metric("p-value", format_number(result.get("p_value")))
    col3.metric("Statistic", format_number(result.get("statistic")))
    col4.metric(
        result.get("effect_size_label", "Effect size"),
        format_number(result.get("effect_size_value")),
    )
    col5.metric("Decision", "Reject H0" if result.get("reject_h0") else "Fail to reject H0")

    if result.get("effect_size_note"):
        st.caption(result["effect_size_note"])

    if "ci_lower" in result and "ci_upper" in result:
        st.info(
            "Confidence interval for Group B - Group A: "
            f"[{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]"
        )

    st.subheader("Plain-English conclusion")
    st.write(build_plain_english(result))

    if assumptions:
        st.subheader("Assumption checks")
        assumption_cols = st.columns(4)
        assumption_cols[0].metric("Recommended route", assumptions.get("recommended_test", "N/A"))
        assumption_cols[1].metric(
            "Shapiro p - Group A",
            format_number(assumptions["group_a_normality"].get("p_value")),
        )
        assumption_cols[2].metric(
            "Shapiro p - Group B",
            format_number(assumptions["group_b_normality"].get("p_value")),
        )
        assumption_cols[3].metric(
            "Levene p",
            format_number(assumptions["variance_equality"].get("p_value")),
        )
        st.write(assumptions["group_a_normality"]["note"])
        st.write(assumptions["group_b_normality"]["note"])
        st.write(assumptions["variance_equality"]["note"])

    if result.get("test_name") == "One-Way ANOVA" and result.get("post_hoc"):
        st.subheader("Tukey post-hoc comparisons")
        tukey_df = pd.DataFrame(result["post_hoc"])
        st.dataframe(
            tukey_df[["group1", "group2", "mean_diff", "p_adj", "lower", "upper", "reject"]],
            width="stretch",
            hide_index=True,
        )

    show_visualization(df, group_col, value_col, result)


def main():
    st.set_page_config(
        page_title="Statistical Inference Toolkit",
        page_icon="ST",
        layout="wide",
    )
    inject_brand_css()

    st.markdown('<div class="stats-title">Statistical Inference Toolkit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="stats-subtitle">A/B tests · lab experiments · surveys → test selection → PDF report</div>',
        unsafe_allow_html=True,
    )

    source = st.radio(
        "Choose data source",
        ["Use sample data", "Upload CSV"],
        horizontal=True,
    )

    df = None
    source_name = None

    if source == "Use sample data":
        sample_label = st.selectbox("Sample dataset", list(SAMPLE_DATASETS.keys()))
        df, source_name = load_sample_dataset(sample_label)
    else:
        st.caption("Accepted file: `.csv`. Minimum columns: one variant/group column and one metric/outcome column.")
        uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            source_name = uploaded_file.name
        else:
            show_csv_upload_guide()

    if df is None:
        st.warning("Use the sample data, or upload a CSV that follows the format above.")
        return

    st.subheader("Data preview")
    st.caption(f"Source: {source_name}")
    st.dataframe(df.head(20), width="stretch")

    columns = list(df.columns)
    left, right, third = st.columns(3)
    group_col = left.selectbox("Group column", columns)
    value_col = right.selectbox(
        "Value column",
        columns,
        index=1 if len(columns) > 1 else 0,
    )
    alpha = third.selectbox("Significance level", [0.01, 0.05, 0.10], index=1)

    alternative = st.selectbox(
        "Alternative hypothesis",
        ["two-sided", "greater", "less"],
        help="'greater' tests whether Group B is greater than Group A.",
    )

    st.subheader("Report details")
    meta_left, meta_right = st.columns(2)
    client_name = meta_left.text_input(
        "Client / project name",
        value="Portfolio Demo / Custom CSV Project",
    )
    prepared_by = meta_right.text_input(
        "Prepared by",
        value="Tianyou Liu - Statistical Analysis",
    )
    audience = st.selectbox(
        "Who is this report for?",
        ["researcher", "small_business", "fiverr_buyer"],
        format_func=lambda value: {
            "fiverr_buyer": "Fiverr buyer - shortest, trust-focused summary",
            "small_business": "Small business / marketer - rollout decision report",
            "researcher": "Researcher / PhD - full statistical methodology",
        }[value],
    )
    st.caption('For business clients, switch to "Small business" for a shorter decision summary.')

    if group_col == value_col:
        st.error("Group column and value column must be different.")
        return

    diagnostics = diagnose_dataset(df, group_col, value_col)
    show_data_diagnostics(diagnostics)

    if not diagnostics["can_run"]:
        st.info("Fix the issues above, then run the analysis again.")
        return

    if st.button("Run analysis", type="primary"):
        with st.spinner("Running statistical test and generating PDF..."):
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                    output_pdf = tmp_pdf.name

                result, assumptions = run_pipeline(
                    df,
                    group_col=group_col,
                    value_col=value_col,
                    alpha=alpha,
                    alternative=alternative,
                    output_pdf=output_pdf,
                    report_metadata={
                        "client_name": client_name,
                        "prepared_by": prepared_by,
                        "audience": audience,
                    },
                )
            except SystemExit as exc:
                st.error(f"Analysis stopped: {exc}")
                return
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        show_result_summary(result, assumptions, df, group_col, value_col)

        with open(output_pdf, "rb") as pdf_file:
            st.download_button(
                "Download PDF report",
                data=pdf_file,
                file_name="ab_test_report.pdf",
                mime="application/pdf",
            )

        try:
            os.remove(output_pdf)
        except OSError:
            pass


if __name__ == "__main__":
    main()
