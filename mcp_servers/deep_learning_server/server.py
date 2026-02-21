
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path

# JIT Import Hack
sys.path.append(str(Path(__file__).parent))
# from mcp_servers.deep_learning_server.tools import model_ops, train_ops

import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging()

mcp = FastMCP("deep_learning_server", dependencies=["tensorflow", "pandas", "numpy", "scikit-learn", "structlog"])

@mcp.tool()
def build_dense_network(input_dim: int, output_dim: int, hidden_layers: List[int], task: str = 'classification') -> Dict[str, Any]:
    """BUILDS dense neural network. [ACTION]
    
    [RAG Context]
    Creates a standard MLP model (Dense -> BN -> ReLU -> Dropout).
    Returns model architecture summary.
    """
    from mcp_servers.deep_learning_server.tools import model_ops
    return model_ops.build_dense_network(input_dim, output_dim, hidden_layers, task)

@mcp.tool()
def build_cnn_1d_network(input_shape: List[int], output_dim: int, filters: int = 64, kernel_size: int = 3, task: str = 'classification') -> Dict[str, Any]:
    """BUILDS 1D CNN. [ACTION]
    
    [RAG Context]
    Creates a 1D CNN for sequence or tabular data.
    Returns model architecture summary.
    """
    from mcp_servers.deep_learning_server.tools import model_ops
    return model_ops.build_cnn_1d_network(input_shape, output_dim, filters, kernel_size, task)

@mcp.tool()
def build_residual_network(input_shape: List[int], output_dim: int, blocks: int = 3, task: str = 'classification') -> Dict[str, Any]:
    """BUILDS ResNet architecture. [ACTION]
    
    [RAG Context]
    Creates a Residual Network for deep learning on tabular/sequence data.
    Returns model architecture summary.
    """
    from mcp_servers.deep_learning_server.tools import model_ops
    return model_ops.build_residual_network(input_shape, output_dim, blocks, task)

# ==========================================
# 2. Granular Layers (New)
# ==========================================
# ==========================================
# 2. Granular Layers (New)
# ==========================================
@mcp.tool()
def add_dense(units: int, activation: str = 'relu') -> Dict[str, Any]:
    """ADDS Dense layer config. [DATA]
    
    [RAG Context]
    Fully connected layer.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_dense(units, activation)

@mcp.tool()
def add_activation(activation: str) -> Dict[str, Any]:
    """ADDS Activation layer config. [DATA]
    
    [RAG Context]
    Applies activation function (relu, sigmoid, etc).
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_activation(activation)

@mcp.tool()
def add_dropout(rate: float) -> Dict[str, Any]:
    """ADDS Dropout layer config. [DATA]
    
    [RAG Context]
    Randomly drops neurons to prevent overfitting.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_dropout(rate)

@mcp.tool()
def add_flatten() -> Dict[str, Any]:
    """ADDS Flatten layer config. [DATA]
    
    [RAG Context]
    Flattens spatial inputs (e.g. 2D to 1D).
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_flatten()

@mcp.tool()
def add_batch_normalization() -> Dict[str, Any]:
    """ADDS BatchNormalization layer config. [DATA]
    
    [RAG Context]
    Normalizes layer inputs.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_batch_normalization()

@mcp.tool()
def add_conv1d(filters: int, kernel_size: int, activation: str = 'relu', padding: str = 'valid') -> Dict[str, Any]:
    """ADDS Conv1D layer config. [DATA]
    
    [RAG Context]
    Convolution over 1D sequence.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_conv1d(filters, kernel_size, activation, padding)

@mcp.tool()
def add_max_pooling1d(pool_size: int = 2) -> Dict[str, Any]:
    """ADDS MaxPooling1D layer config. [DATA]
    
    [RAG Context]
    Downsamples 1D sequence.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_max_pooling1d(pool_size)

@mcp.tool()
def add_lstm(units: int, return_sequences: bool = False) -> Dict[str, Any]:
    """ADDS LSTM layer config. [DATA]
    
    [RAG Context]
    Long Short-Term Memory RNN.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_lstm(units, return_sequences)

@mcp.tool()
def add_gru(units: int, return_sequences: bool = False) -> Dict[str, Any]:
    """ADDS GRU layer config. [DATA]
    
    [RAG Context]
    Gated Recurrent Unit RNN.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.add_gru(units, return_sequences)

@mcp.tool()
def compile_model_config(optimizer: str = 'adam', loss: str = 'mse', metrics: List[str] = ['mae']) -> Dict[str, Any]:
    """DEFINES model compilation config. [DATA]
    
    [RAG Context]
    Sets optimizer and loss function.
    """
    from mcp_servers.deep_learning_server.tools import layer_ops
    return layer_ops.compile_model_config(optimizer, loss, metrics)

@mcp.tool()
def train_deep_model(data_url: str, target_column: str, model_config: Dict[str, Any], epochs: int = 50, batch_size: int = 32) -> Dict[str, Any]:
    """TRAINS deep learning model. [ACTION]
    
    [RAG Context]
    Trains a deep learning model with EarlyStopping and Checkpointing.
    Returns training history and metrics.
    """
    from mcp_servers.deep_learning_server.tools import train_ops
    return train_ops.train_deep_model(data_url, target_column, model_config, epochs, batch_size)

@mcp.tool()
def evaluate_deep_model(data_url: str, target_column: str, model_path: str) -> Dict[str, Any]:
    """EVALUATES deep learning model. [DATA]
    
    [RAG Context]
    Evaluates a saved model on test data.
    Returns loss, accuracy, and confusion matrix.
    """
    from mcp_servers.deep_learning_server.tools import train_ops
    return train_ops.evaluate_deep_model(data_url, target_column, model_path)



# ==========================================
# 6. Components (Losses, Metrics, Inits) (New)
# ==========================================
@mcp.tool()
def loss_categorical_crossentropy(from_logits: bool = False, label_smoothing: float = 0.0) -> Dict[str, Any]:
    """CONFIGURES CategoricalCrossentropy loss. [DATA]
    
    [RAG Context]
    Loss for multi-class classification.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.loss_categorical_crossentropy(from_logits, label_smoothing)

@mcp.tool()
def loss_binary_crossentropy(from_logits: bool = False, label_smoothing: float = 0.0) -> Dict[str, Any]:
    """CONFIGURES BinaryCrossentropy loss. [DATA]
    
    [RAG Context]
    Loss for binary classification.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.loss_binary_crossentropy(from_logits, label_smoothing)

@mcp.tool()
def loss_mean_squared_error() -> Dict[str, Any]:
    """CONFIGURES MSE loss. [DATA]
    
    [RAG Context]
    Mean Squared Error loss.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.loss_mean_squared_error()

@mcp.tool()
def loss_mean_absolute_error() -> Dict[str, Any]:
    """CONFIGURES MAE loss. [DATA]
    
    [RAG Context]
    Mean Absolute Error loss.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.loss_mean_absolute_error()

@mcp.tool()
def metric_accuracy() -> Dict[str, Any]:
    """CONFIGURES Accuracy metric. [DATA]
    
    [RAG Context]
    Standard accuracy metric.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.metric_accuracy()

@mcp.tool()
def metric_auc(num_thresholds: int = 200, curve: str = 'ROC') -> Dict[str, Any]:
    """CONFIGURES AUC metric. [DATA]
    
    [RAG Context]
    Area Under Curve metric.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.metric_auc(num_thresholds, curve)

@mcp.tool()
def init_glorot_uniform() -> Dict[str, Any]:
    """CONFIGURES GlorotUniform initializer. [DATA]
    
    [RAG Context]
    Xavier initializer.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.init_glorot_uniform()

@mcp.tool()
def init_he_uniform() -> Dict[str, Any]:
    """CONFIGURES HeUniform initializer. [DATA]
    
    [RAG Context]
    He initializer.
    """
    from mcp_servers.deep_learning_server.tools import component_ops
    return component_ops.init_he_uniform()

# ==========================================
# 7. Applications (Pretrained Models) (New)
# ==========================================
@mcp.tool()
def app_xception(input_shape: List[int] = (299, 299, 3), include_top: bool = False) -> Dict[str, Any]:
    """CONFIGURES Xception Model. [DATA]
    
    [RAG Context]
    Deep CNN with Separable Convolutions.
    """
    from mcp_servers.deep_learning_server.tools import application_ops
    return application_ops.app_xception(input_shape, include_top)

@mcp.tool()
def app_resnet50(input_shape: List[int] = (224, 224, 3), include_top: bool = False) -> Dict[str, Any]:
    """CONFIGURES ResNet50 Model. [DATA]
    
    [RAG Context]
    50-layer Residual Network.
    """
    from mcp_servers.deep_learning_server.tools import application_ops
    return application_ops.app_resnet50(input_shape, include_top)

@mcp.tool()
def app_vgg16(input_shape: List[int] = (224, 224, 3), include_top: bool = False) -> Dict[str, Any]:
    """CONFIGURES VGG16 Model. [DATA]
    
    [RAG Context]
    Visual Geometry Group 16-layer model.
    """
    from mcp_servers.deep_learning_server.tools import application_ops
    return application_ops.app_vgg16(input_shape, include_top)

@mcp.tool()
def app_mobilenet(input_shape: List[int] = (224, 224, 3), include_top: bool = False) -> Dict[str, Any]:
    """CONFIGURES MobileNet Model. [DATA]
    
    [RAG Context]
    Lightweight model for mobile.
    """
    from mcp_servers.deep_learning_server.tools import application_ops
    return application_ops.app_mobilenet(input_shape, include_top)

if __name__ == "__main__":

    mcp.run()
