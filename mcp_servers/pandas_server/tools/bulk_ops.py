import pandas as pd
import requests
import io
import zipfile
import structlog
from typing import List, Dict, Any, Union

logger = structlog.get_logger()

def bulk_read_datasets(urls: List[str]) -> Dict[str, Any]:
    """READS multiple datasets. [DATA]
    
    [RAG Context]
    Downloads and loads multiple datasets from URLs (CSV, JSON, ZIP).
    Returns a summary dictionary containing success/failure status and metadata.
    Supported formats: CSV, JSON, ZIP (containing CSVs).
    """
    results = {}
    summary = {
        "total": len(urls),
        "success": 0,
        "failed": 0,
        "details": []
    }
    
    for url in urls:
        try:
            logger.info("Downloading dataset", url=url)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Handle ZIP
            if url.lower().endswith('.zip') or 'zip' in content_type:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    for filename in z.namelist():
                        if filename.lower().endswith('.csv'):
                            with z.open(filename) as f:
                                df = pd.read_csv(f)
                                results[f"{url}/{filename}"] = df.shape
                                summary["details"].append({"url": url, "file": filename, "shape": df.shape, "status": "success"})
                                summary["success"] += 1
            
            # Handle JSON
            elif url.lower().endswith('.json') or 'json' in content_type:
                df = pd.read_json(io.BytesIO(response.content))
                results[url] = df.shape
                summary["details"].append({"url": url, "shape": df.shape, "status": "success"})
                summary["success"] += 1

            # Default to CSV
            else:
                df = pd.read_csv(io.BytesIO(response.content))
                results[url] = df.shape
                summary["details"].append({"url": url, "shape": df.shape, "status": "success"})
                summary["success"] += 1
                
        except Exception as e:
            logger.error("Failed to download/read dataset", url=url, error=str(e))
            summary["failed"] += 1
            summary["details"].append({"url": url, "status": "failed", "error": str(e)})
            
    return summary

def merge_datasets_bulk(file_paths: List[str], on: str, how: str = "inner", output_path: str = "") -> str:
    """MERGES multiple dataframes. [ACTION]
    
    [RAG Context]
    Iteratively merges a list of datasets on a common key.
    Useful for combining scattered data files into a master dataset.
    """
    if len(file_paths) < 2:
        return "Need at least 2 files to merge."
        
    try:
        logger.info("Merging datasets", count=len(file_paths))
        # Read first file
        main_df = pd.read_csv(file_paths[0])
        
        for next_file in file_paths[1:]:
            next_df = pd.read_csv(next_file)
            main_df = pd.merge(main_df, next_df, on=on, how=how)
            
        if output_path:
            main_df.to_csv(output_path, index=False)
            return f"Merged {len(file_paths)} files into {main_df.shape} dataset at {output_path}"
        else:
            return f"Merged shape: {main_df.shape}. (No output path provided)"
            
    except Exception as e:
        logger.error("merge_datasets_bulk failed", error=str(e))
        return f"Error: {str(e)}"
