import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import structlog
from typing import List, Optional, Union

logger = structlog.get_logger()

# Set style suitable for dark themes or modern look
sns.set_theme(style="whitegrid")

def _save_plot(output_path: str) -> str:
    try:
        if not output_path:
             # Return base64 if no path? MCP usually expects files or text. 
             # Let's save to a temp path and simple return success message.
             # Or if output_path is provided, use it.
             return "Please provide an output_path."
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close() # Close figure to free memory
        return f"Plot saved to {output_path}"
    except Exception as e:
        plt.close()
        return f"Plotting failed: {e}"


def _run_plot(plot_func, file_path: str, output_path: str, **kwargs) -> str:
    """Helper to run plotting with error handling."""
    try:
        df = pd.read_csv(file_path)
        plt.figure(figsize=(10, 6))
        plot_func(df, **kwargs)
        return _save_plot(output_path)
    except Exception as e:
        plt.close() # Ensure cleanup
        logger.error(f"Plotting failed: {e}")
        return f"Error: Plotting failed ({str(e)})"

def plot_scatter(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "scatter.png") -> str:
    """PLOTS Scatter chart. [ACTION]"""
    return _run_plot(lambda df, **kw: sns.scatterplot(data=df, x=x, y=y, hue=hue), file_path, output_path)

def plot_line(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "line.png") -> str:
    """PLOTS Line chart. [ACTION]"""
    return _run_plot(lambda df, **kw: sns.lineplot(data=df, x=x, y=y, hue=hue), file_path, output_path)

def plot_bar(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "bar.png") -> str:
    """PLOTS Bar chart. [ACTION]"""
    return _run_plot(lambda df, **kw: sns.barplot(data=df, x=x, y=y, hue=hue), file_path, output_path)

def plot_hist(file_path: str, x: str, bins: int = 20, hue: Optional[str] = None, output_path: str = "hist.png") -> str:
    """PLOTS Histogram/Distribution. [ACTION]"""
    return _run_plot(lambda df, **kw: sns.histplot(data=df, x=x, bins=bins, hue=hue, kde=True), file_path, output_path)

def plot_box(file_path: str, x: str, y: str, output_path: str = "box.png") -> str:
    """PLOTS Box plot. [ACTION]"""
    return _run_plot(lambda df, **kw: sns.boxplot(data=df, x=x, y=y), file_path, output_path)

def plot_violin(file_path: str, x: str, y: str, output_path: str = "violin.png") -> str:
    """PLOTS Violin plot. [ACTION]"""
    return _run_plot(lambda df, **kw: sns.violinplot(data=df, x=x, y=y), file_path, output_path)

def plot_heatmap(file_path: str, output_path: str = "heatmap.png") -> str:
    """PLOTS Correlation Heatmap. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        numeric_df = df.select_dtypes(include=['number'])
        plt.figure(figsize=(12, 10))
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f")
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_pairplot(file_path: str, hue: Optional[str] = None, output_path: str = "pairplot.png") -> str:
    """PLOTS Pairplot (Scatter matrix). [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        numeric_cols = df.select_dtypes(include=['number']).columns[:6]
        subset_df = df[numeric_cols].copy()
        if hue and hue in df.columns:
            subset_df[hue] = df[hue]
        
        g = sns.pairplot(subset_df, hue=hue)
        g.savefig(output_path)
        return f"Pairplot saved to {output_path}"
    except Exception as e:
        return f"Error: {e}"

def plot_confusion_matrix(file_path: str, y_true: str, y_pred: str, output_path: str="cm.png") -> str:
    """PLOTS Confusion Matrix. [ACTION]"""
    try:
        from sklearn.metrics import confusion_matrix
        df = pd.read_csv(file_path)
        cm = confusion_matrix(df[y_true], df[y_pred])
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        return _save_plot(output_path)
    except Exception as e:
         return f"Error: {e}"
