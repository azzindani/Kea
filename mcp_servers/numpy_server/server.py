
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)



from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.numpy_server.tools import (
    creation_ops, manip_ops, math_ops, logic_ops, 
    linalg_ops, random_ops, fft_ops, super_ops,
    bitwise_ops, string_ops, set_ops, poly_ops, stat_plus_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("numpy_server", dependencies=["numpy", "pandas"])
NumericData = Any 

# ==========================================
# 1. Creation
# ==========================================
# ==========================================
# 1. Creation
# ==========================================
@mcp.tool()
async def create_array(data: NumericData) -> List[Any]: 
    """CREATES a numpy array from data. [ENTRY]
    
    [RAG Context]
    Converts Python lists, tuples, or nested sequences into high-performance NumPy arrays. This is the primary entry point for numerical computing in the Kea system.
    
    How to Use:
    - Pass any nested list to create a multi-dimensional array (e.g., `[[1, 2], [3, 4]]` for a 2x2 matrix).
    - NumPy arrays are more memory-efficient and faster than Python lists for mathematical operations.
    
    Keywords: array constructor, list to array, matrix creation, tensor init.
    """
    return await creation_ops.create_array(data)

@mcp.tool()
async def create_zeros(shape: List[int]) -> List[Any]: 
    """CREATES an array of zeros. [ENTRY]
    
    [RAG Context]
    Initializes a new array of a given shape, where every element is 0.0.
    
    How to Use:
    - Useful as a placeholder or to initialize accumulators for algorithms.
    - 'shape' is a list of dimensions, e.g., `[5]` for 1D, `[3, 3]` for a 3x3 matrix.
    
    Keywords: zero initialization, empty array, placeholder, buffer init.
    """
    return await creation_ops.create_zeros(shape)

@mcp.tool()
async def create_ones(shape: List[int]) -> List[Any]: 
    """CREATES an array of ones. [ENTRY]
    
    [RAG Context]
    Initializes a new array of a given shape, where every element is 1.0.
    
    Keywords: constant init, baseline array, value initialization.
    """
    return await creation_ops.create_ones(shape)

@mcp.tool()
async def create_full(shape: List[int], fill_value: Union[float, int]) -> List[Any]: 
    """CREATES an array filled with value. [ENTRY]
    
    [RAG Context]
    Initializes a new array of a given shape, filled with a specific constant value.
    
    Arguments:
    - shape: Dimensions of the array.
    - fill_value: The number to fill the array with.
    
    Keywords: constant fill, full array, value init.
    """
    return await creation_ops.create_full(shape, fill_value)

@mcp.tool()
async def arange(start: float, stop: float = None, step: float = 1) -> List[float]: 
    """CREATES evenly spaced values (step). [ENTRY]
    
    [RAG Context]
    Generates a sequence of numbers from 'start' up to (but not including) 'stop', incrementing by 'step'. Similar to Python's range() but returns a NumPy array and supports floats.
    
    How to Use:
    - `arange(0, 10, 2)` -> `[0, 2, 4, 6, 8]`.
    - `arange(5)` -> `[0, 1, 2, 3, 4]`.
    
    Keywords: sequence generator, range array, numeric sequence, step increment.
    """
    return await creation_ops.arange(start, stop, step)

@mcp.tool()
async def linspace(start: float, stop: float, num: int = 50) -> List[float]: 
    """CREATES evenly spaced values (count). [ENTRY]
    
    [RAG Context]
    Generates 'num' numbers evenly spaced between 'start' and 'stop' (inclusive).
    
    How to Use:
    - Best for creating a precise number of sample points across a range for plotting or signal processing.
    - Example: `linspace(0, 1, 11)` -> `[0.0, 0.1, 0.2, ... 1.0]`.
    
    Keywords: linear interval, spacing, sample points, range division.
    """
    return await creation_ops.linspace(start, stop, num)

@mcp.tool()
async def logspace(start: float, stop: float, num: int = 50, base: float = 10.0) -> List[float]: 
    """CREATES logarithmically spaced values. [ENTRY]
    
    [RAG Context]
    Generates numbers evenly spaced on a log scale.
    
    How to Use:
    - Useful for generating frequencies or parameters that span several orders of magnitude.
    - The sequence starts at `base ** start` and ends at `base ** stop`.
    
    Keywords: logarithmic scale, frequency sweep, log spacing.
    """
    return await creation_ops.logspace(start, stop, num, base)

@mcp.tool()
async def geomspace(start: float, stop: float, num: int = 50) -> List[float]: 
    """CREATES geometrically spaced values. [ENTRY]
    
    [RAG Context]
    """
    return await creation_ops.geomspace(start, stop, num)

@mcp.tool()
async def eye(N: int, M: Optional[int] = None, k: int = 0) -> List[List[float]]: 
    """CREATES a 2D identity matrix. [ENTRY]
    
    [RAG Context]
    Generates a 2D array where the main diagonal is 1s and everything else is 0s. 
    
    Arguments:
    - N: Number of rows.
    - M: Number of columns (Defaults to N if None).
    - k: Index of the diagonal (0 for main, >0 for upper, <0 for lower).
    
    Keywords: identity matrix, unit matrix, diagonal init, linear algebra prep.
    """
    return await creation_ops.eye(N, M, k)

@mcp.tool()
async def identity(n: int) -> List[List[float]]: 
    """CREATES a square identity array. [ENTRY]
    
    [RAG Context]
    """
    return await creation_ops.identity(n)

@mcp.tool()
async def diag(v: NumericData, k: int = 0) -> List[Any]: 
    """EXTRACTS or CONSTRUCTS diagonal. [ENTRY]
    
    [RAG Context]
    A dual-purpose tool:
    1. If 'v' is 1D: Creates a square 2D matrix with 'v' on its diagonal.
    2. If 'v' is 2D: Extracts the diagonal elements from the matrix.
    
    Keywords: diagonal extract, diagonal matrix, matrix diag, trace elements.
    """
    return await creation_ops.diag(v, k)

@mcp.tool()
async def vander(x: List[float], N: Optional[int] = None) -> List[List[float]]: 
    """GENERATES a Vandermonde matrix. [ENTRY]
    
    [RAG Context]
    """
    return await creation_ops.vander(x, N)

# ==========================================
# 2. Manipulation
# ==========================================
@mcp.tool()
async def reshape(a: NumericData, newshape: List[int]) -> List[Any]: 
    """RESHAPES an array. [ACTION]
    
    [RAG Context]
    Changes the dimensions (shape) of an array without changing its underlying data.
    
    How to Use:
    - The total number of elements must remain constant.
    - Example: Reshape a 1D array of size 6 into a 2D matrix of shape `[2, 3]`.
    - Use `-1` for one of the dimensions to let NumPy calculate the size automatically based on the other values.
    
    Keywords: change shape, dimension shift, resize array, tensor reshape.
    """
    return await manip_ops.reshape(a, newshape)

@mcp.tool()
async def flatten(a: NumericData) -> List[Any]: 
    """FLATTENS array to 1D. [ACTION]
    
    [RAG Context]
    Collapses a multi-dimensional array into a simple 1D sequence.
    
    Keywords: 1d conversion, vectorization, collapse dimensions.
    """
    return await manip_ops.flatten(a)

@mcp.tool()
async def transpose(a: NumericData, axes: Optional[List[int]] = None) -> List[Any]: 
    """PERMUTES dimensions (Transpose). [ACTION]
    
    [RAG Context]
    Swaps the axes of an array. In 2D, this flips the matrix over its main diagonal (columns become rows).
    
    How to Use:
    - For high-dimensional tensors, use 'axes' to specify the new order of dimensions (e.g., `[2, 0, 1]`).
    
    Keywords: matrix flip, swap axes, dimension permutation, linear algebra swap.
    """
    return await linalg_ops.transpose(a, axes)

@mcp.tool()
async def flip(m: NumericData, axis: Optional[Union[int, List[int]]] = None) -> List[Any]: 
    """REVERSES order of elements. [ACTION]
    
    [RAG Context]
    Reverses the order of elements along the specified axis.
    
    How to Use:
    - If no axis is specified, it flips the array along all axes.
    - Useful for reversing time-series or mirror images (in 2D).
    
    Keywords: mirror, reverse sequence, flip axis, inverted order.
    """
    return await manip_ops.flip(m, axis)

@mcp.tool()
async def roll(a: NumericData, shift: Union[int, List[int]], axis: Optional[Union[int, List[int]]] = None) -> List[Any]: 
    """ROLLS elements along axis. [ACTION]
    
    [RAG Context]
    Shifts elements of an array circularly. Elements that roll off one end come back on the other.
    
    How to Use:
    - 'shift': Number of positions to move (positive for forward, negative for backward).
    - Useful for temporal shifts in cyclic data.
    
    Keywords: cyclic shift, rotate elements, circular buffer, rolling data.
    """
    return await manip_ops.roll(a, shift, axis)

@mcp.tool()
async def concatenate(arrays: List[NumericData], axis: int = 0) -> List[Any]: 
    """JOINS sequence of arrays. [ACTION]
    
    [RAG Context]
    Combines multiple arrays into a single large array along an existing axis.
    
    How to Use:
    - All arrays must have the same shape except in the dimension corresponding to 'axis'.
    - Equivalent to 'appending' data.
    
    Keywords: join arrays, merge numeric, combine vectors, stack deep.
    """
    return await manip_ops.concatenate(arrays, axis)

@mcp.tool()
async def stack(arrays: List[NumericData], axis: int = 0) -> List[Any]: 
    """JOINS arrays along new axis. [ACTION]
    
    [RAG Context]
    Stacks a list of arrays into a single array with one additional dimension. Unlike 'concatenate' which joins along an existing axis, 'stack' creates a new one.
    
    How to Use:
    - All arrays must have the same shape.
    - Useful for turning a list of vectors into a 2D matrix or a list of images into a 3D batch.
    
    Keywords: stack arrays, new dimension, vector to matrix, batching data.
    """
    return await manip_ops.stack(arrays, axis)

@mcp.tool()
async def vstack(tup: List[NumericData]) -> List[Any]: 
    """STACKS arrays vertically (row-wise). [ACTION]
    
    [RAG Context]
    Stacks arrays in sequence vertically (row-wise). For 1D arrays, it stacks them into a 2D matrix where each array is a row.
    
    Keywords: vertical stack, row stack, append rows, matrix building.
    """
    return await manip_ops.vstack(tup)

@mcp.tool()
async def hstack(tup: List[NumericData]) -> List[Any]: 
    """STACKS arrays horizontally (col-wise). [ACTION]
    
    [RAG Context]
    Glues arrays together side-by-side. 
    
    How to Use:
    - For 1D arrays, this is the same as concatenate.
    - For 2D matrices, it appends columns.
    
    Keywords: horizontal join, column stack, widen matrix, lateral merge.
    """
    return await manip_ops.hstack(tup)

@mcp.tool()
async def split(ary: NumericData, indices_or_sections: Union[int, List[int]], axis: int = 0) -> List[List[Any]]: 
    """SPLITS array into sub-arrays. [ACTION]
    
    [RAG Context]
    Divide an array into multiple smaller sub-arrays along a given axis.
    
    How to Use:
    - If 'indices_or_sections' is an integer, the array is split into that many equal sections.
    - If it's a list (e.g., `[2, 3]`), it indicates the points at which the array is split.
    
    Keywords: array division, shard data, segment array, split tensor.
    """
    return await manip_ops.split(ary, indices_or_sections, axis)

@mcp.tool()
async def tile(A: NumericData, reps: List[int]) -> List[Any]: 
    """CONSTRUCTS array by repeating A. [ACTION]
    
    [RAG Context]
    Repeats the entire input array 'A' multiple times to form a larger tiled array.
    
    How to Use:
    - `tile([1, 2], [3])` -> `[1, 2, 1, 2, 1, 2]`.
    - Useful for broadcasting smaller patterns onto larger grids.
    
    Keywords: pattern repeat, tiling, grid creation, data duplication.
    """
    return await manip_ops.tile(A, reps)

@mcp.tool()
async def repeat(a: NumericData, repeats: Union[int, List[int]], axis: Optional[int] = None) -> List[Any]: 
    """REPEATS elements of an array. [ACTION]
    
    [RAG Context]
    Repeats individual elements of an array.
    
    How to Use:
    - `repeat(3, 4)` -> `[3, 3, 3, 3]`.
    - `repeat([1, 2], 2)` -> `[1, 1, 2, 2]`.
    - Unlike 'tile', which repeats the whole array, 'repeat' repeats each element.
    
    Keywords: element duplication, stretch array, oversampling.
    """
    return await manip_ops.repeat(a, repeats, axis)

@mcp.tool()
async def unique(ar: NumericData) -> List[Any]: 
    """FINDS unique elements. [DATA]
    
    [RAG Context]
    Returns the sorted unique elements of an array.
    
    How to Use:
    - Eliminates redundant values.
    - Useful for categorical analysis in numeric form (e.g., finding unique labels in a dataset).
    
    Keywords: distinct values, deduplicate, unique set, category identification.
    """
    return await manip_ops.unique(ar)

@mcp.tool()
async def trim_zeros(filt: NumericData, trim: str = 'fb') -> List[Any]: 
    """TRIMS leading/trailing zeros. [ACTION]
    
    [RAG Context]
    Removes zeros from the ends of a 1D array.
    
    How to Use:
    - 'trim': 'f' (leading), 'b' (trailing), 'fb' (both).
    - Perfect for cleaning signal data or sequences where padding is not needed.
    
    Keywords: zero removal, signal cleaning, trim padding, strip zeros.
    """
    return await manip_ops.trim_zeros(filt, trim)

@mcp.tool()
async def pad(array: NumericData, pad_width: List[Any], mode: str = 'constant', constant_values: Any = 0) -> List[Any]: 
    """PADS array. [ACTION]
    
    [RAG Context]
    Increases the size of an array by adding padding elements to its borders.
    
    How to Use:
    - 'pad_width': Number of elements to add at each edge (e.g., `[1, 1]` for 1 element at the beginning and end).
    - 'mode': 'constant' (fixed value), 'edge' (repeat last element), 'reflect' (mirror).
    - Essential for Image Processing (CNN kernels) and Signal Processing.
    
    Keywords: boarder padding, resizing, frame expansion, signal prep.
    """
    return await manip_ops.pad(array, pad_width, mode, constant_values)

# ==========================================
# 3. Math
# ==========================================
@mcp.tool()
async def add(x1: NumericData, x2: NumericData) -> List[Any]: 
    """ADDS arguments element-wise. [ACTION]
    
    [RAG Context]
    Performs vector-based addition. If inputs have different shapes, NumPy will automatically "broadcast" the smaller array (if compatible).
    
    Keywords: plus, summation, vectorized add, broadcasting addition.
    """
    return await math_ops.add(x1, x2)

@mcp.tool()
async def subtract(x1: NumericData, x2: NumericData) -> List[Any]: 
    """SUBTRACTS arguments element-wise. [ACTION]
    
    [RAG Context]
    Computes `x1 - x2` for every element. Fully supports broadcasting for differently shaped arrays.
    
    Keywords: minus, difference, vectorized subtract, decrement.
    """
    return await math_ops.subtract(x1, x2)

@mcp.tool()
async def multiply(x1: NumericData, x2: NumericData) -> List[Any]: 
    """MULTIPLIES arguments element-wise. [ACTION]
    
    [RAG Context]
    Multiplies every element in x1 by its corresponding element in x2. 
    
    Note: For matrix multiplication (row-by-column), use the 'matmul' tool instead.
    
    Keywords: times, product, Hadamard product, scaling array.
    """
    return await math_ops.multiply(x1, x2)

@mcp.tool()
async def divide(x1: NumericData, x2: NumericData) -> List[Any]: 
    """DIVIDES arguments element-wise. [ACTION]
    
    [RAG Context]
    Divides elements of x1 by x2. Correctly handles float division (e.g., `1 / 2 = 0.5`). 
    
    Keywords: quotient, fractional divide, normalization.
    """
    return await math_ops.divide(x1, x2)

@mcp.tool()
async def power(x1: NumericData, x2: NumericData) -> List[Any]: 
    """RAISES x1 to power x2. [ACTION]
    
    [RAG Context]
    Vectorized exponentiation. Every element in x1 is raised to the power of the corresponding element in x2.
    
    Keywords: exponent, power of, squaring, rooting.
    """
    return await math_ops.power(x1, x2)

@mcp.tool()
async def mod(x1: NumericData, x2: NumericData) -> List[Any]: 
    """RETURNS element-wise remainder. [ACTION]
    
    [RAG Context]
    Calculates the modulus (remainder after division).
    
    Keywords: remainder, modulo, cycle index.
    """
    return await math_ops.mod(x1, x2)

# Functions
@mcp.tool()
async def abs_val(x: NumericData) -> List[Any]: 
    """CALCULATES absolute value. [ACTION]
    
    [RAG Context]
    Returns the positive magnitude of every element.
    
    Keywords: absolute, non-negative, magnitude, modulus.
    """
    return await math_ops.abs_val(x)

@mcp.tool()
async def sign(x: NumericData) -> List[Any]: 
    """RETURNS sign of number. [ACTION]
    
    [RAG Context]
    Returns -1 for negative, 0 for zero, and 1 for positive elements.
    
    Keywords: signum, parity check, positive negative.
    """
    return await math_ops.sign(x)

@mcp.tool()
async def exp(x: NumericData) -> List[Any]: 
    """CALCULATES exponential. [ACTION]
    
    [RAG Context]
    Calculates `e^x` (the exponential of x) element-wise.
    
    Keywords: e to the power, exponential growth, euler number.
    """
    return await math_ops.exp(x)

@mcp.tool()
async def log(x: NumericData) -> List[Any]: 
    """CALCULATES natural logarithm. [ACTION]
    
    [RAG Context]
    Computes the base-'e' logarithm.
    
    Note: Returns NaN for zero or negative inputs.
    
    Keywords: ln, natural log, logarithmic transform.
    """
    return await math_ops.log(x)

@mcp.tool()
async def log10(x: NumericData) -> List[Any]: 
    """CALCULATES base-10 logarithm. [ACTION]
    
    [RAG Context]
    """
    return await math_ops.log10(x)

@mcp.tool()
async def sqrt(x: NumericData) -> List[Any]: 
    """CALCULATES square root. [ACTION]
    
    [RAG Context]
    Returns the non-negative square root of every element.
    
    Keywords: square root, radicle, sqrt, power half.
    """
    return await math_ops.sqrt(x)

@mcp.tool()
async def sin(x: NumericData) -> List[Any]: 
    """CALCULATES sine. [ACTION]
    
    [RAG Context]
    Trigonometric sine function (expects input in Radians).
    
    Keywords: sine wave, trigonometry, periodic function.
    """
    return await math_ops.sin(x)

@mcp.tool()
async def cos(x: NumericData) -> List[Any]: 
    """CALCULATES cosine. [ACTION]
    
    [RAG Context]
    """
    return await math_ops.cos(x)

@mcp.tool()
async def tan(x: NumericData) -> List[Any]: 
    """CALCULATES tangent. [ACTION]
    
    [RAG Context]
    """
    return await math_ops.tan(x)

@mcp.tool()
async def rad2deg(x: NumericData) -> List[Any]: 
    """CONVERTS radians to degrees. [ACTION]
    
    [RAG Context]
    """
    return await math_ops.rad2deg(x)

@mcp.tool()
async def deg2rad(x: NumericData) -> List[Any]: 
    """CONVERTS degrees to radians. [ACTION]
    
    [RAG Context]
    """
    return await math_ops.deg2rad(x)

@mcp.tool()
async def clip(a: NumericData, a_min: float, a_max: float) -> List[Any]: 
    """CLIPS values to interval. [ACTION]
    
    [RAG Context]
    Given an interval [min, max], values smaller than min are set to min, and values larger than max are set to max.
    
    How to Use:
    - Essential for data normalization or to prevent Extreme Outliers during processing.
    
    Keywords: clamp values, range limit, outbound removal.
    """
    return await math_ops.clip(a, a_min, a_max)

@mcp.tool()
async def round_val(a: NumericData, decimals: int = 0) -> List[Any]: 
    """ROUNDS to decimals. [ACTION]
    
    [RAG Context]
    Rounds elements to the nearest integer or specific decimal place.
    
    Keywords: rounding, significant figures, floor ceiling.
    """
    return await math_ops.round_val(a, decimals)

# Aggregations
@mcp.tool()
async def sum_val(a: NumericData, axis: Optional[int] = None) -> Union[float, List[Any]]: 
    """SUMS array elements. [Data]
    
    [RAG Context]
    Calculates the total sum of all elements in the array.
    
    How to Use:
    - If 'axis' is None, sums every element.
    - If 'axis' is 0, sums along columns.
    - If 'axis' is 1, sums along rows.
    
    Keywords: summation, total, reduce sum, aggregate.
    """
    return await math_ops.sum_val(a, axis)

@mcp.tool()
async def prod(a: NumericData, axis: Optional[int] = None) -> Union[float, List[Any]]: 
    """MULTIPLIES array elements. [Data]
    
    [RAG Context]
    """
    return await math_ops.prod(a, axis)

@mcp.tool()
async def cumsum(a: NumericData, axis: Optional[int] = None) -> List[Any]: 
    """CALCULATES cumulative sum. [Data]
    
    [RAG Context]
    Returns an array of the same shape where each element is the sum of all elements up to that index.
    
    How to Use:
    - Ideal for calculating running totals or integration.
    
    Keywords: running sum, accumulation, integral, cumulative total.
    """
    return await math_ops.cumsum(a, axis)

@mcp.tool()
async def cumprod(a: NumericData, axis: Optional[int] = None) -> List[Any]: 
    """CALCULATES cumulative product. [Data]
    
    [RAG Context]
    """
    return await math_ops.cumprod(a, axis)

@mcp.tool()
async def diff(a: NumericData, n: int = 1, axis: int = -1) -> List[Any]: 
    """CALCULATES n-th discrete difference. [Data]
    
    [RAG Context]
    Calculates the difference between adjacent elements. 
    
    How to Use:
    - `[1, 2, 4, 7]` -> `[1, 2, 3]`.
    - Useful for calculating velocity from position data or identifying rates of change.
    
    Keywords: discrete derivative, delta, rate of change, delta calculation.
    """
    return await math_ops.diff(a, n, axis)

@mcp.tool()
async def gradient(f: NumericData) -> List[Any]: 
    """CALCULATES gradient. [Data]
    
    [RAG Context]
    """
    return await math_ops.gradient(f)

@mcp.tool()
async def cross(a: NumericData, b: NumericData) -> List[Any]: 
    """CALCULATES cross product. [Data]
    
    [RAG Context]
    Computes the mathematical cross product of two vectors. The vectors must have 2 or 3 elements.
    
    Keywords: vector cross, normal vector, rotational physics.
    """
    return await math_ops.cross(a, b)

# ==========================================
# 4. Logic
# ==========================================
# ==========================================
# 4. Logic
# ==========================================
@mcp.tool()
async def greater(x1: NumericData, x2: NumericData) -> List[Any]: 
    """CHECKS if x1 > x2. [ACTION]
    
    [RAG Context]
    Returns a boolean array of the same shape, where each element is True if `x1[i] > x2[i]`.
    
    Keywords: greater than, comparison, boolean mask.
    """
    return await logic_ops.greater(x1, x2)

@mcp.tool()
async def less(x1: NumericData, x2: NumericData) -> List[Any]: 
    """CHECKS if x1 < x2. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.less(x1, x2)

@mcp.tool()
async def equal(x1: NumericData, x2: NumericData) -> List[Any]: 
    """CHECKS if x1 == x2. [ACTION]
    
    [RAG Context]
    Performs an element-wise equality check.
    
    Keywords: match, equality, same values.
    """
    return await logic_ops.equal(x1, x2)

@mcp.tool()
async def not_equal(x1: NumericData, x2: NumericData) -> List[Any]: 
    """CHECKS if x1 != x2. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.not_equal(x1, x2)

@mcp.tool()
async def logical_and(x1: NumericData, x2: NumericData) -> List[Any]: 
    """COMPUTES element-wise AND. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.logical_and(x1, x2)

@mcp.tool()
async def logical_or(x1: NumericData, x2: NumericData) -> List[Any]: 
    """COMPUTES element-wise OR. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.logical_or(x1, x2)

@mcp.tool()
async def logical_not(x: NumericData) -> List[Any]: 
    """COMPUTES element-wise NOT. [ACTION]
    
    [RAG Context]
    Inverts the boolean values of every element.
    
    Keywords: inversion, negate, flip boolean.
    """
    return await logic_ops.logical_not(x)

@mcp.tool()
async def all_true(a: NumericData, axis: Optional[int] = None) -> Union[bool, List[bool]]: 
    """CHECKS if all elements are True. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.all_true(a, axis)

@mcp.tool()
async def any_true(a: NumericData, axis: Optional[int] = None) -> Union[bool, List[bool]]: 
    """CHECKS if any element is True. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.any_true(a, axis)

@mcp.tool()
async def where(condition: NumericData, x: Optional[NumericData] = None, y: Optional[NumericData] = None) -> List[Any]: 
    """SELECTS elements depending on condition. [ACTION]
    
    [RAG Context]
    A powerful vectorized 'if-else' tool.
    
    How to Use:
    - If x and y are provided: Returns elements from 'x' where condition is True, and from 'y' where False.
    - If only 'condition' is provided: returns the *indices* of the True elements (useful for searching).
    
    Keywords: ternary operator, conditional select, element filter, array find.
    """
    return await logic_ops.where(condition, x, y)

@mcp.tool()
async def argmax(a: NumericData, axis: Optional[int] = None) -> Union[int, List[int]]: 
    """RETURNS indices of max values. [DATA]
    
    [RAG Context]
    """
    return await logic_ops.argmax(a, axis)

@mcp.tool()
async def argmin(a: NumericData, axis: Optional[int] = None) -> Union[int, List[int]]: 
    """RETURNS indices of min values. [DATA]
    
    [RAG Context]
    Finds the position (index) of the smallest value in the array.
    
    Keywords: minimum index, find lowest, peak detection.
    """
    return await logic_ops.argmin(a, axis)

@mcp.tool()
async def argsort(a: NumericData, axis: int = -1) -> List[Any]: 
    """RETURNS indices that would sort array. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.argsort(a, axis)

@mcp.tool()
async def sort(a: NumericData, axis: int = -1) -> List[Any]: 
    """SORTS an array. [ACTION]
    
    [RAG Context]
    Returns a sorted copy of the input array.
    
    How to Use:
    - Set 'axis' to sort along different dimensions (rows, columns).
    - Returns the values themselves, not the indices.
    
    Keywords: ordering, sequence sort, array arrange.
    """
    return await logic_ops.sort(a, axis)

@mcp.tool()
async def searchsorted(a: NumericData, v: NumericData, side: str = 'left') -> List[Any]: 
    """FINDS indices to insert elements. [ACTION]
    
    [RAG Context]
    Maintains order.
    """
    return await logic_ops.searchsorted(a, v, side)

# ==========================================
# 5. Linalg
# ==========================================
@mcp.tool()
async def dot(a: NumericData, b: NumericData) -> List[Any]: 
    """COMPUTES dot product. [ACTION]
    
    [RAG Context]
    Calculates the dot product of two arrays.
    
    How to Use:
    - For 1D: Standard scalar product of vectors.
    - For 2D: Matrix multiplication (similar to 'matmul').
    
    Keywords: dot product, scalar product, vector multiplication.
    """
    return await linalg_ops.dot(a, b)

@mcp.tool()
async def matmul(x1: NumericData, x2: NumericData) -> List[Any]: 
    """COMPUTES matrix product. [ACTION]
    
    [RAG Context]
    Performs the row-by-column matrix multiplication (the standard SQL or Physics definition of matrix product).
    
    How to Use:
    - Inner dimensions must match (e.g., [m, n] times [n, p] results in [m, p]).
    
    Keywords: matrix multiply, mm, tensor product, linear transformation.
    """
    return await linalg_ops.matmul(x1, x2)

@mcp.tool()
async def inner(a: NumericData, b: NumericData) -> List[Any]: 
    """COMPUTES inner product. [ACTION]
    
    [RAG Context]
    Returns the inner product of two arrays. For 1D vectors, it's the standard dot product. For higher dimensions, it's a sum-product over the last axes.
    
    Keywords: inner product, scalar multiplication, projection.
    """
    return await linalg_ops.inner(a, b)

@mcp.tool()
async def outer(a: NumericData, b: NumericData) -> List[Any]: 
    """COMPUTES outer product. [ACTION]
    
    [RAG Context]
    Computes the outer product of two vectors, resulting in a matrix where `M[i, j] = a[i] * b[j]`.
    
    Keywords: outer product, tensor product, matrix expansion.
    """
    return await linalg_ops.outer(a, b)

@mcp.tool()
async def kron(a: NumericData, b: NumericData) -> List[Any]: 
    """COMPUTES Kronecker product. [ACTION]
    
    [RAG Context]
    """
    return await linalg_ops.kron(a, b)

@mcp.tool()
async def matrix_power(a: NumericData, n: int) -> List[Any]: 
    """RAISES square matrix to power n. [ACTION]
    
    [RAG Context]
    Multiplies a square matrix by itself 'n' times.
    
    How to Use:
    - n=0: Identity matrix.
    - n=-1: Matrix inverse.
    
    Keywords: matrix exponentiation, recursive transform, nth power.
    """
    return await linalg_ops.matrix_power(a, n)

@mcp.tool()
async def cholesky(a: NumericData) -> List[Any]: 
    """COMPUTES Cholesky decomposition. [ACTION]
    
    [RAG Context]
    Factors a square, Hermitian, positive-definite matrix into the product of a lower triangular matrix and its conjugate transpose.
    
    How to Use:
    - Essential for Monte Carlo simulations with correlated variables and solving linear least squares.
    
    Keywords: cholesky, matrix factor, triangular decomposition, simulation prep.
    """
    return await linalg_ops.cholesky(a)

@mcp.tool()
async def qr_decomp(a: NumericData, mode: str = 'reduced') -> Dict[str, Any]: 
    """COMPUTES QR decomposition. [ACTION]
    
    [RAG Context]
    """
    return await linalg_ops.qr_decomp(a, mode)

@mcp.tool()
async def svd_decomp(a: NumericData, full_matrices: bool = True) -> Dict[str, Any]: 
    """COMPUTES Singular Value Decomposition. [ACTION]
    
    [RAG Context]
    """
    return await linalg_ops.svd_decomp(a, full_matrices)

@mcp.tool()
async def eig(a: NumericData) -> Dict[str, Any]: 
    """COMPUTES eigenvalues and eigenvectors. [ACTION]
    
    [RAG Context]
    Decomposes a square matrix into its characteristic roots (eigenvalues) and corresponding vectors. This is the foundation of Dimensionality Reduction (PCA) and system stability analysis.
    
    Keywords: eigensystem, decomposition, eigen, feature extraction.
    """
    return await linalg_ops.eig(a)

@mcp.tool()
async def norm(x: NumericData, ord: Any = None, axis: Any = None) -> float: 
    """CALCULATES matrix or vector norm. [DATA]
    
    [RAG Context]
    Computes the "length" or magnitude of a matrix or vector.
    
    How to Use:
    - ord=2: Euclidean norm (L2).
    - ord=1: Manhattan norm (L1).
    - ord='fro': Frobenius norm for matrices.
    
    Keywords: magnitude, length, l2 norm, frobenius, vector scale.
    """
    return await linalg_ops.norm(x, ord, axis)

@mcp.tool()
async def cond(x: NumericData, p: Any = None) -> float: 
    """CALCULATES condition number. [DATA]
    
    [RAG Context]
    """
    return await linalg_ops.cond(x, p)

@mcp.tool()
async def det(a: NumericData) -> float: 
    """CALCULATES determinant. [DATA]
    
    [RAG Context]
    Computes the determinant of a square matrix. 
    
    How to Use:
    - If determinant is 0, the matrix is "singular" and cannot be inverted.
    
    Keywords: determinant, singular check, matrix scale factor.
    """
    return await linalg_ops.det(a)

@mcp.tool()
async def matrix_rank(M: NumericData) -> int: 
    """CALCULATES matrix rank. [DATA]
    
    [RAG Context]
    Using SVD.
    """
    return await linalg_ops.matrix_rank(M)

@mcp.tool()
async def solve(a: NumericData, b: NumericData) -> List[Any]: 
    """SOLVES linear matrix equation. [ACTION]
    
    [RAG Context]
    Finds the exact solution 'x' for the system `Ax = b`.
    
    How to Use:
    - 'a' must be a square, non-singular matrix. 
    - Much more numerically stable than calculating the inverse (`inv(a) @ b`).
    
    Keywords: system of equations, linear solver, Gaussian elimination.
    """
    return await linalg_ops.solve(a, b)

@mcp.tool()
async def inv(a: NumericData) -> List[Any]: 
    """CALCULATES multiplicative inverse. [ACTION]
    
    [RAG Context]
    Finds the matrix `A^-1` such that `A @ A^-1 = I` (Identity).
    
    Keywords: matrix inversion, reciprocal matrix, solve division.
    """
    return await linalg_ops.inv(a)

@mcp.tool()
async def pinv(a: NumericData) -> List[Any]: 
    """CALCULATES Moore-Penrose pseudo-inverse. [ACTION]
    
    [RAG Context]
    """
    return await linalg_ops.pinv(a)

@mcp.tool()
async def lstsq(a: NumericData, b: NumericData, rcond: str = 'warn') -> Dict[str, Any]: 
    """SOLVES least-squares problem. [ACTION]
    
    [RAG Context]
    """
    return await linalg_ops.lstsq(a, b, rcond)

# ==========================================
# 6. Random
# ==========================================
@mcp.tool()
async def rand_float(size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random floats [0.0, 1.0). [ENTRY]
    
    [RAG Context]
    Returns an array of uniformly distributed random numbers between 0 (inclusive) and 1 (exclusive). 
    
    How to Use:
    - Pass 'size' as a list (e.g., `[100]` for 100 samples, `[3, 3]` for a grid).
    
    Keywords: stochastic, uniform random, noise generation, random sampling.
    """
    return await random_ops.rand_float(size)

@mcp.tool()
async def rand_int(low: int, high: Optional[int] = None, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random integers. [ENTRY]
    
    [RAG Context]
    Returns random integers from 'low' (inclusive) to 'high' (exclusive). 
    
    How to Use:
    - `rand_int(1, 7, [10])` -> Simulates throwing a 6-sided die 10 times.
    
    Keywords: random int, discrete random, stochastics, integer sampling.
    """
    return await random_ops.rand_int(low, high, size)

@mcp.tool()
async def rand_normal(loc: float = 0.0, scale: float = 1.0, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Normal/Gaussian). [ENTRY]
    
    [RAG Context]
    Draws random samples from a Normal (Gaussian) distribution. The Bell Curve.
    
    Arguments:
    - loc: Mean ("center").
    - scale: Standard deviation ("width").
    
    Keywords: gaussian noise, normal distribution, bell curve, natural variability.
    """
    return await random_ops.rand_normal(loc, scale, size)

@mcp.tool()
async def rand_uniform(low: float = 0.0, high: float = 1.0, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Uniform). [ENTRY]
    
    [RAG Context]
    """
    return await random_ops.rand_uniform(low, high, size)

@mcp.tool()
async def rand_choice(a: NumericData, size: Optional[List[int]] = None, replace: bool = True, p: Optional[NumericData] = None) -> List[Any]: 
    """GENERATES random sample from 1-D array. [ENTRY]
    
    [RAG Context]
    Picks random items from a provided set.
    
    How to Use:
    - 'p': An array of probabilities for each item in 'a' (must sum to 1.0).
    - 'replace': Whether the same item can be picked twice.
    
    Keywords: weighted choice, random selection, pick from list, sampling.
    """
    return await random_ops.rand_choice(a, size, replace, p)

@mcp.tool()
async def shuffle(x: NumericData) -> List[Any]: 
    """SHUFFLES array in-place. [ACTION]
    
    [RAG Context]
    Randomizes the order of elements in the array.
    
    Keywords: randomize order, scrambling, data mix.
    """
    return await random_ops.shuffle(x)

@mcp.tool()
async def permutation(x: Union[int, NumericData]) -> List[Any]: 
    """PERMUTES sequence randomly. [ACTION]
    
    [RAG Context]
    """
    return await random_ops.permutation(x)

# Dist
@mcp.tool()
async def rand_beta(a: float, b: float, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Beta). [ENTRY]
    
    [RAG Context]
    Draws samples from a Beta distribution, defined on the interval [0, 1].
    
    How to Use:
    - Used in Bayesian inference to model probabilities.
    
    Keywords: beta distribution, bayesian, probability sampling.
    """
    return await random_ops.rand_beta(a, b, size)

@mcp.tool()
async def rand_binomial(n: int, p: float, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Binomial). [ENTRY]
    
    [RAG Context]
    """
    return await random_ops.rand_binomial(n, p, size)

@mcp.tool()
async def rand_chisquare(df: float, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Chi-Square). [ENTRY]
    
    [RAG Context]
    """
    return await random_ops.rand_chisquare(df, size)

@mcp.tool()
async def rand_gamma(shape: float, scale: float = 1.0, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Gamma). [ENTRY]
    
    [RAG Context]
    """
    return await random_ops.rand_gamma(shape, scale, size)

@mcp.tool()
async def rand_poisson(lam: float = 1.0, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Poisson). [ENTRY]
    
    [RAG Context]
    Draws samples from a Poisson distribution. 
    
    How to Use:
    - Models the number of events occurring in a fixed interval of time (e.g., website clicks per hour).
    
    Keywords: poisson, event count, arrival rate, queueing theory.
    """
    return await random_ops.rand_poisson(lam, size)

@mcp.tool()
async def rand_exponential(scale: float = 1.0, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples (Exponential). [ENTRY]
    
    [RAG Context]
    """
    return await random_ops.rand_exponential(scale, size)

# ==========================================
# 7. FFT & Super
# ==========================================
@mcp.tool()
async def fft(a: NumericData, n: Optional[int] = None, axis: int = -1) -> Dict[str, Any]: 
    """COMPUTES 1-D Discrete Fourier Transform. [ACTION]
    
    [RAG Context]
    Transforms time-domian data into the frequency domain. Essential for signal analysis, spectral density estimation, and data compression.
    
    How to Use:
    - Input 'a' can be a real or complex vector.
    - Returns a dictionary with 'real' and 'imag' parts.
    
    Keywords: dft, frequency domain, signal processing, spectral analysis.
    """
    return await fft_ops.fft(a, n, axis)

@mcp.tool()
async def ifft(a_real: NumericData, a_imag: Optional[NumericData] = None, n: Optional[int] = None, axis: int = -1) -> List[Any]: 
    """COMPUTES Inverse 1-D DFT. [ACTION]
    
    [RAG Context]
    """
    return await fft_ops.ifft(a_real, a_imag, n, axis)

@mcp.tool()
async def fft2(a: NumericData, s: Optional[List[int]] = None) -> Dict[str, Any]: 
    """COMPUTES 2-D Discrete Fourier Transform. [ACTION]
    
    [RAG Context]
    """
    return await fft_ops.fft2(a, s)

@mcp.tool()
async def fftfreq(n: int, d: float = 1.0) -> List[float]: 
    """RETURNS DFT sample frequencies. [DATA]
    
    [RAG Context]
    Calculates the frequency bins for a Fourier Transform of length 'n'.
    
    Keywords: frequency bins, spectral axis, sample frequency.
    """
    return await fft_ops.fftfreq(n, d)

@mcp.tool()
async def analyze_array(data: NumericData) -> Dict[str, Any]: 
    """PERFORMS comprehensive array analysis. [ENTRY]
    
    [RAG Context]
    A "Super Tool" for initial data exploration. Evaluates basic statistics (mean, median, std), identifies outliers, checks for NaN/Infinity values, and computes a data histogram.
    
    Keywords: array profiling, data health, outlier check, summary stats.
    """
    return await super_ops.analyze_array(data)

@mcp.tool()
async def matrix_dashboard(data: NumericData) -> Dict[str, Any]: 
    """GENERATES matrix health dashboard. [ENTRY]
    
    [RAG Context]
    A specialized diagnostic tool for 2D matrices. Analyzes numerical stability by calculating the Condition Number, Rank, Eigenvalues, and Sparsity.
    
    Keywords: matrix stability, condition number, numerical rank, matrix health.
    """
    return await super_ops.matrix_dashboard(data)

@mcp.tool()
async def compare_arrays(a: NumericData, b: NumericData) -> Dict[str, Any]: 
    """COMPARES two arrays (MSE, Max Diff). [ENTRY]
    
    [RAG Context]
    """
    return await super_ops.compare_arrays(a, b)

# ==========================================
# 8. Bitwise (Ultimate)
# ==========================================
@mcp.tool()
async def bitwise_and(x1: NumericData, x2: NumericData) -> List[Any]: 
    """COMPUTES bitwise AND. [ACTION]
    
    [RAG Context]
    Performs the bitwise logical AND operation on every element.
    
    Keywords: masking, binary and, bitwise logic.
    """
    return await bitwise_ops.bitwise_and(x1, x2)

@mcp.tool()
async def bitwise_or(x1: NumericData, x2: NumericData) -> List[Any]: 
    """COMPUTES bitwise OR. [ACTION]
    
    [RAG Context]
    """
    return await bitwise_ops.bitwise_or(x1, x2)

@mcp.tool()
async def bitwise_xor(x1: NumericData, x2: NumericData) -> List[Any]: 
    """COMPUTES bitwise XOR. [ACTION]
    
    [RAG Context]
    """
    return await bitwise_ops.bitwise_xor(x1, x2)

@mcp.tool()
async def bitwise_not(x: NumericData) -> List[Any]: 
    """COMPUTES bitwise inversion (NOT). [ACTION]
    
    [RAG Context]
    """
    return await bitwise_ops.bitwise_not(x)

@mcp.tool()
async def left_shift(x1: NumericData, x2: NumericData) -> List[Any]: 
    """SHIFTS bits to the left. [ACTION]
    
    [RAG Context]
    """
    return await bitwise_ops.left_shift(x1, x2)

@mcp.tool()
async def right_shift(x1: NumericData, x2: NumericData) -> List[Any]: 
    """SHIFTS bits to the right. [ACTION]
    
    [RAG Context]
    """
    return await bitwise_ops.right_shift(x1, x2)

@mcp.tool()
async def binary_repr(num: int, width: Optional[int] = None) -> str: 
    """RETURNS binary representation string. [DATA]
    
    [RAG Context]
    """
    return await bitwise_ops.binary_repr(num, width)

# ==========================================
# 9. Strings (Ultimate)
# ==========================================
@mcp.tool()
async def char_add(x1: Union[List[str], str], x2: Union[List[str], str]) -> List[str]: 
    """CONCATENATES strings element-wise. [ACTION]
    
    [RAG Context]
    Combines strings from two arrays (NumPy string arrays) element-wise.
    
    Keywords: string concat, join text, text merge.
    """
    return await string_ops.char_add(x1, x2)

@mcp.tool()
async def char_multiply(a: Union[List[str], str], i: int) -> List[str]: 
    """REPEATS strings element-wise. [ACTION]
    
    [RAG Context]
    """
    return await string_ops.char_multiply(a, i)

@mcp.tool()
async def char_upper(a: Union[List[str], str]) -> List[str]: 
    """CONVERTS strings to uppercase. [ACTION]
    
    [RAG Context]
    """
    return await string_ops.char_upper(a)

@mcp.tool()
async def char_lower(a: Union[List[str], str]) -> List[str]: 
    """CONVERTS strings to lowercase. [ACTION]
    
    [RAG Context]
    """
    return await string_ops.char_lower(a)

@mcp.tool()
async def char_replace(a: Union[List[str], str], old: str, new: str, count: Optional[int] = None) -> List[str]: 
    """REPLACES substrings. [ACTION]
    
    [RAG Context]
    """
    return await string_ops.char_replace(a, old, new, count)

@mcp.tool()
async def char_compare_equal(x1: Union[List[str], str], x2: Union[List[str], str]) -> List[bool]: 
    """CHECKS for string equality. [ACTION]
    
    [RAG Context]
    """
    return await string_ops.char_compare_equal(x1, x2)

@mcp.tool()
async def char_count(a: Union[List[str], str], sub: str, start: int = 0, end: Optional[int] = None) -> List[int]: 
    """COUNTS substring occurrences. [DATA]
    
    [RAG Context]
    """
    return await string_ops.char_count(a, sub, start, end)

@mcp.tool()
async def char_find(a: Union[List[str], str], sub: str, start: int = 0, end: Optional[int] = None) -> List[int]: 
    """FINDS lowest index of substring. [DATA]
    
    [RAG Context]
    """
    return await string_ops.char_find(a, sub, start, end)

# ==========================================
# 10. Sets (Ultimate)
# ==========================================
@mcp.tool()
async def unique_counts(ar: NumericData) -> Dict[str, Any]: 
    """RETURNS unique elements and counts. [DATA]
    
    [RAG Context]
    Provides a frequency breakdown of all unique values in the array.
    
    Keywords: value counts, histogram data, distinct elements.
    """
    return await set_ops.unique_counts(ar)

@mcp.tool()
async def union1d(ar1: NumericData, ar2: NumericData) -> List[Any]: 
    """FINDS union of two arrays. [DATA]
    
    [RAG Context]
    """
    return await set_ops.union1d(ar1, ar2)

@mcp.tool()
async def intersect1d(ar1: NumericData, ar2: NumericData) -> List[Any]: 
    """FINDS intersection of two arrays. [DATA]
    
    [RAG Context]
    """
    return await set_ops.intersect1d(ar1, ar2)

@mcp.tool()
async def setdiff1d(ar1: NumericData, ar2: NumericData) -> List[Any]: 
    """FINDS set difference of two arrays. [DATA]
    
    [RAG Context]
    """
    return await set_ops.setdiff1d(ar1, ar2)

@mcp.tool()
async def setxor1d(ar1: NumericData, ar2: NumericData) -> List[Any]: 
    """FINDS set exclusive-or of two arrays. [DATA]
    
    [RAG Context]
    """
    return await set_ops.setxor1d(ar1, ar2)

@mcp.tool()
async def isin(element: NumericData, test_elements: NumericData) -> List[bool]: 
    """TESTS whether elements are in test set. [DATA]
    
    [RAG Context]
    """
    return await set_ops.isin(element, test_elements)

# ==========================================
# 11. Polynomials (Ultimate)
# ==========================================
@mcp.tool()
async def poly_fit(x: NumericData, y: NumericData, deg: int) -> Dict[str, Any]: 
    """FITS a polynomial. [ACTION]
    
    [RAG Context]
    Performs Least Squares Polynomial Fit.
    
    How to Use:
    - Finds the coefficients of a polynomial of 'deg' that best matches data (x, y).
    
    Keywords: curve fitting, regression, polynomial model, data modeling.
    """
    return await poly_ops.poly_fit(x, y, deg)

@mcp.tool()
async def poly_val(coef: List[float], x: NumericData) -> List[float]: 
    """EVALUATES a polynomial at x. [ACTION]
    
    [RAG Context]
    """
    return await poly_ops.poly_val(coef, x)

@mcp.tool()
async def poly_roots(coef: List[float]) -> List[Any]: 
    """FINDS roots of a polynomial. [DATA]
    
    [RAG Context]
    """
    return await poly_ops.poly_roots(coef)

@mcp.tool()
async def poly_from_roots(roots: List[float]) -> List[float]: 
    """GENERATES polynomial from roots. [ACTION]
    
    [RAG Context]
    """
    return await poly_ops.poly_from_roots(roots)

@mcp.tool()
async def poly_derivative(coef: List[float], m: int = 1) -> List[float]: 
    """DIFFERENTIATES a polynomial. [ACTION]
    
    [RAG Context]
    """
    return await poly_ops.poly_derivative(coef, m)

@mcp.tool()
async def poly_integrate(coef: List[float], m: int = 1) -> List[float]: 
    """INTEGRATES a polynomial. [ACTION]
    
    [RAG Context]
    """
    return await poly_ops.poly_integrate(coef, m)

# ==========================================
# 12. Stats Plus (Ultimate)
# ==========================================
@mcp.tool()
async def histogram(a: NumericData, bins: Union[int, str] = 10, range: Optional[List[float]] = None) -> Dict[str, Any]: 
    """COMPUTES histogram of a set of data. [DATA]
    
    [RAG Context]
    Calculates the frequency distribution of continuous data.
    
    How to Use:
    - Returns bin counts and bin edges.
    
    Keywords: distribution, binning, data density.
    """
    return await stat_plus_ops.histogram(a, bins, range)

@mcp.tool()
async def bincount(x: NumericData, minlength: int = 0) -> List[int]: 
    """COUNTS occurrences of non-negative ints. [DATA]
    
    [RAG Context]
    """
    return await stat_plus_ops.bincount(x, minlength)

@mcp.tool()
async def digitize(x: NumericData, bins: List[float], right: bool = False) -> List[int]: 
    """RETURNS indices of bins for values. [DATA]
    
    [RAG Context]
    """
    return await stat_plus_ops.digitize(x, bins, right)

@mcp.tool()
async def correlate(a: NumericData, v: NumericData, mode: str = 'valid') -> List[float]: 
    """COMPUTES cross-correlation. [ACTION]
    
    [RAG Context]
    """
    return await stat_plus_ops.correlate(a, v, mode)

@mcp.tool()
async def convolve(a: NumericData, v: NumericData, mode: str = 'full') -> List[float]: 
    """COMPUTES convolution. [ACTION]
    
    [RAG Context]
    """
    return await stat_plus_ops.convolve(a, v, mode)

@mcp.tool()
async def cov(m: NumericData) -> List[List[float]]: 
    """ESTIMATES covariance matrix. [DATA]
    
    [RAG Context]
    Measures the joint variability of multiple variables (features).
    
    Keywords: covariance, correlations, variances, joint variability.
    """
    return await stat_plus_ops.cov(m)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class NumpyServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

