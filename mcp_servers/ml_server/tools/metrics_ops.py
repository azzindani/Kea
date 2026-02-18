from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score, explained_variance_score,
    max_error, median_absolute_error
)
import pandas as pd
import numpy as np
import structlog
from typing import Dict, Any, List, Union

logger = structlog.get_logger()

# Helpers to load data if passed as URL, else assume list?
# MCP tools pass primitive types. Lists of numbers are simplest.

# --- Classification Metrics ---
def calculate_accuracy(y_true: List[int], y_pred: List[int]) -> float:
    """CALCULATES Accuracy Score. [DATA]"""
    return float(accuracy_score(y_true, y_pred))

def calculate_precision(y_true: List[int], y_pred: List[int], average: str = 'binary') -> float:
    """CALCULATES Precision Score. [DATA]"""
    return float(precision_score(y_true, y_pred, average=average, zero_division=0))

def calculate_recall(y_true: List[int], y_pred: List[int], average: str = 'binary') -> float:
    """CALCULATES Recall Score. [DATA]"""
    return float(recall_score(y_true, y_pred, average=average, zero_division=0))

def calculate_f1(y_true: List[int], y_pred: List[int], average: str = 'binary') -> float:
    """CALCULATES F1 Score. [DATA]"""
    return float(f1_score(y_true, y_pred, average=average, zero_division=0))

def calculate_roc_auc(y_true: List[int], y_score: List[float], multi_class: str = 'raise') -> float:
    """CALCULATES ROC AUC Score. [DATA]"""
    try:
        return float(roc_auc_score(y_true, y_score, multi_class=multi_class))
    except:
        return -1.0

# --- Regression Metrics ---
def calculate_mse(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Mean Squared Error. [DATA]"""
    return float(mean_squared_error(y_true, y_pred))

def calculate_rmse(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Root Mean Squared Error. [DATA]"""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def calculate_mae(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Mean Absolute Error. [DATA]"""
    return float(mean_absolute_error(y_true, y_pred))

def calculate_r2(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES R2 Score. [DATA]"""
    return float(r2_score(y_true, y_pred))

def calculate_explained_variance(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Explained Variance Score. [DATA]"""
    return float(explained_variance_score(y_true, y_pred))

def calculate_max_error(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Max Error. [DATA]"""
    return float(max_error(y_true, y_pred))

def calculate_median_absolute_error(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Median Absolute Error. [DATA]"""
    return float(median_absolute_error(y_true, y_pred))
