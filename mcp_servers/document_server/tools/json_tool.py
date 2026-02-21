
import httpx
import json
try:
    import pandas as pd
except ImportError:
    pd = None

from shared.logging.main import get_logger

logger = get_logger(__name__)

async def parse_json(url: str, flatten: bool = False, path: str = None) -> str:
    """Parse JSON file."""
    if flatten and pd is None:
        return "Error: pandas is not installed. JSON flattening is unavailable."
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        
        output_data = {
            "source": url,
            "flattened": False,
            "data": None
        }
        
        # Navigate to path if provided
        if path:
            for key in path.split("."):
                if isinstance(data, dict):
                    data = data.get(key, {})
                elif isinstance(data, list) and key.isdigit():
                    data = data[int(key)]
        
        if flatten and isinstance(data, list):
            try:
                df = pd.json_normalize(data)
                # Convert first 1000 rows to dict
                output_data["data"] = df.head(1000).to_dict(orient='records')
                output_data["flattened"] = True
                output_data["columns"] = list(df.columns)
            except Exception:
                output_data["data"] = data
        else:
            output_data["data"] = data
        
        return json.dumps(output_data, indent=2, default=str)
    except Exception as e:
        logger.error(f"JSON Parser error: {e}")
        return f"Error: {str(e)}"
