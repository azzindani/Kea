from mcp_servers.xgboost_server.tools.core_ops import deserialize_booster
import xgboost as xgb
from typing import Dict, Any, List

async def get_feature_importance(model: str, importance_type: str = 'weight') -> Dict[str, float]:
    """Get feature importance. Type: 'weight', 'gain', 'cover', 'total_gain', 'total_cover'."""
    obj = deserialize_booster(model)
    if hasattr(obj, 'get_booster'):
        booster = obj.get_booster()
    else:
        booster = obj
        
    return booster.get_score(importance_type=importance_type)

async def get_trees(model: str) -> List[str]:
    """Get text dump of all trees."""
    obj = deserialize_booster(model)
    if hasattr(obj, 'get_booster'):
        booster = obj.get_booster()
    else:
        booster = obj
        
    return booster.get_dump()
