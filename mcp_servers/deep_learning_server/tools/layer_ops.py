
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

# Strategy: Instead of returning actual Keras objects (which aren't JSON serializable),
# we return a "Layer Config" dictionary. The `train_deep_model` tool will then 
# interpret these configs to build the model dynamically using functional API or Sequential.

def _layer_config(layer_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": layer_type, "params": params}

# --- Core Layers ---
def add_dense(units: int, activation: str = 'relu') -> Dict[str, Any]:
    """ADDS Dense layer config. [DATA]"""
    return _layer_config("Dense", {"units": units, "activation": activation})

def add_activation(activation: str) -> Dict[str, Any]:
    """ADDS Activation layer config. [DATA]"""
    return _layer_config("Activation", {"activation": activation})

def add_dropout(rate: float) -> Dict[str, Any]:
    """ADDS Dropout layer config. [DATA]"""
    return _layer_config("Dropout", {"rate": rate})

def add_flatten() -> Dict[str, Any]:
    """ADDS Flatten layer config. [DATA]"""
    return _layer_config("Flatten", {})

def add_batch_normalization() -> Dict[str, Any]:
    """ADDS BatchNormalization layer config. [DATA]"""
    return _layer_config("BatchNormalization", {})

# --- Convolutional Layers ---
def add_conv1d(filters: int, kernel_size: int, activation: str = 'relu', padding: str = 'valid') -> Dict[str, Any]:
    """ADDS Conv1D layer config. [DATA]"""
    return _layer_config("Conv1D", {"filters": filters, "kernel_size": kernel_size, "activation": activation, "padding": padding})

def add_conv2d(filters: int, kernel_size: int, activation: str = 'relu', padding: str = 'valid') -> Dict[str, Any]:
    """ADDS Conv2D layer config. [DATA]"""
    return _layer_config("Conv2D", {"filters": filters, "kernel_size": kernel_size, "activation": activation, "padding": padding})

def add_max_pooling1d(pool_size: int = 2) -> Dict[str, Any]:
    """ADDS MaxPooling1D layer config. [DATA]"""
    return _layer_config("MaxPooling1D", {"pool_size": pool_size})

def add_max_pooling2d(pool_size: int = (2, 2)) -> Dict[str, Any]:
    """ADDS MaxPooling2D layer config. [DATA]"""
    return _layer_config("MaxPooling2D", {"pool_size": pool_size})

# --- RNN Layers ---
def add_lstm(units: int, return_sequences: bool = False) -> Dict[str, Any]:
    """ADDS LSTM layer config. [DATA]"""
    return _layer_config("LSTM", {"units": units, "return_sequences": return_sequences})

def add_gru(units: int, return_sequences: bool = False) -> Dict[str, Any]:
    """ADDS GRU layer config. [DATA]"""
    return _layer_config("GRU", {"units": units, "return_sequences": return_sequences})

def add_simple_rnn(units: int, return_sequences: bool = False) -> Dict[str, Any]:
    """ADDS SimpleRNN layer config. [DATA]"""
    return _layer_config("SimpleRNN", {"units": units, "return_sequences": return_sequences})

# --- Model Compiler ---
def compile_model_config(optimizer: str = 'adam', loss: str = 'mse', metrics: List[str] = ['mae']) -> Dict[str, Any]:
    """DEFINES model compilation config. [DATA]"""
    return {"optimizer": optimizer, "loss": loss, "metrics": metrics}
