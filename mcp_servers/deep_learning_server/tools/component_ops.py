from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()

def _comp(type_name: str, name: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
    return {"type": type_name, "name": name, "params": params}

# --- Loss Functions ---
def loss_categorical_crossentropy(from_logits: bool = False, label_smoothing: float = 0.0) -> Dict[str, Any]:
    """CONFIGURES CategoricalCrossentropy loss. [DATA]"""
    return _comp("Loss", "CategoricalCrossentropy", {"from_logits": from_logits, "label_smoothing": label_smoothing})

def loss_binary_crossentropy(from_logits: bool = False, label_smoothing: float = 0.0) -> Dict[str, Any]:
    """CONFIGURES BinaryCrossentropy loss. [DATA]"""
    return _comp("Loss", "BinaryCrossentropy", {"from_logits": from_logits, "label_smoothing": label_smoothing})

def loss_mean_squared_error() -> Dict[str, Any]:
    """CONFIGURES MSE loss. [DATA]"""
    return _comp("Loss", "MeanSquaredError")

def loss_mean_absolute_error() -> Dict[str, Any]:
    """CONFIGURES MAE loss. [DATA]"""
    return _comp("Loss", "MeanAbsoluteError")

def loss_huber(delta: float = 1.0) -> Dict[str, Any]:
    """CONFIGURES Huber loss. [DATA]"""
    return _comp("Loss", "Huber", {"delta": delta})

def loss_log_cosh() -> Dict[str, Any]:
    """CONFIGURES LogCosh loss. [DATA]"""
    return _comp("Loss", "LogCosh")

def loss_poisson() -> Dict[str, Any]:
    """CONFIGURES Poisson loss. [DATA]"""
    return _comp("Loss", "Poisson")

def loss_kullback_leibler_divergence() -> Dict[str, Any]:
    """CONFIGURES KLDivergence loss. [DATA]"""
    return _comp("Loss", "KLDivergence")

def loss_hinge() -> Dict[str, Any]:
    """CONFIGURES Hinge loss. [DATA]"""
    return _comp("Loss", "Hinge")

def loss_squared_hinge() -> Dict[str, Any]:
    """CONFIGURES SquaredHinge loss. [DATA]"""
    return _comp("Loss", "SquaredHinge")

# --- Metrics ---
def metric_accuracy() -> Dict[str, Any]:
    """CONFIGURES Accuracy metric. [DATA]"""
    return _comp("Metric", "Accuracy")

def metric_binary_accuracy(threshold: float = 0.5) -> Dict[str, Any]:
    """CONFIGURES BinaryAccuracy metric. [DATA]"""
    return _comp("Metric", "BinaryAccuracy", {"threshold": threshold})

def metric_categorical_accuracy() -> Dict[str, Any]:
    """CONFIGURES CategoricalAccuracy metric. [DATA]"""
    return _comp("Metric", "CategoricalAccuracy")

def metric_auc(num_thresholds: int = 200, curve: str = 'ROC', from_logits: bool = False) -> Dict[str, Any]:
    """CONFIGURES AUC metric. [DATA]"""
    return _comp("Metric", "AUC", {"num_thresholds": num_thresholds, "curve": curve, "from_logits": from_logits})

def metric_precision(thresholds: float = None) -> Dict[str, Any]:
    """CONFIGURES Precision metric. [DATA]"""
    return _comp("Metric", "Precision", {"thresholds": thresholds})

def metric_recall(thresholds: float = None) -> Dict[str, Any]:
    """CONFIGURES Recall metric. [DATA]"""
    return _comp("Metric", "Recall", {"thresholds": thresholds})

def metric_true_positives(thresholds: float = None) -> Dict[str, Any]:
    """CONFIGURES TruePositives metric. [DATA]"""
    return _comp("Metric", "TruePositives", {"thresholds": thresholds})

def metric_true_negatives(thresholds: float = None) -> Dict[str, Any]:
    """CONFIGURES TrueNegatives metric. [DATA]"""
    return _comp("Metric", "TrueNegatives", {"thresholds": thresholds})

def metric_false_positives(thresholds: float = None) -> Dict[str, Any]:
    """CONFIGURES FalsePositives metric. [DATA]"""
    return _comp("Metric", "FalsePositives", {"thresholds": thresholds})

def metric_false_negatives(thresholds: float = None) -> Dict[str, Any]:
    """CONFIGURES FalseNegatives metric. [DATA]"""
    return _comp("Metric", "FalseNegatives", {"thresholds": thresholds})

# --- Initializers ---
def init_zeros() -> Dict[str, Any]:
    """CONFIGURES Zeros initializer. [DATA]"""
    return _comp("Initializer", "Zeros")

def init_ones() -> Dict[str, Any]:
    """CONFIGURES Ones initializer. [DATA]"""
    return _comp("Initializer", "Ones")

def init_constant(value: float = 0.0) -> Dict[str, Any]:
    """CONFIGURES Constant initializer. [DATA]"""
    return _comp("Initializer", "Constant", {"value": value})

def init_random_normal(mean: float = 0.0, stddev: float = 0.05) -> Dict[str, Any]:
    """CONFIGURES RandomNormal initializer. [DATA]"""
    return _comp("Initializer", "RandomNormal", {"mean": mean, "stddev": stddev})

def init_random_uniform(minval: float = -0.05, maxval: float = 0.05) -> Dict[str, Any]:
    """CONFIGURES RandomUniform initializer. [DATA]"""
    return _comp("Initializer", "RandomUniform", {"minval": minval, "maxval": maxval})

def init_truncated_normal(mean: float = 0.0, stddev: float = 0.05) -> Dict[str, Any]:
    """CONFIGURES TruncatedNormal initializer. [DATA]"""
    return _comp("Initializer", "TruncatedNormal", {"mean": mean, "stddev": stddev})

def init_variance_scaling(scale: float = 1.0, mode: str = 'fan_in', distribution: str = 'truncated_normal') -> Dict[str, Any]:
    """CONFIGURES VarianceScaling initializer. [DATA]"""
    return _comp("Initializer", "VarianceScaling", {"scale": scale, "mode": mode, "distribution": distribution})

def init_orthogonal(gain: float = 1.0) -> Dict[str, Any]:
    """CONFIGURES Orthogonal initializer. [DATA]"""
    return _comp("Initializer", "Orthogonal", {"gain": gain})

def init_lecun_uniform() -> Dict[str, Any]:
    """CONFIGURES LecunUniform initializer. [DATA]"""
    return _comp("Initializer", "LecunUniform")

def init_glorot_uniform() -> Dict[str, Any]:
    """CONFIGURES GlorotUniform initializer. [DATA]"""
    return _comp("Initializer", "GlorotUniform")

def init_he_uniform() -> Dict[str, Any]:
    """CONFIGURES HeUniform initializer. [DATA]"""
    return _comp("Initializer", "HeUniform")

# --- Regularizers ---
def reg_l1(l1: float = 0.01) -> Dict[str, Any]:
    """CONFIGURES L1 regularizer. [DATA]"""
    return _comp("Regularizer", "L1", {"l1": l1})

def reg_l2(l2: float = 0.01) -> Dict[str, Any]:
    """CONFIGURES L2 regularizer. [DATA]"""
    return _comp("Regularizer", "L2", {"l2": l2})

def reg_l1_l2(l1: float = 0.01, l2: float = 0.01) -> Dict[str, Any]:
    """CONFIGURES L1L2 regularizer. [DATA]"""
    return _comp("Regularizer", "L1L2", {"l1": l1, "l2": l2})
