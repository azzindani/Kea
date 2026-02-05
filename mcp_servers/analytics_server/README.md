# 📊 Analytics Server (MCP)

The **Analytics Server** provides a suite of advanced data science tools for exploratory data analysis (EDA), cleaning, transformation, and statistical validation. It leverages the power of **Pandas**, **Numpy**, and **Scipy** to process datasets.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `eda_auto` | Perform automatic Exploratory Data Analysis. Generates summaries of types, missing values, and numeric distributions. |
| `data_profiler` | Generate a detailed data profile report (uses `ydata-profiling` if available). |
| `data_cleaner` | Clean datasets by handling missing values (mean/median/mode/ffill), outliers (clip/drop), and duplicates. |
| `correlation_matrix` | Compute Pearson/Spearman/Kendall correlation matrices for numeric columns. |
| `statistical_test` | Run statistical tests including T-Tests, ANOVA, Chi-Square, and Shapiro-Wilk (normality). |
| `feature_engineer` | Automate feature engineering tasks like one-hot encoding, ratio creation, and date extraction. |

## 🏗️ Implementation

This server acts as a wrapper around Python's data science stack. It supports loading data from direct JSON inputs or external CSV URLs. Results are returned as structured Markdown reports.

## 📦 Dependencies

- `pandas`: Core data manipulation.
- `numpy`: Numerical calculations.
- `scipy`: Statistical testing engine.
- `ydata-profiling`: (Optional) Advanced profiling reports.
