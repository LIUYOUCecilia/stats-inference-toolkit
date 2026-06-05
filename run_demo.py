# -*- coding: utf-8 -*-
"""
run_demo.py
Generates mock A/B test data for binary, continuous (normal & non-normal), and categorical metrics,
runs the statistical pipeline, and verifies that PDF reports are successfully created.
"""
import os
import pandas as pd
import numpy as np
import stats_inference_toolkit as toolkit

def generate_mock_data():
    print("Generating mock datasets...")
    os.makedirs("demo_data", exist_ok=True)
    np.random.seed(42) # For reproducible results
    
    # 1. Binary Conversion Data (Z-Test)
    # Group A: 1000 visitors, 12.0% conversion
    # Group B: 1050 visitors, 15.2% conversion
    n_a, p_a = 1000, 0.120
    n_b, p_b = 1050, 0.152
    
    group_a_conv = np.random.binomial(1, p_a, n_a)
    group_b_conv = np.random.binomial(1, p_b, n_b)
    
    df_binary = pd.DataFrame({
        "group": ["Group_A"] * n_a + ["Group_B"] * n_b,
        "converted": np.concatenate([group_a_conv, group_b_conv])
    })
    df_binary.to_csv("demo_data/conversion_data.csv", index=False)
    print("  -> Saved demo_data/conversion_data.csv (Binary Z-test)")
    
    # 2. Continuous Metric Data - Normal (Welch's T-Test due to unequal variances)
    # Group A: 50 orders, mean revenue $45, std dev $8
    # Group B: 55 orders, mean revenue $52, std dev $15
    n_t_a = 50
    n_t_b = 55
    rev_a = np.random.normal(45.0, 8.0, n_t_a)
    rev_b = np.random.normal(52.0, 15.0, n_t_b)
    
    df_means = pd.DataFrame({
        "group": ["Control"] * n_t_a + ["Variant"] * n_t_b,
        "revenue": np.concatenate([rev_a, rev_b])
    })
    df_means.to_csv("demo_data/revenue_data.csv", index=False)
    print("  -> Saved demo_data/revenue_data.csv (Continuous T-test)")
    
    # 3. Continuous Metric Data - Non-Normal (Mann-Whitney U Test fallback)
    # Shapiro-Wilk will reject normality, and small sample size (n < 30) will bypass CLT.
    n_mw_a = 18
    n_mw_b = 20
    # Exponential distributions are highly skewed (non-normal)
    duration_a = np.random.exponential(scale=10.0, size=n_mw_a)
    duration_b = np.random.exponential(scale=18.0, size=n_mw_b)
    
    df_non_normal = pd.DataFrame({
        "group": ["Control"] * n_mw_a + ["Variant"] * n_mw_b,
        "session_duration": np.concatenate([duration_a, duration_b])
    })
    df_non_normal.to_csv("demo_data/session_data.csv", index=False)
    print("  -> Saved demo_data/session_data.csv (Continuous Non-parametric)")

    # 4. Categorical Feedback Data (Chi-Square Test of Independence)
    # Survey rating responses: 'Satisfied', 'Neutral', 'Unsatisfied'
    n_cat_a = 200
    n_cat_b = 220
    # Probabilities:
    # Control: 55% Satisfied, 30% Neutral, 15% Unsatisfied
    # Variant: 65% Satisfied, 25% Neutral, 10% Unsatisfied
    rating_choices = ["Satisfied", "Neutral", "Unsatisfied"]
    ratings_a = np.random.choice(rating_choices, size=n_cat_a, p=[0.55, 0.30, 0.15])
    ratings_b = np.random.choice(rating_choices, size=n_cat_b, p=[0.65, 0.25, 0.10])
    
    df_categorical = pd.DataFrame({
        "group": ["Control"] * n_cat_a + ["Variant"] * n_cat_b,
        "satisfaction_rating": np.concatenate([ratings_a, ratings_b])
    })
    df_categorical.to_csv("demo_data/feedback_data.csv", index=False)
    print("  -> Saved demo_data/feedback_data.csv (Categorical Chi-Square)")
    print()

def run_tests():
    print("Starting pipeline test suite...\n")
    os.makedirs("reports", exist_ok=True)
    
    # Test Case 1: Proportions Z-Test
    df_conv = pd.read_csv("demo_data/conversion_data.csv")
    toolkit.run_pipeline(
        df_conv, 
        group_col="group", 
        value_col="converted", 
        output_pdf="reports/conversion_z_report.pdf"
    )
    
    # Test Case 2: Means T-Test (Welch)
    df_rev = pd.read_csv("demo_data/revenue_data.csv")
    toolkit.run_pipeline(
        df_rev, 
        group_col="group", 
        value_col="revenue", 
        output_pdf="reports/revenue_t_report.pdf"
    )
    
    # Test Case 3: Mann-Whitney U test (Non-parametric fallback due to non-normality and n < 30)
    df_session = pd.read_csv("demo_data/session_data.csv")
    toolkit.run_pipeline(
        df_session, 
        group_col="group", 
        value_col="session_duration", 
        output_pdf="reports/session_nonparametric_report.pdf"
    )
    
    # Test Case 4: Chi-Square Test of Independence
    df_feedback = pd.read_csv("demo_data/feedback_data.csv")
    toolkit.run_pipeline(
        df_feedback, 
        group_col="group", 
        value_col="satisfaction_rating", 
        output_pdf="reports/feedback_chisquare_report.pdf"
    )
    
    print("\nAll pipeline tests executed!")
    print("Verify files in reports/:")
    print("  - reports/conversion_z_report.pdf")
    print("  - reports/revenue_t_report.pdf")
    print("  - reports/session_nonparametric_report.pdf")
    print("  - reports/feedback_chisquare_report.pdf")

if __name__ == "__main__":
    generate_mock_data()
    run_tests()
