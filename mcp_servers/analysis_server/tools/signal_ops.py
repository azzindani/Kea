import numpy as np
import pandas as pd
import structlog
from scipy import signal, fft
from typing import Dict, List, Any, Optional

logger = structlog.get_logger()

def _get_data(file_path, col):
    df = pd.read_csv(file_path)
    return df[col].dropna().values

def signal_fft(file_path: str, column: str) -> Dict[str, Any]:
    """COMPUTES Fast Fourier Transform. [DATA]"""
    try:
        x = _get_data(file_path, column)
        y = fft.fft(x)
        # Return magnitude for JSON serialization usually, or complex parts
        return {
            "real": y.real.tolist()[:100], 
            "imag": y.imag.tolist()[:100],
            "magnitude": np.abs(y).tolist()[:100]
        }
    except Exception as e:
        return {"error": str(e)}

def signal_periodogram(file_path: str, column: str, fs: float = 1.0) -> Dict[str, Any]:
    """COMPUTES Periodogram. [DATA]"""
    try:
        x = _get_data(file_path, column)
        f, Pxx = signal.periodogram(x, fs)
        return {"freqs": f.tolist(), "power": Pxx.tolist()}
    except Exception as e:
        return {"error": str(e)}

def signal_welch(file_path: str, column: str, fs: float = 1.0) -> Dict[str, Any]:
    """COMPUTES Welch's Method PSD. [DATA]"""
    try:
        x = _get_data(file_path, column)
        f, Pxx = signal.welch(x, fs)
        return {"freqs": f.tolist(), "power": Pxx.tolist()}
    except Exception as e:
        return {"error": str(e)}

def signal_detrend(file_path: str, column: str, output_path: str="detrended.csv") -> str:
    """REMOVES linear trend. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        y = df[column].dropna() # Detrend needs no nans usually
        detrended = signal.detrend(y)
        # Pad back to original length or create new df
        df_out = pd.DataFrame({f"{column}_detrend": detrended})
        df_out.to_csv(output_path, index=False)
        return f"Saved to {output_path}"
    except Exception as e:
        return f"Error: {e}"

def signal_hilbert(file_path: str, column: str) -> Dict[str, Any]:
    """COMPUTES Hilbert Transform. [DATA]"""
    try:
        x = _get_data(file_path, column)
        h = signal.hilbert(x)
        return {
            "amplitude": np.abs(h).tolist()[:100], 
            "phase": np.angle(h).tolist()[:100]
        }
    except Exception as e:
        return {"error": str(e)}

def signal_resample(file_path: str, column: str, num_samples: int, output_path: str="resampled.csv") -> str:
    """RESAMPLES signal. [ACTION]"""
    try:
        x = _get_data(file_path, column)
        resampled = signal.resample(x, num_samples)
        pd.DataFrame({column: resampled}).to_csv(output_path, index=False)
        return f"Saved to {output_path}"
    except Exception as e:
        return f"Error: {e}"
