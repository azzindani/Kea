from mcp_servers.xgboost_server.tools.core_ops import create_dmatrix, deserialize_booster, serialize_booster, DataInput, VectorInput
import xgboost as xgb
import json
import os
import tempfile
from typing import Dict, Any, List, Optional, Union

async def booster_predict(model: str, X: DataInput) -> List[float]:
    """Predict using a serialized model (Booster or Sklearn wrapper)."""
    obj = deserialize_booster(model)
    
    # Check if sklearn wrapper
    if hasattr(obj, 'predict'):
        # Usually expects DataFrame/Array
        from mcp_servers.xgboost_server.tools.core_ops import parse_data_frame
        df = parse_data_frame(X)
        return obj.predict(df).tolist()
    elif isinstance(obj, xgb.Booster):
        # Expects DMatrix
        dtest = create_dmatrix(X)
        return obj.predict(dtest).tolist()
    else:
        raise ValueError("Unknown model type")

async def booster_save(model: str, format: str = 'json') -> str:
    """Save/Dump model to string (JSON/UBJSON/Text)."""
    obj = deserialize_booster(model)
    
    # Extract booster if sklearn wrapper
    if hasattr(obj, 'get_booster'):
        booster = obj.get_booster()
    elif isinstance(obj, xgb.Booster):
        booster = obj
    else:
        raise ValueError("Object is not a Booster or Wrapper")
        
    if format == 'json':
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            booster.save_model(tmp.name)
            with open(tmp.name, 'r') as f:
                content = f.read()
            os.unlink(tmp.name)
            return content
    elif format == 'text':
        return "\n".join(booster.get_dump())
    
    return "Unsupported format"

async def booster_attributes(model: str) -> Dict[str, Any]:
    """Get attributes of the booster."""
    obj = deserialize_booster(model)
    if hasattr(obj, 'get_booster'):
        booster = obj.get_booster()
    else:
        booster = obj
        
    return {
        "attr": booster.attributes(),
        "best_iteration": booster.best_iteration,
        "best_ntree_limit": booster.best_ntree_limit
    }
