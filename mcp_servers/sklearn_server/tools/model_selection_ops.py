from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, DataInput, VectorInput
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score, confusion_matrix, classification_report,
    mean_squared_error, r2_score, mean_absolute_error
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
# We need to instantate models dynamically for GridSearchCV, simplified approach:
# Only basic common models supported for GridSearch via this tool for now.

import pandas as pd
from typing import Dict, Any, List, Optional, Union

async def split_data(X: DataInput, y: Optional[VectorInput] = None, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
    """Split data into train and test sets."""
    X_df = parse_data(X)
    if y:
        y_vec = parse_vector(y)
        X_train, X_test, y_train, y_test = train_test_split(X_df, y_vec, test_size=test_size, random_state=random_state)
        return to_serializable({
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test
        })
    else:
        X_train, X_test = train_test_split(X_df, test_size=test_size, random_state=random_state)
        return to_serializable({
            "X_train": X_train,
            "X_test": X_test
        })

async def calculate_metrics(y_true: VectorInput, y_pred: VectorInput, task: str = 'classification') -> Dict[str, Any]:
    """Calculate evaluation metrics."""
    yt = parse_vector(y_true)
    yp = parse_vector(y_pred)
    
    if task == 'classification':
        return to_serializable({
            "accuracy": accuracy_score(yt, yp),
            "f1_macro": f1_score(yt, yp, average='macro'),
            "confusion_matrix": confusion_matrix(yt, yp).tolist(),
            "report": classification_report(yt, yp, output_dict=True)
        })
    elif task == 'regression':
        return to_serializable({
            "mse": mean_squared_error(yt, yp),
            "rmse": mean_squared_error(yt, yp, squared=False),
            "mae": mean_absolute_error(yt, yp),
            "r2": r2_score(yt, yp)
        })
    return {"error": "Unknown task type"}

# GridSearch simplified: Only supports optimizing a few fixed estimators via string 
# because passing estimator objects is hard in stateless mode. 
# Real dynamic grid search fits better in "super_ops" where we instantiate locally.
