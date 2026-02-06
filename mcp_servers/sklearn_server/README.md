# 🔌 Sklearn Server

The `sklearn_server` is an MCP server providing tools for **Sklearn Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `fit_transform_scaler` | Execute fit transform scaler operation | `data: DataInput, method: str = 'standard'` |
| `fit_transform_encoder` | Execute fit transform encoder operation | `data: DataInput, method: str = 'label', columns: Optional[List[str]] = None` |
| `impute_missing` | Execute impute missing operation | `data: DataInput, strategy: str = 'mean', fill_value: Optional[Any] = None` |
| `generate_features` | Execute generate features operation | `data: DataInput, method: str = 'poly', degree: int = 2` |
| `split_data` | Execute split data operation | `X: DataInput, y: Optional[VectorInput] = None, test_size: float = 0.2, random_state: int = 42` |
| `calculate_metrics` | Execute calculate metrics operation | `y_true: VectorInput, y_pred: VectorInput, task: str = 'classification'` |
| `logistic_regression` | Execute logistic regression operation | `X: DataInput, y: VectorInput, C: float = 1.0, max_iter: int = 100` |
| `svc` | Execute svc operation | `X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf'` |
| `linear_svc` | Execute linear svc operation | `X: DataInput, y: VectorInput, C: float = 1.0` |
| `decision_tree_clf` | Execute decision tree clf operation | `X: DataInput, y: VectorInput, max_depth: Optional[int] = None` |
| `knn_classifier` | Execute knn classifier operation | `X: DataInput, y: VectorInput, n_neighbors: int = 5` |
| `naive_bayes_gaussian` | Execute naive bayes gaussian operation | `X: DataInput, y: VectorInput` |
| `mlp_classifier` | Execute mlp classifier operation | `X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]` |
| `linear_regression` | Execute linear regression operation | `X: DataInput, y: VectorInput` |
| `ridge_regression` | Execute ridge regression operation | `X: DataInput, y: VectorInput, alpha: float = 1.0` |
| `lasso_regression` | Execute lasso regression operation | `X: DataInput, y: VectorInput, alpha: float = 1.0` |
| `elasticnet` | Execute elasticnet operation | `X: DataInput, y: VectorInput, alpha: float = 1.0, l1_ratio: float = 0.5` |
| `svr` | Execute svr operation | `X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf'` |
| `decision_tree_reg` | Execute decision tree reg operation | `X: DataInput, y: VectorInput, max_depth: Optional[int] = None` |
| `knn_regressor` | Execute knn regressor operation | `X: DataInput, y: VectorInput, n_neighbors: int = 5` |
| `mlp_regressor` | Execute mlp regressor operation | `X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]` |
| `kmeans` | Execute kmeans operation | `X: DataInput, n_clusters: int = 8` |
| `dbscan` | Execute dbscan operation | `X: DataInput, eps: float = 0.5, min_samples: int = 5` |
| `agglomerative` | Execute agglomerative operation | `X: DataInput, n_clusters: int = 2` |
| `spectral_clustering` | Execute spectral clustering operation | `X: DataInput, n_clusters: int = 8` |
| `pca` | Execute pca operation | `X: DataInput, n_components: int = 2` |
| `tsne` | Execute tsne operation | `X: DataInput, n_components: int = 2, perplexity: float = 30.0` |
| `nmf` | Execute nmf operation | `X: DataInput, n_components: int = 2` |
| `fast_ica` | Execute fast ica operation | `X: DataInput, n_components: int = 2` |
| `random_forest_clf` | Execute random forest clf operation | `X: DataInput, y: VectorInput, n_estimators: int = 100` |
| `random_forest_reg` | Execute random forest reg operation | `X: DataInput, y: VectorInput, n_estimators: int = 100` |
| `gradient_boosting_clf` | Execute gradient boosting clf operation | `X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1` |
| `gradient_boosting_reg` | Execute gradient boosting reg operation | `X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1` |
| `adaboost_clf` | Execute adaboost clf operation | `X: DataInput, y: VectorInput, n_estimators: int = 50` |
| `select_k_best` | Execute select k best operation | `X: DataInput, y: VectorInput, k: int = 10, score_func: str = 'f_classif'` |
| `select_percentile` | Execute select percentile operation | `X: DataInput, y: VectorInput, percentile: int = 10, score_func: str = 'f_classif'` |
| `rfe` | Execute rfe operation | `X: DataInput, y: VectorInput, n_features_to_select: int = 5, estimator_type: str = 'random_forest_clf'` |
| `variance_threshold` | Execute variance threshold operation | `X: DataInput, threshold: float = 0.0` |
| `isomap` | Execute isomap operation | `X: DataInput, n_components: int = 2, n_neighbors: int = 5` |
| `lle` | Execute lle operation | `X: DataInput, n_components: int = 2, n_neighbors: int = 5, method: str = 'standard'` |
| `mds` | Execute mds operation | `X: DataInput, n_components: int = 2, metric: bool = True` |
| `spectral_embedding` | Execute spectral embedding operation | `X: DataInput, n_components: int = 2` |
| `gaussian_process_clf` | Execute gaussian process clf operation | `X: DataInput, y: VectorInput` |
| `gaussian_process_reg` | Execute gaussian process reg operation | `X: DataInput, y: VectorInput` |
| `pls_regression` | Execute pls regression operation | `X: DataInput, Y: DataInput, n_components: int = 2` |
| `cca` | Execute cca operation | `X: DataInput, Y: DataInput, n_components: int = 2` |
| `label_propagation` | Execute label propagation operation | `X: DataInput, y: VectorInput, kernel: str = 'rbf'` |
| `label_spreading` | Execute label spreading operation | `X: DataInput, y: VectorInput, kernel: str = 'rbf', alpha: float = 0.2` |
| `self_training` | Execute self training operation | `X: DataInput, y: VectorInput` |
| `automl_classifier` | Execute automl classifier operation | `X: DataInput, y: VectorInput` |
| `pipeline_runner` | Execute pipeline runner operation | `X: DataInput, y: VectorInput, steps: List[str] = ['scaler', 'rf']` |

## 📦 Dependencies

The following packages are required:
- `scikit-learn`
- `numpy`
- `pandas`
- `joblib`
- `threadpoolctl`
- `scipy`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.sklearn_server.server
```
