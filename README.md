# 📊 Automated A/B Testing Report Pipeline (Fiverr Showcase)

A production-ready Python tool designed to automate statistical hypothesis testing and generate publication-grade PDF business reports in seconds. 

> **Perfect for Marketers, Product Managers, and Data Teams** who want to stop manually running calculations in Excel and need client-ready reports instantly.

---

## 💎 Client Value & Business Benefits
- **Zero Manual Calculations**: Input your raw CSV, and the pipeline automatically handles statistical assumptions (normality, variance checks) and selects the mathematically correct test.
- **Client-Ready Deliverables**: Automatically exports high-end, clean PDF reports with standard AP Statistics (State-Plan-Do-Conclude) framework and styled LaTeX equations.
- **Robust Decision Making**: Includes detailed p-value and confidence interval explanations, reducing the risk of false positives in business experiments.

## 🚀 Interactive Demo & Features
1. **Normality Check**: Uses Shapiro-Wilk test to ensure data distribution is valid.
2. **Homogeneity of Variance Check**: Uses Levene's test to guide between Student's t-test and Welch's t-test.
3. **Automated Test Selection**: Handles Z-test, T-test, Mann-Whitney U, and Chi-Square dynamically.
4. **PDF Engine**: Instantly generates polished reports (stored in `reports/` folder).

---

## 🛠️ Quick Start Guide (For Technical Clients)

### 1. Installation
Clone this repository and install the standard statistical libraries:
```bash
git clone https://github.com/LIUYOUCecilia/stats-inference-toolkit.git
cd stats-inference-toolkit
pip install pandas scipy matplotlib reportlab statsmodels
