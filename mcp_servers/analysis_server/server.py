
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
from typing import List, Dict, Any, Union, Optional
from shared.logging.main import setup_logging, get_logger
setup_logging(force_stderr=True)
logger = get_logger(__name__)

from mcp_servers.analysis_server.tools import stats_ops



mcp = FastMCP("analysis_server", dependencies=["pandas", "numpy", "scikit-learn", "xgboost", "tensorflow", "matplotlib", "seaborn", "statsmodels", "scipy"])

@mcp.tool()
def meta_analysis(data_points: List[Dict[str, Any]], analysis_type: str = "comparison") -> str:
    """PERFORMS meta-analysis across sources. [ENTRY]
    
    [RAG Context]
    A high-level "Super Tool" that aggregates and compares results from multiple independent datasets or agents to find underlying patterns or contradictions.
    
    How to Use:
    - 'analysis_type': Use 'comparison' to find differences, 'consensus' to find commonalities, or 'variance' to see spread.
    - Input 'data_points' should be a list of results from other tools.
    
    Keywords: synthesis, aggregate data, consensus building, comparative analysis.
    """
    return stats_ops.meta_analysis(data_points, analysis_type)

@mcp.tool()
def trend_detection(data: List[Union[Dict, float, int]], metric_name: str = "Value", detect_anomalies: bool = True) -> str:
    """DETECTS trends and anomalies in time-series. [ENTRY]
    
    [RAG Context]
    Analyzes historical data sequences to identify significant upward/downward shifts or sudden spikes/dips.
    
    How to Use:
    - 'data': A list of values.
    - 'detect_anomalies': If True, it uses statistical thresholds (Z-score) to flag outliers in the trend.
    
    Keywords: drift analysis, anomaly scan, temporal patterns, trajectory check.
    """
    return stats_ops.trend_detection(data, metric_name, detect_anomalies)

@mcp.tool()
async def analyze_data_science_project(dataset_url: str, target_column: str, goal: str) -> Dict[str, Any]:
    """EXECUTES a complete, end-to-end data science pipeline using an autonomous agentic workflow. [ACTION] [SUPER TOOL]
    
    [RAG Context]
    This is the "Grand-Master Orchestrator" of the analysis server. It is a highly sophisticated agentic tool that automates the entire lifecycle of a data science project. It doesn't just run a single model; it performs intelligent data ingestion, automated exploratory data analysis (EDA), multi-tier data cleaning, feature engineering, and model selection across multiple libraries (NumPy, Pandas, Scikit-Learn, XGBoost, TensorFlow). It is the mandatory tool for "Corporate Intelligence Discovery," allowing the Kea system to take a raw dataset URL and a high-level goal (e.g., "Predict customer churn and identify key drivers") and return a fully evaluated model and insight report without human intervention.
    
    How to Use:
    - 'dataset_url': Provide a direct link to the CSV, Parquet, or remote data source.
    - 'target_column': Specify the variable the system should learn to predict.
    - 'goal': Define the business objective in natural language to guide the agent's internal reasoning.
    - Returns a comprehensive dictionary containing model metrics (accuracy, RMSE, etc.), feature importance maps, and a summary of the cleaning steps performed.
    
    Keywords: autonomous data science, auto-ml, pipeline orchestration, end-to-end analysis, automated modeling, data intelligence agent.
    """
    from mcp_servers.analysis_server.tools import agent_ops
    return await agent_ops.analyze_data_science_project(dataset_url, target_column, goal)


# ==========================================
# 3. Visualization Tools (New)
# ==========================================
# ==========================================
# 3. Visualization Tools (New)
# ==========================================
@mcp.tool()
def plot_scatter(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "scatter.png") -> str:
    """PLOTS Scatter chart. [ACTION]
    
    [RAG Context]
    Generates a 2D scatter plot to visualize the relationship (correlation or clustering) between two continuous numerical variables.
    
    How to Use:
    - 'hue': Optional categorical column name to color-code points.
    - Uses Seaborn and Matplotlib for high-quality rendering.
    
    Keywords: correlation plot, xy graph, relationship viz, scatter points.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_scatter(file_path, x, y, hue, output_path)

@mcp.tool()
def plot_line(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "line.png") -> str:
    """GENERATES a professional-grade line chart to visualize trends and time-series progressions. [ACTION]
    
    [RAG Context]
    A foundational "Temporal Analysis Super Tool" for tracking the trajectory of metrics over time or sequence. Line charts are the definitive standard for visualizing "Continuous Progression," allowing the system to identify growth rates, seasonal cycles, and sudden trend breaks in business data. By using the 'hue' parameter, the tool can overlay multiple lines on a single axis (e.g., "Company Revenue vs Competitor Revenue"), enabling direct comparative momentum analysis. It is the mandatory tool for "KPI Monitoring" and "Financial Forecasting" across the Kea corporate kernel.
    
    How to Use:
    - 'x': Typically a temporal column (date) or a sequence identifier.
    - 'y': The numerical metric whose trend you wish to visualize.
    - 'hue': Optional categorical column for faceted line analysis.
    - Produces a high-resolution image suitable for executive board decks and automated performance alerts.
    
    Keywords: trend visualization, time-series plot, momentum tracking, progress chart, comparative line graph, temporal analytics.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_line(file_path, x, y, hue, output_path)

@mcp.tool()
def plot_bar(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "bar.png") -> str:
    """CREATES a high-impact bar chart for categorical comparison and aggregate analysis. [ACTION]
    
    [RAG Context]
    An essential "Executive Comparison Super Tool" designed to visualize differences between distinct categories. While line charts show trends, bar charts are the gold standard for "Cross-Sectional Auditing," where you need to compare discrete entities (e.g., "Sales by Region" or "Headcount by Department"). The tool automatically handles aggregation if multiple records exist for a single category, providing a clean, authoritative view of the data's volume and composition. It is the mandatory tool for "Resource Allocation Reviews" and "Market Share Benchmarking."
    
    How to Use:
    - 'x': A categorical column (labels).
    - 'y': A numerical column (volumes/values).
    - 'hue': Use this for sub-categorized comparisons (e.g., "Region" on the X-axis, and "Quarter" as the hue).
    - Delivers a premium-quality visual representation tailored for institutional-grade reporting.
    
    Keywords: bar chart, categorical comparison, volume visualization, regional analysis, aggregate comparison, cross-sectional audit.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_bar(file_path, x, y, hue, output_path)

@mcp.tool()
def plot_hist(file_path: str, x: str, bins: int = 20, hue: Optional[str] = None, output_path: str = "hist.png") -> str:
    """PLOTS Histogram/Distribution. [ACTION]
    
    [RAG Context]
    Shows frequency distribution.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_hist(file_path, x, bins, hue, output_path)

@mcp.tool()
def plot_box(file_path: str, x: str, y: str, output_path: str = "box.png") -> str:
    """PLOTS Box plot. [ACTION]
    
    [RAG Context]
    Statistical summary (quartiles, outliers).
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_box(file_path, x, y, output_path)

@mcp.tool()
def plot_violin(file_path: str, x: str, y: str, output_path: str = "violin.png") -> str:
    """RENDERS a sophisticated violin plot combining distribution density with statistical summaries. [ACTION]
    
    [RAG Context]
    An advanced "Statistical Density Super Tool" for high-resolution distribution comparison. Unlike a standard box plot, a violin plot includes a "Kernel Density Estimate" (KDE) which reveals the "True Shape" of the data distribution for each category. This allows the system to identify if a group is bimodal (has two sub-peaks) or has unique skewness that a simple median calculation would miss. It is the preferred tool for "Technical Quality Audits" and "Scientific Telemetry," where understanding the "Probability Map" of a variable is as important as its central range.
    
    How to Use:
    - 'x': The categorical grouping variable.
    - 'y': The numerical distribution variable.
    - The resulting graphic provides a premium visual summary of probability peaks, quartiles, and outliers in one unified, high-density dashboard.
    
    Keywords: violin plot, density visualization, probability distribution, multimodal analysis, high-resolution statistics, distribution variance.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_violin(file_path, x, y, output_path)

@mcp.tool()
def plot_heatmap(file_path: str, output_path: str = "heatmap.png") -> str:
    """GENERATES a professional correlation heatmap to visualize relationships between all numerical variables. [ACTION]
    
    [RAG Context]
    An elite "Relational Discovery Super Tool" used for high-density pattern recognition across an entire dataset. A heatmap transforms the raw correlation matrix—which can be overwhelming in numerical form—into a vibrant, color-coded grid. This allows the AI and human analysts to instantly identify "Feature Clusters," redundant variables (multi-collinearity), and unexpected strong associations. It is the mandatory tool for "Multivariate Screening," providing the strategic overview needed before selecting features for complex predictive modeling or risk assessment.
    
    How to Use:
    - Simply provide the 'file_path' to the dataset.
    - The tool automatically identifies all numerical columns and calculates their Pearson correlation.
    - Standard color gradients (e.g., 'RdBu' or 'viridis') are used to ensure the difference between positive and negative correlation is visually striking and instantly interpretable.
    
    Keywords: correlation heatmap, feature relationship, multivariate discovery, pattern recognition, redundancy check, relational grid.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_heatmap(file_path, output_path)

@mcp.tool()
def plot_pairplot(file_path: str, hue: Optional[str] = None, output_path: str = "pairplot.png") -> str:
    """CREATES a comprehensive pairplot grid to visualize all pairwise relationships in a dataset. [ACTION]
    
    [RAG Context]
    The absolute "System-Wide Data Audit Super Tool" for high-dimensional discovery. A pairplot generates a matrix of scatter plots (for variable interactions) and histograms (for individual distributions) for every numeric column in the dataset. This "All-at-Once" view allows the system to detect non-linear correlations, hidden data clusters, and outlier concentrations that a simple correlation number would miss. It is the mandatory first step for any "Deep Data Investigation," providing a complete visual map of the data's internal structural logic.
    
    How to Use:
    - 'hue': Assign a categorical column to color-code the entire grid, making it instantly obvious how different groups (e.g., "Premium" vs "Basic" users) occupy the multidimensional data space.
    - Warning: Can be mathematically intensive and create very large images for datasets with more than 10 numerical columns.
    
    Keywords: pairplot, pairwise visualization, scatter matrix, multidimensional audit, relational discovery, data landscape.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_pairplot(file_path, hue, output_path)

@mcp.tool()
def plot_confusion_matrix(file_path: str, y_true: str, y_pred: str, output_path: str="cm.png") -> str:
    """GENERATES a professional confusion matrix to evaluate the performance of a classification model. [ACTION]
    
    [RAG Context]
    The definitive "Model Diagnostic Super Tool" for classification accuracy auditing. While a single "Accuracy Score" can be misleading, a confusion matrix breaks down the performance into True Positives, True Negatives, False Positives (Type I Errors), and False Negatives (Type II Errors). This allows the system to understand *how* a model is failing—for example, distinguishing between a model that simply "guesses" and one that has a specific bias toward one category. It is a mandatory requirement for "Quality Assurance" in any machine learning deployment.
    
    How to Use:
    - 'y_true': The column name containing the actual ground-truth labels.
    - 'y_pred': The column name containing the model's predictions.
    - Result is a color-coded heatmap that makes it instantly obvious where the model is confusing one class for another (e.g., mislabeling "Fraud" as "Normal").
    
    Keywords: confusion matrix, model evaluation, classification audit, accuracy breakdown, error analysis, diagnostic visualization.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_confusion_matrix(file_path, y_true, y_pred, output_path)


# ==========================================
# 4. Statistical Tests (New)
# ==========================================
@mcp.tool()
def test_ttest_1samp(file_path: str, column: str, population_mean: float) -> Dict[str, Any]:
    """PERFORMS a statistically rigorous One-Sample T-Test to compare a column mean against a target benchmark. [DATA]
    
    [RAG Context]
    A vital "Benchmark Verification Super Tool" used to determine if a specific data group differs significantly from a known standard or business goal. For example, "Is our average delivery time of 3.2 days statistically higher than our corporate target of 3.0 days, or is the difference due to random daily variance?" This tool provides the "Mathematical Proof" required for executive decision-making, moving beyond simple averages to provide a probability-based confidence level (P-value). It is mandatory for "Performance Auditing" and "SLA Compliance Checks."
    
    How to Use:
    - 'column': The numerical field to test.
    - 'population_mean': The target or known population average you are comparing against.
    - Check the 'p-value': If p < 0.05, the difference is considered statistically significant, indicating that the observed mean did not occur by chance.
    
    Keywords: one-sample t-test, benchmark comparison, mean verification, statistical significance, performance audit, goal validation.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_ttest_1samp(file_path, column, population_mean)

@mcp.tool()
def test_ttest_ind(file_path1: str, col1: str, file_path2: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Independent T-Test. [DATA]
    
    [RAG Context]
    Tests whether the means of two independent samples are significantly different.
    
    How to Use:
    - If p-value < 0.05: The difference between the two groups is statistically significant.
    - Assumes the data follows a normal distribution (check with 'test_shapiro').
    
    Keywords: mean comparison, group difference, hypothesis testing, p-value.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_ttest_ind(file_path1, col1, file_path2, col2)

@mcp.tool()
def test_mannwhitneyu(file_path1: str, col1: str, file_path2: str, col2: str) -> Dict[str, Any]:
    """PERFORMS the Mann-Whitney U test for non-parametric comparison of two independent groups. [DATA]
    
    [RAG Context]
    A robust "Distribution Comparison Super Tool" that serves as the non-parametric alternative to the Independent T-test. In real-world business data, variables are often skewed, have extreme outliers, or do not follow a perfect "Bell Curve" (normal distribution). The Mann-Whitney U test handles these situations by comparing the *ranks* of the data rather than the raw means, making it far more reliable for "High-Noise Environments" and "Ordinal Data" (e.g., comparing user satisfaction scores or transaction rankings). It is the mandatory tool for "Scientific Audit" when the strict assumptions of parametric statistics are violated.
    
    How to Use:
    - 'file_path1', 'col1': The first data group.
    - 'file_path2', 'col2': The second data group.
    - If the resulting 'p-value' is < 0.05, you can conclude that there is a significant difference between the distributions of the two groups.
    
    Keywords: mann-whitney u, non-parametric test, distribution comparison, robust statistics, rank-based audit, significance testing.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_mannwhitneyu(file_path1, col1, file_path2, col2)

@mcp.tool()
def test_pearsonr(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """CALCULATES Pearson Correlation. [DATA]
    
    [RAG Context]
    Measures the linear relationship between two continuous variables.
    
    How to Use:
    - Returns 'r' (correlation coefficient) from -1 (perfect negative) to +1 (perfect positive).
    - Also returns 'p-value' (significance).
    
    Keywords: linear relationship, correlation strength, dependency check.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_pearsonr(file_path, col1, col2)

@mcp.tool()
def test_spearmanr(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """CALCULATES Spearman Correlation. [DATA]
    
    [RAG Context]
    Rank correlation coefficient.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_spearmanr(file_path, col1, col2)

@mcp.tool()
def test_shapiro(file_path: str, column: str) -> Dict[str, Any]:
    """PERFORMS a rigorous Shapiro-Wilk Normality Test to verify if a dataset follows a Gaussian distribution. [DATA]
    
    [RAG Context]
    The definitive "Model Assumption Super Tool" for statistical data hygiene. Most power-user analytical tools—such as Pearson Correlation, T-tests, and OLS Regression—assume that the underlying data is normally distributed ("Bell Curve"). If this assumption is violated, the results of those tools become untrustworthy. This tool provides the "Scientific Gatekeeping" required to decide if you should use parametric tests or if you must switch to robust, non-parametric alternatives (like Spearman or Mann-Whitney). It is a mandatory requirement for any "Self-Correcting Data Pipeline" within the Kea ecosystem.
    
    How to Use:
    - 'column': The numerical field to investigate.
    - Result includes a 'p-value'.
    - If p > 0.05: The data is likely normal (Gaussian), and you can proceed with standard statistical models.
    - If p < 0.05: The data is significantly non-normal, and you should use non-parametric tools for more accurate results.
    
    Keywords: shapiro-wilk test, normality check, gaussian distribution, statistical audit, model assumptions, data distribution test.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_shapiro(file_path, column)

@mcp.tool()
def test_chi2_contingency(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """PERFORMS a Chi-Square test of independence to identify relationships between two categorical variables. [DATA]
    
    [RAG Context]
    A powerful "Categorical Interaction Super Tool" used to discover hidden dependencies in non-numeric data. While correlation tools handle numbers, the Chi-Square test answers questions like: "Is 'Customer Feedback Level' dependent on 'Subscription Tier'?" or "Is 'Project Success' related to a specific 'Regional Manager'?" It compares the observed frequency of occurrences against an expected distribution. It is the mandatory tool for "Demographic Sentiment Analysis" and "Operational Dependency Audits," allowing the AI to prove relationships that exist in qualitative labels.
    
    How to Use:
    - 'col1', 'col2': Specify two categorical headers (e.g., 'Department' and 'Outcome_Status').
    - Result includes the Chi-Square statistic and a 'p-value'.
    - A significant p-value (< 0.05) indicates that the two variables are NOT independent—meaning a change in one is likely associated with the state of the other.
    
    Keywords: chi-square test, contingency table, categorical dependency, independence test, relationship audit, qualitative analysis.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_chi2_contingency(file_path, col1, col2)

# ==========================================
# 5. Time Series Analysis (New)
# ==========================================
@mcp.tool()
def model_ols_regression(file_path: str, formula: str) -> Dict[str, Any]:
    """EXECUTES an Ordinary Least Squares (OLS) Linear Regression for predictive modeling and impact analysis. [DATA]
    
    [RAG Context]
    An elite "Causal Discovery Super Tool" for quantifying the relationship between a target outcome and multiple independent predictors. Using a sophisticated formula-based syntax, it builds a mathematical model (e.g., `Revenue ~ Marketing_Spend + Employee_Count + Seasonal_Factor`) to determine exactly how much each variable contributes to the final result. It doesn't just predict; it provides "Coefficient P-Values" and "R-Squared" metrics, allowing the system to statistically prove which factors are truly driving performance. It is the mandatory tool for "Attribution Modeling" and "Strategic Forecasting."
    
    How to Use:
    - 'formula': Use R-style notation (e.g., 'Target ~ Var1 + Var2').
    - Returns a comprehensive summary including coefficients (the 'impact' of each variable), p-values (the 'confidence' in that impact), and the R-Squared (the 'overall accuracy' of the model).
    - Perfect for answering: "If we increase marketing spend by 10%, what is the expected revenue lift?"
    
    Keywords: ols regression, linear model, causal analysis, attribution, predictive forecasting, r-squared summary.
    """
    from mcp_servers.analysis_server.tools import time_series_ops
    return time_series_ops.model_ols_regression(file_path, formula)

@mcp.tool()
def model_arima(file_path: str, value_col: str, order: List[int], date_col: str = None) -> Dict[str, Any]:
    """RUNS ARIMA Model. [DATA]
    
    [RAG Context]
    Applies the AutoRegressive Integrated Moving Average model for time series forecasting.
    
    How to Use:
    - 'order': List of 3 ints (p, d, q). 
    - Automatically handles data loading and model fitting.
    
    Keywords: time series prediction, arima forecasting, lag model.
    """
    from mcp_servers.analysis_server.tools import time_series_ops
    return time_series_ops.model_arima(file_path, value_col, order, date_col)

@mcp.tool()
def test_adfuller(file_path: str, value_col: str) -> Dict[str, Any]:
    """PERFORMS the Augmented Dickey-Fuller (ADF) test to verify the stationarity of a time-series. [DATA]
    
    [RAG Context]
    A critical "Time-Series Integrity Super Tool" for forecasting and sequence analysis. Before applying predictive models like ARIMA, the system *must* know if the data is "Stationary"—meaning its statistical properties (mean, variance) remain constant over time. If a time-series has a strong trend or seasonality, it is non-stationary, and many standard forecasting algorithms will fail. This tool provides the "Mathematical Verification" needed to decide if the data requires "Differencing" or "Detrending" first. It is a mandatory requirement for any "Enterprise Forecasting Pipeline."
    
    How to Use:
    - 'value_col': The numerical sequence to test for stationarity.
    - Result includes the ADF statistic and a 'p-value'.
    - If p < 0.05: The series is stationary (ready for direct modeling).
    - If p > 0.05: The series is non-stationary (requires pre-processing like 'signal_detrend' or differencing).
    
    Keywords: adf test, stationarity discovery, time-series audit, forecasting preparation, unit root test, sequence analysis.
    """
    from mcp_servers.analysis_server.tools import time_series_ops
    return time_series_ops.test_adfuller(file_path, value_col)

# ==========================================
# 8. Advanced Visualizations (New)
# ==========================================
@mcp.tool()
def plot_kde(file_path: str, x: str) -> str:
    """PLOTS KDE Density. [ACTION]
    
    [RAG Context]
    Kernel Density Estimation.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_kde(file_path, x)

@mcp.tool()
def plot_joint(file_path: str, x: str, y: str, kind: str = "scatter") -> str:
    """GENERATES a sophisticated Joint Plot to visualize bivariate relationships alongside univariant distributions. [ACTION]
    
    [RAG Context]
    An elite "Multi-Perspective Visualization Super Tool" that provides a 3-in-1 view of data interactions. The central plot shows the direct relationship between two variables (e.g., using scatter or hex bins), while the marginal axes simultaneously display the individual histograms or KDE density for each variable. This allows the system to identify not just *how* two variables correlate, but also where the majority of their individual data points reside. it is the mandatory tool for "Deep Relationship Audits," providing the most complete two-dimensional snapshot possible of the interaction between two features.
    
    How to Use:
    - 'x', 'y': The two numerical columns to compare.
    - 'kind': Choose 'scatter' for raw points, 'reg' to include a regression line, or 'hex' to handle large datasets where points might overlap.
    - High-density visual output optimized for identifying outliers and multimodal distribution peaks in a single dashboard.
    
    Keywords: joint plot, bivariate visualization, marginal distribution, relationship summary, data interaction, composite viz.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_joint(file_path, x, y, kind)

@mcp.tool()
def plot_3d_scatter(file_path: str, x: str, y: str, z: str) -> str:
    """RENDERS a dynamic 3D Scatter Plot to visualize interactions between three numerical variables. [ACTION]
    
    [RAG Context]
    A high-level "Spatial Interaction Super Tool" designed to break the limitations of two-dimensional analysis. In complex corporate systems, performance is often driven by more than just two factors; this tool allows the AI to visualize the "Data Cloud" in three dimensions (e.g., "Profitability" vs "Ad Spend" vs "Market Size"). This reveals structural patterns—such as planes, clusters, or voids in the data space—that are mathematically invisible on a 2D plane. It is the mandatory tool for "Complex Multivariate Auditing" and identifying higher-order relationships in business telemetry.
    
    How to Use:
    - Provide three numerical columns ('x', 'y', 'z').
    - The tool generates a 3D perspective projection, allowing for the visual discovery of multi-dimensional clusters and seasonal trends that span across multiple independent axes.
    
    Keywords: 3d scatter, spatial visualization, multivariate interaction, data cloud, higher-order patterns, 3d analytics.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_3d_scatter(file_path, x, y, z)

@mcp.tool()
def plot_hexbin(file_path: str, x: str, y: str) -> str:
    """PLOTS Hexbin Plot. [ACTION]
    
    [RAG Context]
    Bivariate histogram with hexagonal bins.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_hexbin(file_path, x, y)

# ==========================================
# 9. Advanced Statistics (New)
# ==========================================
@mcp.tool()
def stat_anova_oneway(file_path: str, formula: str) -> Dict[str, Any]:
    """EXECUTES a One-Way ANOVA (Analysis of Variance) to compare means across multiple categorical groups. [DATA]
    
    [RAG Context]
    An authoritative "Group Differentiation Super Tool" used to determine if there are any statistically significant differences between the means of three or more independent groups. While a T-test is limited to two groups, ANOVA can compare many groups simultaneously (e.g., "Is average production output different between Plant A, Plant B, and Plant C?"). It calculates the F-statistic to see if the variation between group means is larger than the variation within the groups. It is the mandatory tool for "Operational Benchmarking" and "A/B/C Testing."
    
    How to Use:
    - 'formula': Use the syntax 'Numeric_Metric ~ Categorical_Feature' (e.g., 'Revenue ~ Region').
    - If the 'p-value' (PR(>F)) is < 0.05, it indicates that at least one group mean is significantly different from the others.
    - Essential for identifying which departments, regions, or product lines are statistical outliers in performance.
    
    Keywords: anova, analysis of variance, group comparison, f-test, operational benchmark, multivariate mean test.
    """
    from mcp_servers.analysis_server.tools import advanced_stats_ops
    return advanced_stats_ops.stat_anova_oneway(file_path, formula)

@mcp.tool()
def stat_logit(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS Logistic Regression. [DATA]
    
    [RAG Context]
    Logit model for binary outcomes.
    """
    from mcp_servers.analysis_server.tools import advanced_stats_ops
    return advanced_stats_ops.stat_logit(file_path, formula)

@mcp.tool()
def stat_glm(file_path: str, formula: str, family: str = 'Gaussian') -> Dict[str, Any]:
    """RUNS GLM. [DATA]
    
    [RAG Context]
    Generalized Linear Model.
    """
    from mcp_servers.analysis_server.tools import advanced_stats_ops
    return advanced_stats_ops.stat_glm(file_path, formula)

# ==========================================
# 10. Signal Processing (New)
# ==========================================
@mcp.tool()
def signal_fft(file_path: str, column: str) -> Dict[str, Any]:
    """COMPUTES FFT. [DATA]
    
    [RAG Context]
    Fast Fourier Transform.
    """
    from mcp_servers.analysis_server.tools import signal_ops
    return signal_ops.signal_fft(file_path, column)

@mcp.tool()
def signal_detrend(file_path: str, column: str) -> str:
    """REMOVES linear trend. [ACTION]
    
    [RAG Context]
    Signal detrending.
    """
    from mcp_servers.analysis_server.tools import signal_ops
    return signal_ops.signal_detrend(file_path, column)

@mcp.tool()
def signal_resample(file_path: str, column: str, num_samples: int) -> str:
    """RESAMPLES signal. [ACTION]
    
    [RAG Context]
    Changes sampling rate of signal.
    """
    from mcp_servers.analysis_server.tools import signal_ops
    return signal_ops.signal_resample(file_path, column, num_samples)

if __name__ == "__main__":
    mcp.run()

class AnalysisServer:

    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
            return list(self.mcp._tool_manager._tools.values())
        return []

