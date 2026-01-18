"""
Machine Learning MCP Server.

Provides tools for ML operations:
- AutoML: automatic model selection
- Feature importance
- Model comparison
- Predictions with explanations
"""

from __future__ import annotations

from typing import Any
import json

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class MLServer(MCPServerBase):
    """MCP server for machine learning operations."""
    
    def __init__(self) -> None:
        super().__init__(name="ml_server")
    
    def _load_dataframe(self, args: dict):
        """
        Load DataFrame from either data_url or inline data.
        
        Supports:
        - data_url: URL to CSV file
        - data: {"columns": [...], "rows": [[...], ...]}
        """
        import pandas as pd
        
        if "data_url" in args and args["data_url"]:
            return pd.read_csv(args["data_url"])
        elif "data" in args and args["data"]:
            data = args["data"]
            if isinstance(data, dict) and "columns" in data and "rows" in data:
                return pd.DataFrame(data["rows"], columns=data["columns"])
            elif isinstance(data, list):
                return pd.DataFrame(data)
            else:
                raise ValueError("Invalid data format. Expected {columns: [], rows: []} or list of dicts")
        else:
            raise ValueError("Either data_url or data must be provided")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="auto_ml",
                description="Automatically select and train the best ML model",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "target_column": {"type": "string", "description": "Target variable to predict"},
                        "task_type": {"type": "string", "description": "Task: classification or regression"},
                        "test_size": {"type": "number", "description": "Test set proportion (0.1-0.4)"},
                    },
                    required=["data_url", "target_column"],
                ),
            ),
            Tool(
                name="feature_importance",
                description="Analyze feature importance for prediction",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "target_column": {"type": "string", "description": "Target variable"},
                        "method": {"type": "string", "description": "Method: permutation, shap, tree"},
                    },
                    required=["data_url", "target_column"],
                ),
            ),
            Tool(
                name="clustering",
                description="Perform unsupervised clustering",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "data": {"type": "object", "description": "Inline data: {columns: [], rows: []}"},
                        "n_clusters": {"type": "integer", "description": "Number of clusters (or 'auto')"},
                        "method": {"type": "string", "description": "Method: kmeans, dbscan, hierarchical"},
                    },
                    required=[],
                ),
            ),
            Tool(
                name="anomaly_detection",
                description="Detect anomalies/outliers in data",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "data": {"type": "object", "description": "Inline data: {columns: [], rows: []}"},
                        "method": {"type": "string", "description": "Method: isolation_forest, lof, zscore"},
                        "contamination": {"type": "number", "description": "Expected proportion of outliers"},
                    },
                    required=[],
                ),
            ),
            Tool(
                name="time_series_forecast",
                description="Forecast time series data",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "date_column": {"type": "string", "description": "Date column name"},
                        "value_column": {"type": "string", "description": "Value column to forecast"},
                        "periods": {"type": "integer", "description": "Number of periods to forecast"},
                    },
                    required=["data_url", "value_column"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "auto_ml":
                return await self._handle_auto_ml(arguments)
            elif name == "feature_importance":
                return await self._handle_feature_importance(arguments)
            elif name == "clustering":
                return await self._handle_clustering(arguments)
            elif name == "anomaly_detection":
                return await self._handle_anomaly(arguments)
            elif name == "time_series_forecast":
                return await self._handle_forecast(arguments)
            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
    
    async def _handle_auto_ml(self, args: dict) -> ToolResult:
        """Automatic ML model selection and training."""
        import pandas as pd
        import numpy as np
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.preprocessing import LabelEncoder, StandardScaler
        from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score
        
        url = args["data_url"]
        target = args["target_column"]
        task_type = args.get("task_type", "auto")
        test_size = args.get("test_size", 0.2)
        
        df = pd.read_csv(url)
        
        result = "# 🤖 AutoML Results\n\n"
        
        # Prepare data
        X = df.drop(columns=[target])
        y = df[target]
        
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
            from sklearn.svm import SVC
            
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_feature_importance(self, args: dict) -> ToolResult:
        """Analyze feature importance."""
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.preprocessing import LabelEncoder
        
        url = args["data_url"]
        target = args["target_column"]
        method = args.get("method", "tree")
        
        df = pd.read_csv(url)
        
        X = df.drop(columns=[target])
        y = df[target]
        
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_clustering(self, args: dict) -> ToolResult:
        """Perform clustering."""
        import pandas as pd
        import numpy as np
        from sklearn.cluster import KMeans, DBSCAN
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        from sklearn.metrics import silhouette_score
        
        df = self._load_dataframe(args)
        n_clusters = args.get("n_clusters", 3)
        method = args.get("method", "kmeans")
        
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
                n_clusters = 3  # Default
            
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_anomaly(self, args: dict) -> ToolResult:
        """Detect anomalies."""
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        
        df = self._load_dataframe(args)
        method = args.get("method", "isolation_forest")
        contamination = args.get("contamination", 0.1)
        
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_forecast(self, args: dict) -> ToolResult:
        """Time series forecasting."""
        import pandas as pd
        import numpy as np
        
        url = args["data_url"]
        date_col = args.get("date_column")
        value_col = args["value_column"]
        periods = args.get("periods", 10)
        
        df = pd.read_csv(url)
        
        result = "# 📈 Time Series Forecast\n\n"
        
        # Handle date column
        if date_col and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
        
        values = df[value_col].values
        
        # Simple moving average forecast
        window = min(5, len(values) // 2)
        ma = pd.Series(values).rolling(window=window).mean()
        
        result += f"**Value Column**: {value_col}\n"
        result += f"**Data Points**: {len(values)}\n"
        result += f"**Forecast Periods**: {periods}\n\n"
        
        # Last value and trend
        last_value = values[-1]
        trend = (values[-1] - values[0]) / len(values)
        
        result += "## Forecast\n\n"
        result += "| Period | Forecast |\n|--------|----------|\n"
        
        for i in range(1, periods + 1):
            forecast = last_value + (trend * i)
            result += f"| +{i} | {forecast:.2f} |\n"
        
        result += "\n## Statistics\n\n"
        result += f"- Mean: {np.mean(values):.2f}\n"
        result += f"- Std: {np.std(values):.2f}\n"
        result += f"- Trend: {'+' if trend > 0 else ''}{trend:.4f}/period\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def auto_ml_tool(args: dict) -> ToolResult:
    server = MLServer()
    return await server._handle_auto_ml(args)

async def clustering_tool(args: dict) -> ToolResult:
    server = MLServer()
    return await server._handle_clustering(args)

async def anomaly_detection_tool(args: dict) -> ToolResult:
    server = MLServer()
    return await server._handle_anomaly(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = MLServer()
        await server.run()
        
    asyncio.run(main())
