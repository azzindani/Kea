from typing import Dict, Any, List, Optional, Union
import structlog

logger = structlog.get_logger()

def _layer(type_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": type_name, "params": params}

# --- Advanced Activations ---
def add_leaky_relu(alpha: float = 0.3) -> Dict[str, Any]:
    """ADDS LeakyReLU layer. [DATA]"""
    return _layer("LeakyReLU", {"alpha": alpha})

def add_prelu(alpha_initializer: str = "zeros") -> Dict[str, Any]:
    """ADDS PReLU layer. [DATA]"""
    return _layer("PReLU", {"alpha_initializer": alpha_initializer})

def add_elu(alpha: float = 1.0) -> Dict[str, Any]:
    """ADDS ELU layer. [DATA]"""
    return _layer("ELU", {"alpha": alpha})

def add_thresholded_relu(theta: float = 1.0) -> Dict[str, Any]:
    """ADDS ThresholdedReLU layer. [DATA]"""
    return _layer("ThresholdedReLU", {"theta": theta})

def add_softmax(axis: int = -1) -> Dict[str, Any]:
    """ADDS Softmax layer. [DATA]"""
    return _layer("Softmax", {"axis": axis})

# --- Shape Manipulation ---
def add_permute(dims: List[int]) -> Dict[str, Any]:
    """ADDS Permute layer. [DATA]"""
    return _layer("Permute", {"dims": dims})

def add_repeat_vector(n: int) -> Dict[str, Any]:
    """ADDS RepeatVector layer. [DATA]"""
    return _layer("RepeatVector", {"n": n})

def add_reshape(target_shape: List[int]) -> Dict[str, Any]:
    """ADDS Reshape layer. [DATA]"""
    return _layer("Reshape", {"target_shape": target_shape})

def add_up_sampling1d(size: int = 2) -> Dict[str, Any]:
    """ADDS UpSampling1D layer. [DATA]"""
    return _layer("UpSampling1D", {"size": size})

def add_up_sampling2d(size: Union[int, List[int]] = (2, 2)) -> Dict[str, Any]:
    """ADDS UpSampling2D layer. [DATA]"""
    return _layer("UpSampling2D", {"size": size})

# --- Pooling ---
def add_global_average_pooling1d() -> Dict[str, Any]:
    """ADDS GlobalAveragePooling1D. [DATA]"""
    return _layer("GlobalAveragePooling1D", {})

def add_global_average_pooling2d() -> Dict[str, Any]:
    """ADDS GlobalAveragePooling2D. [DATA]"""
    return _layer("GlobalAveragePooling2D", {})

def add_global_max_pooling1d() -> Dict[str, Any]:
    """ADDS GlobalMaxPooling1D. [DATA]"""
    return _layer("GlobalMaxPooling1D", {})

def add_global_max_pooling2d() -> Dict[str, Any]:
    """ADDS GlobalMaxPooling2D. [DATA]"""
    return _layer("GlobalMaxPooling2D", {})

# --- Recurrent Wrappers/Variations ---
def add_embedding(input_dim: int, output_dim: int, input_length: Optional[int] = None) -> Dict[str, Any]:
    """ADDS Embedding layer. [DATA]"""
    return _layer("Embedding", {"input_dim": input_dim, "output_dim": output_dim, "input_length": input_length})

def add_bidirectional(layer: Dict[str, Any], merge_mode: str = "concat") -> Dict[str, Any]:
    """ADDS Bidirectional wrapper. [DATA]"""
    return _layer("Bidirectional", {"layer": layer, "merge_mode": merge_mode})

def add_time_distributed(layer: Dict[str, Any]) -> Dict[str, Any]:
    """ADDS TimeDistributed wrapper. [DATA]"""
    return _layer("TimeDistributed", {"layer": layer})

def add_attention(use_scale: bool = False) -> Dict[str, Any]:
    """ADDS Attention layer. [DATA]"""
    return _layer("Attention", {"use_scale": use_scale})

# --- Regularization ---
def add_activity_regularization(l1: float = 0.0, l2: float = 0.0) -> Dict[str, Any]:
    """ADDS ActivityRegularization. [DATA]"""
    return _layer("ActivityRegularization", {"l1": l1, "l2": l2})

def add_masking(mask_value: float = 0.0) -> Dict[str, Any]:
    """ADDS Masking layer. [DATA]"""
    return _layer("Masking", {"mask_value": mask_value})
