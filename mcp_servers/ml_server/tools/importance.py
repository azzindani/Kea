import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from mcp_servers.ml_server.tools.utils import load_dataframe

async def feature_importance(data_url: str, target_column: str, method: str = "tree") -> str:
    """Analyze feature importance."""
    try:
        df = pd.read_csv(data_url)
        
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Encode
        le = LabelEncoder()
        for col in X.select_dtypes(include=['object']).columns:
            X[col] = le.fit_transform(X[col].astype(str))
        
        if y.dtype == 'object':
            y = le.fit_transform(y)
            is_classification = True
        else:
            is_classification = y.nunique() < 10
        
        X = X.fillna(X.median())
        
        result = "# 📊 Feature Importance\n\n"
        
        if method == "tree":
            if is_classification:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            model.fit(X, y)
            
            importance = pd.DataFrame({
                'feature': X.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            result += "## Tree-based Importance\n\n"
            result += "| Rank | Feature | Importance |\n|------|---------|------------|\n"
            
            for i, row in importance.head(15).iterrows():
                bar = "█" * int(row['importance'] * 20)
                result += f"| {importance.index.get_loc(i)+1} | {row['feature']} | {row['importance']:.4f} {bar} |\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
