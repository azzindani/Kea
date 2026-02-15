import pandas as pd
import numpy as np
import structlog
from typing import List, Dict, Any, Union
import os

logger = structlog.get_logger()

def clean_dataset_auto(file_path: str, output_path: str) -> str:
    """CLEANS dataset automatically. [ACTION]
    
    [RAG Context]
    "Super Cleaner". Runs standard pipeline: 
    Headers, Whitespace, Empty Cols, Impute NaNs, Dates, Outliers.
    """
    try:
        df = pd.read_csv(file_path)
        report = []
        
        # 1. Standardize Headers
        df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
        report.append("Standardized headers (snake_case)")
        
        # 2. Trim Whitespace (String cols)
        str_cols = df.select_dtypes(include=['object']).columns
        for col in str_cols:
             df[col] = df[col].str.strip()
        report.append(f"Trimmed whitespace in {len(str_cols)} columns")
        
        # 3. Drop Empty Columns/Rows
        orig_shape = df.shape
        df.dropna(how='all', axis=1, inplace=True)
        df.dropna(how='all', axis=0, inplace=True)
        if df.shape != orig_shape:
            report.append(f"Dropped empty rows/cols. New shape: {df.shape}")
            
        # 4. Impute Missing Values (Simple Strategy)
        # Numeric -> Median
        num_cols = df.select_dtypes(include=['number']).columns
        for col in num_cols:
            if df[col].isnull().sum() > 0:
                median = df[col].median()
                df[col] = df[col].fillna(median)
                report.append(f"Imputed {col} with median {median}")

        # Categorical -> Mode
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            if df[col].isnull().sum() > 0:
                mode = df[col].mode()[0]
                df[col] = df[col].fillna(mode)
                report.append(f"Imputed {col} with mode '{mode}'")
                
        # 5. Outliers (IQR Method) - optional but requested in generic 'clean'
        # We'll just cap them to avoid data loss, or mark them? Let's cap at 1.5 IQR
        for col in num_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            if outliers > 0:
                df[col] = np.clip(df[col], lower_bound, upper_bound)
                report.append(f"Capped {outliers} outliers in {col}")
        
        # Save
        df.to_csv(output_path, index=False)
        return "\n".join(report)
        
    except Exception as e:
        logger.error("clean_dataset_auto failed", error=str(e))
        return f"Error: {str(e)}"

def generate_profile_report(file_path: str, output_path: str) -> str:
    """GENERATES HTML profile. [DATA]
    
    [RAG Context]
    Generates a comprehensive HTML report using ydata_profiling.
    Includes stats, correlations, distributions.
    """
    try:
        from ydata_profiling import ProfileReport
        df = pd.read_csv(file_path)
        profile = ProfileReport(df, title="Pandas Profiling Report", minimal=True)
        profile.to_file(output_path)
        return f"Report saved to {output_path}"
    except ImportError:
        return "ydata-profiling not installed. Please install it to use this tool."
    except Exception as e:
        logger.error("generate_profile_report failed", error=str(e))
        return f"Error: {str(e)}"
