from mcp_servers.scipy_server.tools.core_ops import to_serializable, parse_data, NumericData
from scipy import signal, fft
import numpy as np
from typing import Dict, Any, List, Optional

async def find_peaks(data: NumericData, height: Optional[float] = None, distance: Optional[int] = None) -> Dict[str, Any]:
    """Find peaks inside a signal."""
    arr = parse_data(data)
    peaks, props = signal.find_peaks(arr, height=height, distance=distance)
    return to_serializable({"peaks": peaks.tolist(), "properties": props})

async def compute_fft(data: NumericData) -> Dict[str, Any]:
    """
    Compute Fast Fourier Transform.
    Returns magnitude and phase for simplicity in JSON.
    """
    arr = parse_data(data)
    res = fft.fft(arr)
    # Return spectrum
    return to_serializable({
        "real": res.real.tolist(),
        "imag": res.imag.tolist(),
        "magnitude": np.abs(res).tolist(),
        "phase": np.angle(res).tolist()
    })

async def compute_ifft(data_real: NumericData, data_imag: Optional[NumericData] = None) -> List[float]:
    """Inverse FFT (returns real part)."""
    r = parse_data(data_real)
    if data_imag:
        i = parse_data(data_imag)
        comp = r + 1j * i
    else:
        comp = r 
        
    res = fft.ifft(comp)
    return to_serializable(res.real.tolist())

async def resample(data: NumericData, num: int) -> List[float]:
    """Resample x to num samples."""
    arr = parse_data(data)
    res = signal.resample(arr, num)
    return to_serializable(res.tolist())

async def medfilt(data: NumericData, kernel_size: int = 3) -> List[float]:
    """Apply median filter."""
    arr = parse_data(data)
    res = signal.medfilt(arr, kernel_size)
    return to_serializable(res.tolist())

async def wiener(data: NumericData) -> List[float]:
    """Apply Wiener filter."""
    arr = parse_data(data)
    res = signal.wiener(arr)
    return to_serializable(res.tolist())

async def savgol_filter(data: NumericData, window_length: int = 5, polyorder: int = 2) -> List[float]:
    """Apply Savitzky-Golay filter."""
    arr = parse_data(data)
    res = signal.savgol_filter(arr, window_length, polyorder)
    return to_serializable(res.tolist())

async def detrend(data: NumericData, type: str = 'linear') -> List[float]:
    """Remove linear trend."""
    arr = parse_data(data)
    res = signal.detrend(arr, type=type)
    return to_serializable(res.tolist())
