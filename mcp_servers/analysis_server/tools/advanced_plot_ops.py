import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import structlog
from typing import Dict, List, Any, Optional

logger = structlog.get_logger()

def _save_plot(output_path: str) -> str:
    try:
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return f"Plot saved to {output_path}"
    except Exception as e:
        plt.close()
        return f"Error plotting: {e}"

def _load(file_path):
    return pd.read_csv(file_path)

def plot_kde(file_path: str, x: str, shade: bool = True, output_path: str="kde.png") -> str:
    """PLOTS KDE Density. [ACTION]"""
    try:
        df = _load(file_path)
        plt.figure(figsize=(10, 6))
        sns.kdeplot(data=df, x=x, fill=shade)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_rug(file_path: str, x: str, output_path: str="rug.png") -> str:
    """PLOTS Rug Plot. [ACTION]"""
    try:
        df = _load(file_path)
        plt.figure(figsize=(10, 2))
        sns.rugplot(data=df, x=x)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_strip(file_path: str, x: str, y: str, output_path: str="strip.png") -> str:
    """PLOTS Strip Plot. [ACTION]"""
    try:
        df = _load(file_path)
        plt.figure(figsize=(10, 6))
        sns.stripplot(data=df, x=x, y=y)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_swarm(file_path: str, x: str, y: str, output_path: str="swarm.png") -> str:
    """PLOTS Swarm Plot. [ACTION]"""
    try:
        df = _load(file_path)
        plt.figure(figsize=(10, 6))
        sns.swarmplot(data=df, x=x, y=y)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_joint(file_path: str, x: str, y: str, kind: str = "scatter", output_path: str="joint.png") -> str:
    """PLOTS Joint Plot. [ACTION]"""
    try:
        df = _load(file_path)
        g = sns.jointplot(data=df, x=x, y=y, kind=kind)
        g.savefig(output_path)
        return f"Saved to {output_path}"
    except Exception as e:
        return f"Error: {e}"

def plot_hexbin(file_path: str, x: str, y: str, gridsize: int = 20, output_path: str="hexbin.png") -> str:
    """PLOTS Hexbin Plot. [ACTION]"""
    try:
        df = _load(file_path)
        g = sns.jointplot(data=df, x=x, y=y, kind="hex", gridsize=gridsize)
        g.savefig(output_path)
        return f"Saved to {output_path}"
    except Exception as e:
        return f"Error: {e}"

def plot_ecdf(file_path: str, x: str, output_path: str="ecdf.png") -> str:
    """PLOTS ECDF Plot. [ACTION]"""
    try:
        df = _load(file_path)
        plt.figure(figsize=(10, 6))
        sns.ecdfplot(data=df, x=x)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_reg(file_path: str, x: str, y: str, output_path: str="reg.png") -> str:
    """PLOTS Regression Plot. [ACTION]"""
    try:
        df = _load(file_path)
        plt.figure(figsize=(10, 6))
        sns.regplot(data=df, x=x, y=y)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_resid(file_path: str, x: str, y: str, output_path: str="resid.png") -> str:
    """PLOTS Residual Plot. [ACTION]"""
    try:
        df = _load(file_path)
        plt.figure(figsize=(10, 6))
        sns.residplot(data=df, x=x, y=y)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"

def plot_3d_scatter(file_path: str, x: str, y: str, z: str, output_path: str="scatter3d.png") -> str:
    """PLOTS 3D Scatter. [ACTION]"""
    try:
        df = _load(file_path)
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(df[x], df[y], df[z])
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_zlabel(z)
        return _save_plot(output_path)
    except Exception as e:
        return f"Error: {e}"
