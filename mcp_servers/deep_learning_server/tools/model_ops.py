import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

def _get_output_activation(task: str, output_dim: int) -> str:
    if task == 'regression':
        return 'linear'
    elif output_dim == 1:
        return 'sigmoid' # Binary classification
    else:
        return 'softmax' # Multi-class

def build_dense_network(input_dim: int, output_dim: int, hidden_layers: List[int], task: str = 'classification') -> Dict[str, Any]:
    """BUILDS dense neural network. [ACTION]"""
    try:
        inputs = layers.Input(shape=(input_dim,))
        x = inputs
        
        for units in hidden_layers:
            x = layers.Dense(units)(x)
            x = layers.BatchNormalization()(x)
            x = layers.Activation('relu')(x)
            x = layers.Dropout(0.3)(x)
            
        outputs = layers.Dense(output_dim, activation=_get_output_activation(task, output_dim))(x)
        
        model = models.Model(inputs=inputs, outputs=outputs, name="DenseNet")
        
        # We process the model to a JSON config for later reconstruction or just return summary
        config = model.to_json()
        
        return {
            "name": "DenseNet",
            "summary": "Model built successfully",
            "config": config,
            "params": model.count_params()
        }
    except Exception as e:
        logger.error("build_dense_network failed", error=str(e))
        return {"error": str(e)}

def build_cnn_1d_network(input_shape: List[int], output_dim: int, filters: int = 64, kernel_size: int = 3, task: str = 'classification') -> Dict[str, Any]:
    """BUILDS 1D CNN. [ACTION]"""
    try:
        inputs = layers.Input(shape=tuple(input_shape))
        
        # Block 1
        x = layers.Conv1D(filters, kernel_size, padding='same', activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        
        # Block 2
        x = layers.Conv1D(filters * 2, kernel_size, padding='same', activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        
        x = layers.Flatten()(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.4)(x)
        
        outputs = layers.Dense(output_dim, activation=_get_output_activation(task, output_dim))(x)
        
        model = models.Model(inputs=inputs, outputs=outputs, name="CNN1D")
        config = model.to_json()
        
        return {
            "name": "CNN1D",
            "summary": "Model built successfully",
            "config": config,
            "params": model.count_params()
        }
    except Exception as e:
        logger.error("build_cnn_1d_network failed", error=str(e))
        return {"error": str(e)}

def residual_block(x, filters, kernel_size=3):
    shortcut = x
    x = layers.Conv1D(filters, kernel_size, padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Conv1D(filters, kernel_size, padding='same')(x)
    x = layers.BatchNormalization()(x)
    
    # Adjust shortcut input if dimensions change (not needed if simple same padding)
    
    x = layers.Add()([x, shortcut])
    x = layers.Activation('relu')(x)
    return x

def build_residual_network(input_shape: List[int], output_dim: int, blocks: int = 3, task: str = 'classification') -> Dict[str, Any]:
    """BUILDS ResNet architecture. [ACTION]"""
    try:
        inputs = layers.Input(shape=tuple(input_shape))
        x = layers.Conv1D(64, 7, padding='same', activation='relu')(inputs)
        
        for _ in range(blocks):
            x = residual_block(x, 64)
        
        # FIX: Was layers.GlobalAveragePooling1D()(x) but missed x assignment or similar in prev code?
        # No, the previous code had a bug where 'outputs' was undefined. 
        # Correctly implementing here.
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dense(output_dim, activation=_get_output_activation(task, output_dim))(x)
        
        # Corrected variable usage here
        model = models.Model(inputs=inputs, outputs=x, name="ResNet")
        config = model.to_json()
        
        return {
            "name": "ResNet",
            "summary": "Model built successfully",
            "config": config,
            "params": model.count_params()
        }
    except Exception as e:
        logger.error("build_residual_network failed", error=str(e))
        return {"error": str(e)}
