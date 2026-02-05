import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, r2_score
from mcp_servers.ml_server.tools.utils import load_dataframe

async def auto_ml(data_url: str, target_column: str, task_type: str = "auto", test_size: float = 0.2) -> str:
    """Automatic ML model selection and training."""
    try:
        df = pd.read_csv(data_url)
        
        result = "# 🤖 AutoML Results\n\n"
        
        # Prepare data
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Detect task type
        if task_type == "auto":
            if y.dtype == 'object' or y.nunique() < 10:
                task_type = "classification"
            else:
                task_type = "regression"
        
        result += f"**Task**: {task_type}\n"
        result += f"**Features**: {X.shape[1]}\n"
        result += f"**Samples**: {X.shape[0]}\n\n"
        
        # Encode categorical features
        le = LabelEncoder()
        for col in X.select_dtypes(include=['object']).columns:
            X[col] = le.fit_transform(X[col].astype(str))
        
        # Encode target if classification
        if task_type == "classification" and y.dtype == 'object':
            y = le.fit_transform(y)
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )
        
        # Model candidates
        if task_type == "classification":
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            
            models = {
                "Logistic Regression": LogisticRegression(max_iter=1000),
                "Random Forest": RandomForestClassifier(n_estimators=100),
                "Gradient Boosting": GradientBoostingClassifier(n_estimators=100),
            }
        else:
            from sklearn.linear_model import LinearRegression, Ridge
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            
            models = {
                "Linear Regression": LinearRegression(),
                "Ridge": Ridge(),
                "Random Forest": RandomForestRegressor(n_estimators=100),
                "Gradient Boosting": GradientBoostingRegressor(n_estimators=100),
            }
        
        # Train and evaluate
        result += "## Model Comparison\n\n"
        result += "| Model | CV Score | Test Score |\n|-------|----------|------------|\n"
        
        best_model = None
        best_score = -np.inf
        
        for name, model in models.items():
            try:
                # Cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                cv_mean = cv_scores.mean()
                
                # Test set
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                if task_type == "classification":
                    test_score = accuracy_score(y_test, y_pred)
                else:
                    test_score = r2_score(y_test, y_pred)
                
                result += f"| {name} | {cv_mean:.4f} | {test_score:.4f} |\n"
                
                if test_score > best_score:
                    best_score = test_score
                    best_model = name
                    
            except Exception as e:
                result += f"| {name} | Error | {str(e)[:20]} |\n"
        
        result += f"\n## Best Model\n\n"
        result += f"🏆 **{best_model}** with test score: {best_score:.4f}\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
