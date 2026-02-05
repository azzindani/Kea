from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import pandas as pd
from typing import Dict, Any, List, Optional

async def automl_classifier(X: DataInput, y: VectorInput) -> Dict[str, Any]:
    """
    Super Tool: Train multiple classifiers and return the best one based on CV score.
    """
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForest": RandomForestClassifier(random_state=42),
        "SVM": SVC(probability=True),
        "GradientBoosting": GradientBoostingClassifier(random_state=42)
    }
    
    best_name = None
    best_score = -1
    best_model = None
    results = {}
    
    for name, model in models.items():
        # Quick CV check
        scores = cross_val_score(model, X_df, y_vec, cv=3)
        avg = scores.mean()
        results[name] = avg
        
        if avg > best_score:
            best_score = avg
            best_name = name
            best_model = model
            
    # Retrain best
    best_model.fit(X_df, y_vec)
    
    return to_serializable({
        "best_model_name": best_name,
        "best_cv_accuracy": best_score,
        "all_results": results,
        "model": serialize_model(best_model)
    })

async def pipeline_runner(X: DataInput, y: VectorInput, steps: List[str] = ['scaler', 'rf']) -> Dict[str, Any]:
    """
    Super Tool: Run a Pipeline (e.g., Scaler -> Model).
    Steps: 'scaler', 'pca', 'rf', 'svm', 'logreg'
    """
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    pipe_steps = []
    
    for step in steps:
        if step == 'scaler':
            pipe_steps.append(('scaler', StandardScaler()))
        elif step == 'rf':
             pipe_steps.append(('rf', RandomForestClassifier()))
        elif step == 'svm':
             pipe_steps.append(('svm', SVC()))
        elif step == 'logreg':
             pipe_steps.append(('logreg', LogisticRegression()))
             
    pipe = Pipeline(pipe_steps)
    pipe.fit(X_df, y_vec)
    score = pipe.score(X_df, y_vec)
    
    return to_serializable({
        "train_score": score,
        "model": serialize_model(pipe)
    })
