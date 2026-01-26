from mcp_servers.sklearn_server.tools.core_ops import parse_data, to_serializable, serialize_model, DataInput
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler,
    LabelEncoder, OneHotEncoder, OrdinalEncoder,
    Binarizer, PolynomialFeatures, PowerTransformer
)
from sklearn.impute import SimpleImputer
import pandas as pd
from typing import Dict, Any, List, Optional, Union

async def fit_transform_scaler(data: DataInput, method: str = 'standard') -> Dict[str, Any]:
    """Fit and transform data using specified scaler. Returns transformed data and serialized model."""
    df = parse_data(data)
    
    if method == 'standard':
        scaler = StandardScaler()
    elif method == 'minmax':
        scaler = MinMaxScaler()
    elif method == 'robust':
        scaler = RobustScaler()
    elif method == 'maxabs':
        scaler = MaxAbsScaler()
    else:
        raise ValueError(f"Unknown scaler method: {method}")
        
    transformed = scaler.fit_transform(df)
    
    return to_serializable({
        "transformed": transformed.tolist(),
        "model": serialize_model(scaler)
    })

async def fit_transform_encoder(data: DataInput, method: str = 'label', columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Fit and transform categorical data."""
    df = parse_data(data)
    
    # LabelEncoder works on 1D vector (target usually)
    if method == 'label':
        # Flatten input if needed or assume single column data
        vals = df.iloc[:, 0] if df.shape[1] > 0 else []
        enc = LabelEncoder()
        transformed = enc.fit_transform(vals)
        return to_serializable({
            "transformed": transformed.tolist(),
            "classes": enc.classes_.tolist(),
            "model": serialize_model(enc)
        })
        
    elif method == 'onehot':
        enc = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        transformed = enc.fit_transform(df)
        return to_serializable({
            "transformed": transformed.tolist(),
            "feature_names": enc.get_feature_names_out().tolist(),
            "model": serialize_model(enc)
        })
        
    elif method == 'ordinal':
        enc = OrdinalEncoder()
        transformed = enc.fit_transform(df)
        return to_serializable({
            "transformed": transformed.tolist(),
            "model": serialize_model(enc)
        })

async def impute_missing(data: DataInput, strategy: str = 'mean', fill_value: Optional[Any] = None) -> Dict[str, Any]:
    """Impute missing values."""
    df = parse_data(data)
    imp = SimpleImputer(strategy=strategy, fill_value=fill_value)
    transformed = imp.fit_transform(df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "model": serialize_model(imp)
    })

async def generate_features(data: DataInput, method: str = 'poly', degree: int = 2) -> Dict[str, Any]:
    """Generate polynomial or power features."""
    df = parse_data(data)
    
    if method == 'poly':
        trans = PolynomialFeatures(degree=degree)
    elif method == 'power':
        trans = PowerTransformer()
        
    transformed = trans.fit_transform(df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "model": serialize_model(trans)
    })
