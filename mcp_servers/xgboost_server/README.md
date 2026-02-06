# 🔌 Xgboost Server

The `xgboost_server` is an MCP server providing tools for **Xgboost Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `xgb_classifier` | Execute xgb classifier operation | `X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.3, max_depth: int = 6, objective: str = 'binary:logistic', sample_weight: Optional[VectorInput] = None` |
| `xgb_regressor` | Execute xgb regressor operation | `X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.3, max_depth: int = 6, objective: str = 'reg:squarederror', sample_weight: Optional[VectorInput] = None` |
| `xgb_ranker` | Execute xgb ranker operation | `X: DataInput, y: VectorInput, group: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1, objective: str = 'rank:pairwise'` |
| `xgb_rf_classifier` | Execute xgb rf classifier operation | `X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6` |
| `xgb_rf_regressor` | Execute xgb rf regressor operation | `X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6` |
| `train_booster` | Execute train booster operation | `X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, weight: Optional[VectorInput] = None` |
| `cv_booster` | Execute cv booster operation | `X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, nfold: int = 3, stratified: bool = False, metrics: List[str] = ['rmse'], seed: int = 0` |
| `booster_predict` | Execute booster predict operation | `model: str, X: DataInput` |
| `booster_save` | Execute booster save operation | `model: str, format: str = 'json'` |
| `booster_attributes` | Execute booster attributes operation | `model: str` |
| `get_feature_importance` | Execute get feature importance operation | `model: str, importance_type: str = 'weight'` |
| `get_trees` | Execute get trees operation | `model: str` |
| `auto_xgboost_clf` | Execute auto xgboost clf operation | `X: DataInput, y: VectorInput, n_iter: int = 10, cv: int = 3, scoring: str = 'accuracy'` |
| `auto_xgboost_reg` | Execute auto xgboost reg operation | `X: DataInput, y: VectorInput, n_iter: int = 10, cv: int = 3, scoring: str = 'neg_mean_squared_error'` |

## 📦 Dependencies

The following packages are required:
- `xgboost`
- `scikit-learn`
- `numpy`
- `pandas`
- `joblib`
- `scipy`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.xgboost_server.server
```
