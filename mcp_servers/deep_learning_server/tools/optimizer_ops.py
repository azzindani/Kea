from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

def _config(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    return {"class_name": name, "config": params}

# --- Optimizers ---
def config_sgd(learning_rate: float = 0.01, momentum: float = 0.0, nesterov: bool = False) -> Dict[str, Any]:
    """CONFIGURES SGD Optimizer. [DATA]"""
    return _config("SGD", {"learning_rate": learning_rate, "momentum": momentum, "nesterov": nesterov})

def config_rmsprop(learning_rate: float = 0.001, rho: float = 0.9) -> Dict[str, Any]:
    """CONFIGURES RMSprop Optimizer. [DATA]"""
    return _config("RMSprop", {"learning_rate": learning_rate, "rho": rho})

def config_adam(learning_rate: float = 0.001, beta_1: float = 0.9, beta_2: float = 0.999) -> Dict[str, Any]:
    """CONFIGURES Adam Optimizer. [DATA]"""
    return _config("Adam", {"learning_rate": learning_rate, "beta_1": beta_1, "beta_2": beta_2})

def config_adadelta(learning_rate: float = 0.001, rho: float = 0.95) -> Dict[str, Any]:
    """CONFIGURES Adadelta Optimizer. [DATA]"""
    return _config("Adadelta", {"learning_rate": learning_rate, "rho": rho})

def config_adagrad(learning_rate: float = 0.001) -> Dict[str, Any]:
    """CONFIGURES Adagrad Optimizer. [DATA]"""
    return _config("Adagrad", {"learning_rate": learning_rate})

def config_adamax(learning_rate: float = 0.002) -> Dict[str, Any]:
    """CONFIGURES Adamax Optimizer. [DATA]"""
    return _config("Adamax", {"learning_rate": learning_rate})

def config_nadam(learning_rate: float = 0.001) -> Dict[str, Any]:
    """CONFIGURES Nadam Optimizer. [DATA]"""
    return _config("Nadam", {"learning_rate": learning_rate})

def config_ftrl(learning_rate: float = 0.001) -> Dict[str, Any]:
    """CONFIGURES Ftrl Optimizer. [DATA]"""
    return _config("Ftrl", {"learning_rate": learning_rate})

# --- Callbacks ---
def config_early_stopping(monitor: str = 'val_loss', patience: int = 3, restore_best_weights: bool = True) -> Dict[str, Any]:
    """CONFIGURES EarlyStopping. [DATA]"""
    return _config("EarlyStopping", {"monitor": monitor, "patience": patience, "restore_best_weights": restore_best_weights})

def config_model_checkpoint(filepath: str, monitor: str = 'val_loss', save_best_only: bool = True) -> Dict[str, Any]:
    """CONFIGURES ModelCheckpoint. [DATA]"""
    return _config("ModelCheckpoint", {"filepath": filepath, "monitor": monitor, "save_best_only": save_best_only})

def config_reduce_lr_on_plateau(monitor: str = 'val_loss', factor: float = 0.1, patience: int = 10) -> Dict[str, Any]:
    """CONFIGURES ReduceLROnPlateau. [DATA]"""
    return _config("ReduceLROnPlateau", {"monitor": monitor, "factor": factor, "patience": patience})

def config_csv_logger(filename: str, separator: str = ',', append: bool = False) -> Dict[str, Any]:
    """CONFIGURES CSVLogger. [DATA]"""
    return _config("CSVLogger", {"filename": filename, "separator": separator, "append": append})
