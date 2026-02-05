from pathlib import Path
from typing import Optional, Union, Any, Dict
import pandas as pd
import structlog

logger = structlog.get_logger()

SUPPORTED_EXTENSIONS = {
    '.csv': 'csv',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.json': 'json',
    '.parquet': 'parquet',
    '.feather': 'feather',
    '.pkl': 'pickle',
    '.pickle': 'pickle',
    '.xml': 'xml',
    '.html': 'html',
    '.h5': 'hdf',
    '.hdf5': 'hdf'
}

def detect_format(file_path: Union[str, Path]) -> str:
    """Detect file format from extension."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[suffix]
    raise ValueError(f"Unsupported or unknown file extension: {suffix}")

def load_dataframe(file_path: Union[str, Path], format: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """Universal load function."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    fmt = format or detect_format(path)
    
    try:
        if fmt == 'csv':
            return pd.read_csv(path, **kwargs)
        elif fmt == 'excel':
            return pd.read_excel(path, **kwargs)
        elif fmt == 'json':
            return pd.read_json(path, **kwargs)
        elif fmt == 'parquet':
            return pd.read_parquet(path, **kwargs)
        elif fmt == 'feather':
            return pd.read_feather(path, **kwargs)
        elif fmt == 'pickle':
            # Security warning: pickle is unsafe, but necessary for internal state sometimes
            return pd.read_pickle(path, **kwargs)
        elif fmt == 'xml':
            return pd.read_xml(path, **kwargs)
        elif fmt == 'html':
            dfs = pd.read_html(path, **kwargs)
            return dfs[0] if dfs else pd.DataFrame()
        elif fmt == 'hdf':
            return pd.read_hdf(path, **kwargs)
        else:
            raise ValueError(f"No handler for format: {fmt}")
    except Exception as e:
        logger.error("load_dataframe_failed", file=str(path), error=str(e))
        raise RuntimeError(f"Failed to load {file_path}: {str(e)}")

def save_dataframe(df: pd.DataFrame, file_path: Union[str, Path], format: Optional[str] = None, **kwargs) -> None:
    """Universal save function."""
    path = Path(file_path)
    # Create parent dirs if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fmt = format or detect_format(path)

    try:
        if fmt == 'csv':
            df.to_csv(path, index=False, **kwargs)
        elif fmt == 'excel':
            df.to_excel(path, index=False, **kwargs)
        elif fmt == 'json':
            df.to_json(path, **kwargs)
        elif fmt == 'parquet':
            df.to_parquet(path, **kwargs)
        elif fmt == 'feather':
            df.to_feather(path, **kwargs)
        elif fmt == 'pickle':
            df.to_pickle(path, **kwargs)
        elif fmt == 'xml':
            df.to_xml(path, index=False, **kwargs)
        elif fmt == 'html':
            df.to_html(path, index=False, **kwargs)
        elif fmt == 'hdf':
            df.to_hdf(path, key='data', **kwargs)
        else:
            raise ValueError(f"No handler for format: {fmt}")
    except Exception as e:
        logger.error("save_dataframe_failed", file=str(path), error=str(e))
        raise RuntimeError(f"Failed to save to {file_path}: {str(e)}")

def get_dataframe_info(df: pd.DataFrame) -> Dict[str, Any]:
    """Get serializable info about a dataframe."""
    import io
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()
    
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "memory_usage": df.memory_usage(deep=True).sum(),
        "shape": df.shape,
        "summary": info_str
    }
