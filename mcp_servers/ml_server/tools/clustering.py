import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score
from mcp_servers.ml_server.tools.utils import load_dataframe
from typing import Union, Dict, List, Any

async def clustering(data_url: str = None, data: Union[Dict, List] = None, n_clusters: Any = 3, method: str = "kmeans") -> str:
    """Perform clustering."""
    try:
        df = load_dataframe(data_url, data)
        
        # Prepare numeric data
        le = LabelEncoder()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = le.fit_transform(df[col].astype(str))
        
        X = df.fillna(df.median())
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        result = f"# 🎯 Clustering Results ({method})\n\n"
        
        if method == "kmeans":
            if n_clusters == "auto":
                # Find optimal k using elbow method
                scores = []
                for k in range(2, 11):
                    km = KMeans(n_clusters=k, random_state=42, n_init=10)
                    km.fit(X_scaled)
                    scores.append(km.inertia_)
                n_clusters = 3  # Default fallback
            
            model = KMeans(n_clusters=int(n_clusters), random_state=42, n_init=10)
            labels = model.fit_predict(X_scaled)
            
        elif method == "dbscan":
            model = DBSCAN(eps=0.5, min_samples=5)
            labels = model.fit_predict(X_scaled)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        silhouette = silhouette_score(X_scaled, labels) if len(set(labels)) > 1 else 0
        
        result += f"**Clusters Found**: {n_clusters}\n"
        result += f"**Silhouette Score**: {silhouette:.4f}\n\n"
        
        result += "## Cluster Sizes\n\n"
        cluster_counts = pd.Series(labels).value_counts().sort_index()
        for cluster, count in cluster_counts.items():
            pct = count / len(labels) * 100
            result += f"- Cluster {cluster}: {count} ({pct:.1f}%)\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
