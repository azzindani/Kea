from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
import pandas as pd
from typing import Dict, Any, List, Optional

async def _train_classifier(model, X, y):
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    model.fit(X_df, y_vec)
    
    # Basic metrics on train set? Or just return model?
    # Usually users want model + maybe score
    score = model.score(X_df, y_vec)
    
    return to_serializable({
        "train_accuracy": score,
        "classes": model.classes_.tolist() if hasattr(model, 'classes_') else None,
        "model": serialize_model(model) # Return base64 model
    })

async def logistic_regression(X: DataInput, y: VectorInput, C: float = 1.0, max_iter: int = 100) -> Dict[str, Any]:
    return await _train_classifier(LogisticRegression(C=C, max_iter=max_iter), X, y)

async def svc(X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf') -> Dict[str, Any]:
    return await _train_classifier(SVC(C=C, kernel=kernel, probability=True), X, y)

async def linear_svc(X: DataInput, y: VectorInput, C: float = 1.0) -> Dict[str, Any]:
    return await _train_classifier(LinearSVC(C=C), X, y)

async def decision_tree_clf(X: DataInput, y: VectorInput, max_depth: Optional[int] = None) -> Dict[str, Any]:
    return await _train_classifier(DecisionTreeClassifier(max_depth=max_depth), X, y)

async def knn_classifier(X: DataInput, y: VectorInput, n_neighbors: int = 5) -> Dict[str, Any]:
    return await _train_classifier(KNeighborsClassifier(n_neighbors=n_neighbors), X, y)

async def naive_bayes_gaussian(X: DataInput, y: VectorInput) -> Dict[str, Any]:
    return await _train_classifier(GaussianNB(), X, y)

async def mlp_classifier(X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]) -> Dict[str, Any]:
    return await _train_classifier(MLPClassifier(hidden_layer_sizes=tuple(hidden_layer_sizes)), X, y)
