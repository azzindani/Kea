import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from mcp_servers.ml_server.tools.utils import load_dataframe
from typing import Union, Dict, List

async def anomaly_detection(data_url: str = None, data: Union[Dict, List] = None, method: str = "isolation_forest", contamination: float = 0.1) -> str:
    """Detect anomalies."""
    try:
        df = load_dataframe(data_url, data)
        
        # Prepare numeric data
        le = LabelEncoder()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = le.fit_transform(df[col].astype(str))
        
        X = df.fillna(df.median())
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        result = f"# 🚨 Anomaly Detection ({method})\n\n"
        
        if method == "isolation_forest":
            model = IsolationForest(contamination=contamination, random_state=42)
            predictions = model.fit_predict(X_scaled)
            
        elif method == "zscore":
            from scipy import stats
            z_scores = np.abs(stats.zscore(X_scaled))
            predictions = np.where(np.any(z_scores > 3, axis=1), -1, 1)
        
        anomalies = (predictions == -1).sum()
        normal = (predictions == 1).sum()
        
        result += f"**Normal**: {normal} ({normal/len(predictions)*100:.1f}%)\n"
        result += f"**Anomalies**: {anomalies} ({anomalies/len(predictions)*100:.1f}%)\n\n"
        
        # Show anomaly examples
        if anomalies > 0:
            result += "## Anomaly Examples\n\n"
            anomaly_idx = np.where(predictions == -1)[0][:5]
            result += "```\n"
            result += df.iloc[anomaly_idx].to_string()
            result += "\n```\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
