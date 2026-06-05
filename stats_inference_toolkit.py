# -*- coding: utf-8 -*-
"""
stats_inference_toolkit.py
Main orchestration entry point for loading data, auto-routing to the correct test,
and compiling a PDF report.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np

import assumptions_checker as checker
import ab_testers as testers
import pdf_generator as generator

def load_data(filepath):
    """
    Loads data from CSV.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found at '{filepath}'")
        sys.exit(1)
        
    try:
        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        sys.exit(1)

def run_pipeline(df, group_col, value_col, alpha=0.05, alternative="two-sided", output_pdf="ab_test_report.pdf", force_test=None):
    """
    Analyzes data, runs calculations, and writes the PDF report.
    """
    print(f"\n--- Starting Analysis on '{value_col}' by '{group_col}' ---")
    
    # 1. Clean data: Drop rows with missing values in target columns
    df_clean = df[[group_col, value_col]].dropna()
    
    # Get unique groups (expecting exactly 2 for A/B tests)
    unique_groups = df_clean[group_col].unique()
    if len(unique_groups) != 2:
        print(f"Error: Expected exactly 2 groups in column '{group_col}', found {len(unique_groups)}: {unique_groups}")
        sys.exit(1)
        
    # Sort groups to maintain consistency
    group_names = sorted(list(unique_groups))
    group_a_name, group_b_name = group_names[0], group_names[1]
    
    group_a_data = df_clean[df_clean[group_col] == group_a_name][value_col]
    group_b_data = df_clean[df_clean[group_col] == group_b_name][value_col]
    
    print(f"Group A ({group_a_name}): n = {len(group_a_data)}")
    print(f"Group B ({group_b_name}): n = {len(group_b_data)}")
    
    # Determine the data type
    values = df_clean[value_col].values
    is_numeric = np.issubdtype(values.dtype, np.number)
    
    # Unique value count helps determine if data is binary/boolean
    unique_vals = np.unique(values)
    is_binary = len(unique_vals) <= 2 and (
        all(v in [0, 1, 0.0, 1.0] for v in unique_vals) or 
        all(v in [True, False] for v in unique_vals) or
        all(isinstance(v, str) and v.lower() in ['yes', 'no', 'success', 'failure', 'true', 'false'] for v in unique_vals)
    )
    
    # Check if user forced a specific test
    if force_test:
        test_type = force_test.lower()
    elif is_binary:
        test_type = "proportion_z"
    elif is_numeric:
        test_type = "means_t"
    else:
        test_type = "chi_square"
        
    print(f"Detected variable type: {'Binary/Success-Failure' if is_binary else 'Continuous Numerical' if is_numeric else 'Categorical'}")
    print(f"Selected route: {test_type.upper()}")
    
    # Run the tests based on selected route
    test_results = None
    assumptions_results = None
    
    if test_type == "proportion_z":
        # Convert binary categories into successes/totals
        # Let's count success cases (treating 1, True, or 'yes'/'success' as success)
        def count_successes(series):
            unique_s = series.unique()
            success_indicators = [1, 1.0, True, 'yes', 'success', 'true']
            success_sum = 0
            for ind in success_indicators:
                success_sum += (series == ind).sum()
                if isinstance(ind, str):
                    success_sum += (series.astype(str).str.lower() == ind).sum()
            # If nothing matched (e.g. 0/1 integers were already covered), fallback to the max val
            if success_sum == 0:
                max_val = series.max()
                success_sum = (series == max_val).sum()
            return int(success_sum)
            
        x_a = count_successes(group_a_data)
        n_a = len(group_a_data)
        x_b = count_successes(group_b_data)
        n_b = len(group_b_data)
        
        print(f"Proportion conversions: Group A = {x_a}/{n_a} ({x_a/n_a:.4%}), Group B = {x_b}/{n_b} ({x_b/n_b:.4%})")
        test_results = testers.run_proportion_z_test(x_a, n_a, x_b, n_b, alpha, alternative)
        
    elif test_type == "means_t":
        # Run assumptions check first
        print("Running normality and variance check...")
        assumptions_results = checker.analyze_assumptions(group_a_data.values, group_b_data.values, alpha)
        
        rec = assumptions_results["recommended_test"]
        print(f"Normality A: {assumptions_results['group_a_normality']['note']}")
        print(f"Normality B: {assumptions_results['group_b_normality']['note']}")
        print(f"Equal Variance: {assumptions_results['variance_equality']['note']}")
        print(f"Recommendation: Use {rec}")
        
        if "Student's T-test" in rec:
            test_results = testers.run_means_t_test(group_a_data.values, group_b_data.values, alpha, equal_var=True, alternative=alternative)
        elif "Welch's T-test" in rec:
            test_results = testers.run_means_t_test(group_a_data.values, group_b_data.values, alpha, equal_var=False, alternative=alternative)
        else:
            # Mann-Whitney U test fallback
            test_results = testers.run_mann_whitney_u_test(group_a_data.values, group_b_data.values, alpha, alternative=alternative)
            
    elif test_type == "chi_square" or test_type == "categorical":
        # Build contingency table
        contingency_table = pd.crosstab(df_clean[group_col], df_clean[value_col])
        print("Contingency Table (Observed):")
        print(contingency_table)
        observed = contingency_table.values
        test_results = testers.run_chi_square_test(observed, alpha)
        
    else:
        print(f"Error: Unknown test route '{force_test}'")
        sys.exit(1)
        
    # Inject group names for presentation
    test_results["group_a_name"] = group_a_name
    test_results["group_b_name"] = group_b_name
    
    # 3. Generate Report
    print(f"Generating PDF report: {output_pdf}...")
    generator.generate_report(test_results, assumptions_results, output_pdf)
    print("Report completed successfully!")
    return test_results, assumptions_results

def main():
    parser = argparse.ArgumentParser(description="stats-inference-toolkit: A/B Testing & Statistical Inference Toolkit")
    parser.add_argument("--data", required=True, help="Path to input CSV data file")
    parser.add_argument("--group-col", required=True, help="Name of the group/variant column (e.g. 'variant')")
    parser.add_argument("--value-col", required=True, help="Name of the value metric column (e.g. 'converted', 'revenue')")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level (default: 0.05)")
    parser.add_argument("--alternative", choices=["two-sided", "greater", "less"], default="two-sided", help="Alternative hypothesis type (default: two-sided)")
    parser.add_argument("--output", default="ab_test_report.pdf", help="Output PDF report filepath (default: ab_test_report.pdf)")
    parser.add_argument("--force-test", choices=["proportion_z", "means_t", "categorical", "mann_whitney"], default=None, help="Force a specific statistical test")
    
    args = parser.parse_args()
    
    df = load_data(args.data)
    run_pipeline(
        df,
        group_col=args.group_col,
        value_col=args.value_col,
        alpha=args.alpha,
        alternative=args.alternative,
        output_pdf=args.output,
        force_test=args.force_test
    )

if __name__ == "__main__":
    main()
