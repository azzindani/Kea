from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional

async def fft(a: NumericData, n: Optional[int] = None, axis: int = -1) -> Dict[str, Any]:
    """Compute the 1-D FFT."""
    res = np.fft.fft(parse_array(a), n=n, axis=axis)
    return {
        "real": res.real.tolist(),
        "imag": res.imag.tolist(),
        "abs": np.abs(res).tolist()
    }

async def ifft(a_real: NumericData, a_imag: Optional[NumericData] = None, n: Optional[int] = None, axis: int = -1) -> List[Any]:
    """Compute the 1-D inverse FFT."""
    real = parse_array(a_real)
    if a_imag:
        imag = parse_array(a_imag)
        comp = real + 1j * imag
    else:
        comp = real
    res = np.fft.ifft(comp, n=n, axis=axis)
    # usually interested in real signal reconstruction
    return to_serializable(res.real.tolist())

async def fft2(a: NumericData, s: Optional[List[int]] = None) -> Dict[str, Any]:
    """Compute the 2-D FFT."""
    res = np.fft.fft2(parse_array(a), s=s)
    return {
        "real": res.real.tolist(),
        "imag": res.imag.tolist(),
        "abs": np.abs(res).tolist()
    }

async def fftfreq(n: int, d: float = 1.0) -> List[float]:
    """Return the Discrete Fourier Transform sample frequencies."""
    return to_serializable(np.fft.fftfreq(n, d=d).tolist())
