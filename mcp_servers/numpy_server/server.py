
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
    """CREATES an array of zeros for initialization and placeholders. [ENTRY]
    
    [RAG Context]
    A fundamental "Super Tool" for memory pre-allocation and baseline initialization in numerical computing. In high-performance algorithms, it is statistically more efficient to pre-allocate the memory needed for a large matrix as a "blank slate" of zeros rather than appending values row-by-row, which causes expensive memory re-allocations. This tool generates a new array of any dimensionality (1D, 2D, or higher) where every single element is initialized to exactly 0.0, providing a neutral starting point for accumulators, image buffers, or masking operations.
    
    How to Use:
    - 'shape': A list defining the dimensions (e.g., `[100]` for a simple vector, `[10, 10]` for a 2D matrix).
    - Use this tool whenever you know the required size of your output data but have not yet calculated the values.
    - Standard practice for initializing "mask" arrays or gradient buffers in deep learning and signal processing.
    
    Keywords: zero initialization, memory pre-allocation, blank array, buffer setup, numerical placeholder, baseline matrix.
    """
    return await creation_ops.create_zeros(shape)

@mcp.tool()
async def create_ones(shape: List[int]) -> List[Any]: 
    """CREATES an array of ones for constant initialization and scaling. [ENTRY]
    
    [RAG Context]
    A versatile "Super Tool" for creating unit-value matrices and reference benchmarks. Initializing an array where every element is exactly 1.0 is essential for operations involving multiplicative identities, normalization, or creating weighting masks that treat all data points equally by default. This tool enables the rapid generation of multidimensional arrays that serve as the "multiplicative neutral" starting point for sophisticated linear algebra operations, such as creating offset vectors or initializing neural network weights (though specialized initializers are often used there, 'ones' remain a core primitive).
    
    How to Use:
    - 'shape': The desired dimensions (e.g., `[5, 5]` for a 5x5 square matrix).
    - Ideal for creating "multiplication masks" where you want to preserve values in certain regions while potentially zeroing out others later.
    - Often used in signal processing to represent a "constant DC offset" or as a baseline for unit-testing mathematical formulas.
    
    Keywords: unit initialization, ones array, multiplicative identity, scaling baseline, constant matrix, unit vector.
    """
    return await creation_ops.create_ones(shape)

@mcp.tool()
async def create_full(shape: List[int], fill_value: Union[float, int]) -> List[Any]: 
    """CREATES an array filled with a specific constant value. [ENTRY]
    
    [RAG Context]
    A highly convenient "Super Tool" for initializing homogenous datasets with a custom baseline. While 'zeros' and 'ones' are common, many workflows require arrays pre-populated with a specific value like -1.0 (for padding), 0.5 (for default probabilities), or even large numbers (for infinity placeholders). This tool removes the need for two-step operations (creating zeros then adding a value), allowing the system to instantiate and fill memory in a single, efficient atomic operation. This is particularly useful for initializing cost matrices, default state buffers, or creating homogenous backgrounds for image processing tasks.
    
    How to Use:
    - 'shape': The array dimensions.
    - 'fill_value': The specific number to replicate across every element.
    - Use this to set "default" parameters across a wide search space or to initialize data structures with known boundary values (like 255 for a white image canvas).
    
    Keywords: constant fill, uniform initialization, homogenous array, custom baseline, value replication, buffer filling.
    """
    return await creation_ops.create_full(shape, fill_value)

@mcp.tool()
async def arange(start: float, stop: float = None, step: float = 1) -> List[float]: 
    """CREATES evenly spaced values over an interval with a fixed step size. [ENTRY]
    
    [RAG Context]
    A fundamental "Super Tool" for sequence generation and iterative indexing. Unlike Python's native `range()`, which is limited to integers, `arange` allows for the high-speed generation of floating-point sequences. This is the primary tool for creating coordinate grids, time-step vectors for simulations, or discrete "bucket" boundaries for histogram analysis. It generates a sequence that starts at a given value and proceeds by a defined step until reaching a termination boundary, making it indispensable for any task involving linear progression or sequential data access.
    
    How to Use:
    - 'start': The beginning of the sequence.
    - 'stop': The "exclusive" end-point (the sequence ends just before reaching this).
    - 'step': The distance between each adjacent number.
    - Example: `arange(0, 1, 0.1)` produces 10 points from 0.0 to 0.9.
    - Use this whenever you need a predictable, ordered series of numbers for plotting or mathematical iteration.
    
    Keywords: numeric sequence, range generation, step progression, coordinate vector, linear sequence, iterative indexing.
    """
    return await creation_ops.arange(start, stop, step)

@mcp.tool()
async def linspace(start: float, stop: float, num: int = 50) -> List[float]: 
    """CREATES evenly spaced values over an interval with a fixed sample count. [ENTRY]
    
    [RAG Context]
    An elite "Super Tool" for precision interval division and sampling. While 'arange' focuses on the *step* between numbers, 'linspace' focuses on the final *count* of points between two boundaries. This is the standard tool for generating sampling grids for function plotting, creating smooth gradients for computer graphics, or defining the discrete frequency bins for digital signal processing. It ensures that the sequence starts exactly at 'start' and ends exactly at 'stop' (inclusive), guaranteeing that the entire range is perfectly partitioned into equal segments regardless of how complex the decimal math might be.
    
    How to Use:
    - 'num': The number of samples to generate (default is 50).
    - Unlike 'arange', the endpoint is included by default, making it superior for tasks where boundary accuracy is paramount.
    - Use this to generate the "X-Axis" for mathematical plots or to create a set of test points across a range to find a function's maximum or minimum.
    
    Keywords: linear interpolation, sample generation, range partitioning, plotting grid, uniform interval, interval division.
    """
    return await creation_ops.linspace(start, stop, num)

@mcp.tool()
async def logspace(start: float, stop: float, num: int = 50, base: float = 10.0) -> List[float]: 
    """CREATES logarithmically spaced values over several orders of magnitude. [ENTRY]
    
    [RAG Context]
    A specialized "Super Tool" for analyzing phenomena that change exponentially. In the physical world, many things (like sound volume, earthquake intensity, or financial growth) are better understood on a logarithmic scale rather than a linear one. This tool generates a sequence of numbers that are evenly spaced on a log scale—meaning the *ratio* between adjacent numbers is constant rather than the *difference*. It is essential for creating frequency sweeps in acoustics, designing search grids for machine learning hyperparameters (like learning rates), or analyzing long-term compound interest scenarios.
    
    How to Use:
    - 'start' and 'stop': These represent the *exponents* (e.g., if base is 10, start=1 means 10^1 = 10).
    - 'base': The logarithmic base (defaults to 10.0).
    - Perfect for when you need to cover a vast range of values (e.g., from 0.001 to 100,000) with a limited number of sampling points.
    
    Keywords: log scale, exponential sequence, frequency sweep, order of magnitude, geometric progression, scale-invariant sampling.
    """
    return await creation_ops.logspace(start, stop, num, base)

@mcp.tool()
async def geomspace(start: float, stop: float, num: int = 50) -> List[float]: 
    """CREATES geometrically spaced values (constant ratio). [ENTRY]
    
    [RAG Context]
    A precise "Super Tool" for creating geometric progressions where the ratio between successive terms is constant. While similar to 'logspace', this tool allows you to specify the actual start and end values directly rather than their exponents. This makes it much more intuitive for practical engineering and finance tasks, such as modeling population growth, calculating interest schedules, or defining the physical layers of a neural network that should decrease in size by a fixed percentage at each step. It ensures a perfectly smooth exponential transition between your chosen bounds.
    
    How to Use:
    - Provide the literal 'start' and 'stop' values (e.g., `start=1, stop=1000`).
    - Use this instead of 'linspace' when the phenomenon you are modeling has a "scale-invariant" nature or when an increase from 1 to 2 is just as significant as an increase from 100 to 200.
    
    Keywords: geometric sequence, progression, constant ratio growth, exponential sweep, scale-invariant sampling.
    """
    return await creation_ops.geomspace(start, stop, num)

@mcp.tool()
async def eye(N: int, M: Optional[int] = None, k: int = 0) -> List[List[float]]: 
    """CREATES a 2D identity matrix or its variation. [ENTRY]
    
    [RAG Context]
    A foundational "Super Tool" for linear algebra and coordinate transformations. An Identity Matrix is a square matrix with ones on the main diagonal and zeros everywhere else; it acts as the "numerical equivalent of the number 1" for matrix multiplication. If you multiply any matrix by the identity matrix, the original remains unchanged. This tool is essential for initializing transformation matrices in computer graphics, solving systems of linear equations, and for "One-Hot" encoding logic where you need to map a categorical index to a unique vector representation.
    
    How to Use:
    - 'N': Number of rows.
    - 'M': Optional number of columns (defaults to N for a square matrix).
    - 'k': The shift of the diagonal (0 is the center, positive is above, negative is below).
    - Perfect for creating unit-transformation foundations or for extracting/isolating specific diagonal relationships in a dataset.
    
    Keywords: identity matrix, unit matrix, diagonal ones, linear transformation, coordinate foundation, matrix identity.
    """
    return await creation_ops.eye(N, M, k)

@mcp.tool()
async def identity(n: int) -> List[List[float]]: 
    """CREATES a square identity matrix (Special case of 'eye'). [ENTRY]
    
    [RAG Context]
    A high-speed "Super Tool" specifically optimized for the most common linear algebra requirement: the square identity matrix. Unlike the more flexible 'eye' tool, 'identity' is designed solely for generating NxN matrices with ones on the main diagonal. This tool is the standard "building block" for initializing iterative solvers, finding matrix inverses, and implementing algorithms like Principal Component Analysis (PCA) where orthogonality must be preserved. It provides a clean, unambiguous way to express the core unit of a multi-dimensional space.
    
    How to Use:
    - 'n': The size of the square matrix (e.g., 3 for a 3x3 matrix).
    - Use this whenever your math requires a "base state" for a square transformation or as a starting point for diagonal-only matrices.
    
    Keywords: square identity, unit matrix, neutral transformation, pca foundation, matrix base, linear algebra unit.
    """
    return await creation_ops.identity(n)

@mcp.tool()
async def diag(v: NumericData, k: int = 0) -> List[Any]: 
    """EXTRACTS or CONSTRUCTS a diagonal matrix. [ENTRY]
    
    [RAG Context]
    A dual-purpose "Super Tool" for manipulating the diagonal backbone of matrices. It serves two distinct and critical roles: it can either "collapse" a 2D matrix down to just its diagonal elements (extraction) or "expand" a 1D vector into a square 2D matrix where that vector forms the diagonal (construction). This is the primary engine for calculating the "Trace" of a matrix, creating "Scaling Matrices" where individual dimensions are weighted differently, and for isolating the variance components in covariance matrices.
    
    How to Use:
    - Construction: Pass a 1D list `[1, 2, 3]` to get a 3x3 matrix where the diagonal is 1, 2, 3.
    - Extraction: Pass a 2D matrix to receive a simple list of its diagonal values.
    - 'k': Use to target the diagonals above or below the center.
    - Essential for sophisticated linear algebra operations and for identifying the "Self-Relationship" in data correlation tables.
    
    Keywords: diagonal matrix, trace extraction, matrix scaling, backbone construction, eigenvalue alignment, diagonal isolation.
    """
    return await creation_ops.diag(v, k)

@mcp.tool()
async def vander(x: List[float], N: Optional[int] = None) -> List[List[float]]: 
    """GENERATES a Vandermonde matrix from a vector. [ENTRY]
    
    [RAG Context]
    An advanced "Super Tool" primarily used for polynomial interpolation and curve fitting. A Vandermonde matrix has the property that each row is a geometric progression based on the elements of the input vector 'x'. This specific structure is the mathematical key to solving the coefficients of a polynomial that passes through a given set of points. It is widely used in signal processing (for discrete Fourier transforms), coding theory (Reed-Solomon codes), and in statistics for creating "Polynomial Regression" models that can follow complex trends that a simple straight line would miss.
    
    How to Use:
    - 'x': The input points.
    - 'N': The number of columns in the output (determines the degree of the polynomial).
    - If you are building a system to "Predict the next number" based on an irregular sequence, the Vandermonde matrix is often the underlying mathematical engine used to perform the fit.
    
    Keywords: vandermonde, polynomial interpolation, curve fitting, coefficient solver, geometric matrix, regression foundation.
    """
    return await creation_ops.vander(x, N)

# ==========================================
# 2. Manipulation
# ==========================================
@mcp.tool()
async def reshape(a: NumericData, newshape: List[int]) -> List[Any]: 
    """RESHAPES an array into a new dimensional configuration. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for data structural transformation and algorithmic compatibility. In high-performance computing, the "shape" of data is just as important as the values themselves. Reshaping allows the system to change the organizational perspective of a dataset—for example, turning a flat list of 1,000 prices into a 10x10x10 cube for 3D analysis—without ever moving or copying the underlying numbers in memory. This tool is the bridge between different stages of a pipeline, such as flattening an image for a neural network's input or converting a multi-channel signal into a series of individual processing tracks.
    
    How to Use:
    - 'newshape': A list defining the new dimensions (e.g., `[2, 500]`).
    - The total number of elements MUST remain exactly the same.
    - Tip: Use `-1` for one of the dimensions (e.g., `[-1, 10]`) to let oxygen calculate the correct size automatically based on the remaining data.
    
    Keywords: dimensional reshaping, tensor reformulating, shape transformation, data view update, structural resizing, matrix reformatting.
    """
    return await manip_ops.reshape(a, newshape)

@mcp.tool()
async def flatten(a: NumericData) -> List[Any]: 
    """FLATTENS a multi-dimensional array into a simple 1D sequence. [ACTION]
    
    [RAG Context]
    A vital "Super Tool" for data simplification and vectorization. When performing operations that treat every data point as an independent sample—such as calculating a global average, finding a total sum, or preparing multi-dimensional data for a standard classifier—you must often "collapse" the complex hierarchy into a single linear progression. This tool removes all dimensional boundaries (rows, columns, planes), providing a "stream" of values that is easy to iterate over or process as a single mathematical vector. It is a mandatory preprocessing step for moving from specialized tensor operations to general-purpose statistical analysis.
    
    How to Use:
    - Use this whenever you need to "Reset" the structure of your data before feeding it into a tool that expects a simple list.
    - Essential for converting 2D images or 3D volumes into a format suitable for histogram generation or global normalization.
    
    Keywords: 1d flattening, dimensionality collapse, vectorization, sequential normalization, data stream conversion, tensor unrolling.
    """
    return await manip_ops.flatten(a)

@mcp.tool()
async def transpose(a: NumericData, axes: Optional[List[int]] = None) -> List[Any]: 
    """PERMUTES the axes of an array (Matrix Transpose). [ACTION]
    
    [RAG Context]
    An advanced "Super Tool" for orienting mathematical operations and swapping data perspectives. In 2D space, transposing "flips" a matrix over its main diagonal, effectively turning its rows into columns and vice versa. This is a primary requirement for many linear algebra algorithms, such as computing the dot product of two vectors or solving systems of equations. For high-dimensional "Tensors" (3D+), this tool allows you to re-order the entire hierarchy—for example, moving the "Time" axis to the front of a video dataset to process frames sequentially across all pixels simultaneously.
    
    How to Use:
    - 'axes': An optional list defining the new order of dimension indices (e.g., `[1, 0]` for a 2D swap).
    - If no axes are provided, it performs a complete reversal of the dimension order.
    - Critical for aligning data before performing matrix multiplications or when moving between different convolutional layer configurations.
    
    Keywords: matrix transpose, axes permutation, dimension swapping, structural orientation, linear algebra flip, tensor rotation.
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
    """ROLLS (circularly shifts) array elements along a specified axis. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for cyclic data manipulation and temporal alignment. Unlike a standard shift where data "falls off" the edge, 'roll' treats the array as a continuous loop: any element pushed off the end automatically reappears at the beginning. This "Circular Buffer" behavior is essential for signal processing tasks involving periodic boundaries (like Fourier Transforms), for synchronizing time-series data where there is a constant phase offset, and for implementing "sliding window" features in machine learning pipelines where the data is wrap-around in nature (like 360-degree panoramic images).
    
    How to Use:
    - 'shift': The number of positions to move. Positive moves elements forward; negative moves them backward.
    - 'axis': The dimension to shift along. If None, the array is flattened before shifting.
    - Perfect for modeling circular queues, time-delay offsets, and periodic physical phenomena.
    
    Keywords: circular shift, element rotation, cyclic buffer, temporal alignment, phase shifting, periodic wrapping.
    """
    return await manip_ops.roll(a, shift, axis)

@mcp.tool()
async def concatenate(arrays: List[NumericData], axis: int = 0) -> List[Any]: 
    """JOINS a sequence of arrays along an existing axis. [ACTION]
    
    [RAG Context]
    A high-capacity "Super Tool" for data fusion and dataset assembly. Concatenation is the primary method for growing a dataset by "gluing" new records or features onto an existing block of memory. It allows the system to combine multiple smaller arrays into one continuous large array without changing the number of dimensions. This is the numerical equivalent of 'appending' to a list, but optimized for multi-dimensional tensors. It is essential for merging daily log files into monthly reports, combining different sensor tracks into a unified multi-channel stream, or for expanding a training set with new observations.
    
    How to Use:
    - 'arrays': The list of arrays to combine.
    - 'axis': The dimension to join along (default is 0).
    - Note: All arrays must have identical shapes in all dimensions *except* the one being joined.
    - Use this for "End-to-End" or "Side-by-Side" data enlargement.
    
    Keywords: array joining, data fusion, tensor merging, vector appending, dataset assembly, memory concatenation.
    """
    return await manip_ops.concatenate(arrays, axis)

@mcp.tool()
async def stack(arrays: List[NumericData], axis: int = 0) -> List[Any]: 
    """STACKS arrays into a higher-dimensional configuration. [ACTION]
    
    [RAG Context]
    A sophisticated "Super Tool" for structural promotion and batch data preparation. Unlike 'concatenate' (which glues arrays along an existing dimension), 'stack' creates an entirely *new* dimension to house the provided arrays. Think of it as taking individual pieces of paper (1D or 2D) and stacking them on top of each other to create a book (2D or 3D). This is a mandatory operation for preparing "Batches" in Deep Learning—where you stack 32 individual 2D images to create one 4D processing block—and for building multi-layered temporal snapshots of a system's state.
    
    How to Use:
    - All input arrays MUST have identical shapes.
    - 'axis': Defines where the new dimension will be inserted (0 for the front, -1 for the end).
    - Ideal for turning a sequence of spatial maps into a temporal volume or converting a list of features into a multi-channel input tensor.
    
    Keywords: dimensional stacking, structure promotion, batch creation, tensor layering, coordinate expansion, multi-array fusion.
    """
    return await manip_ops.stack(arrays, axis)

@mcp.tool()
async def vstack(tup: List[NumericData]) -> List[Any]: 
    """STACKS arrays vertically (row-wise). [ACTION]
    
    [RAG Context]
    A convenient "Super Tool" for expanding the rows of a dataset. Vertical Stacking (vstack) specializes in "piling" arrays on top of each other. For 1D vectors, it automatically promotes them into rows of a 2D matrix. For existing 2D matrices, it appends them vertically. This is the primary method for adding new "Observations" or "Samples" to a data table, rebuilding a master file from partitioned row-blocks, and for preparing long-form data frames for statistical modeling. It provides a standardized way to grow data in the "vertical" dimension without manual reshaping.
    
    How to Use:
    - Pass a list of arrays that have matching horizontal dimensions (number of columns).
    - Perfect for combining results from parallel processing tasks where each worker produced a subset of the final rows.
    
    Keywords: vertical stacking, row appending, matrix building, observations fusion, vertical concatenation, data piling.
    """
    return await manip_ops.vstack(tup)

@mcp.tool()
async def hstack(tup: List[NumericData]) -> List[Any]: 
    """STACKS arrays horizontally (column-wise). [ACTION]
    
    [RAG Context]
    A convenient "Super Tool" for expanding the features of a dataset. Horizontal Stacking (hstack) specializes in "gluing" arrays side-by-side. It is the primary method for adding new "Variables" or "Features" to an existing dataset (e.g., adding a 'Temperature' column to a matrix that already has 'Time' and 'Pressure'). This tool is essential for feature engineering pipelines where multiple independent processing branches each generate a new dimensional attribute that must be fused into a final "Wide" feature vector before being passed to a classifier or regression model.
    
    How to Use:
    - Pass a list of arrays that have matching vertical dimensions (number of rows).
    - Unlike 'vstack', this focuses on widening the dataset rather than lengthening it.
    - Ideal for multi-modal data fusion where different sensors contribute different data types for the same time-step.
    
    Keywords: horizontal join, feature stacking, column appending, matrix widening, lateral data fusion, variable assembly.
    """
    return await manip_ops.hstack(tup)

@mcp.tool()
async def split(ary: NumericData, indices_or_sections: Union[int, List[int]], axis: int = 0) -> List[List[Any]]: 
    """SPLITS an array into multiple sub-sections. [ACTION]
    
    [RAG Context]
    A high-precision "Super Tool" for data partitioning and distributed processing. Splitting allows the system to divide a single large dataset into smaller, manageable chunks along a chosen axis. This is a fundamental step for "Mini-Batching"—where you split a large training set into smaller groups for optimization—and for "Cross-Validation" in machine learning, where you partition data into 'K' folds. It ensures that the dimensional structure of the data remains intact within each sub-portion, making them ready for independent parallel processing or selective analysis.
    
    How to Use:
    - 'indices_or_sections': 
        - Pass an integer (e.g., 4) to split the data into 4 equal parts.
        - Pass a list (e.g., `[100, 200]`) to split at those specific row/column indices (creating chunks 0-99, 100-199, and 200+).
    - Perfect for sharding datasets or isolating specific regions of a multi-dimensional sensor map.
    
    Keywords: array sharding, data partitioning, mini-batching, segmenting, tensor division, data folding.
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
    """REPEATS individual elements of an array. [ACTION]
    
    [RAG Context]
    A flexible "Super Tool" for data upsampling and element-level replication. Unlike 'tile' (which duplicates the entire structure), 'repeat' replicates each individual number within the structure. This is essential for coordinate expansion, where you might need to repeat each "Category ID" multiple times to match an upsampled data stream. It is also a core tool for signal oversampling and for implementing "Zero-Order Hold" logic where a discrete value must be held constant over several subsequent processing steps or time intervals.
    
    How to Use:
    - 'repeats': Number of copies for each element (can be a single integer or a list defining a different count for each element).
    - 'axis': The dimension to repeat along. If None, the array is flattened.
    - Ideal for stretching data to fit a larger coordinate grid or for duplicating training samples to balance imbalanced class distributions.
    
    Keywords: element replication, data upsampling, stretch array, oversampling, value duplication, coordinate expansion.
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
    """TRIMS leading and trailing zeros from a dataset sequence. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for data cleaning and signal normalization. In many automated measurement or recording systems, datasets often contain long sequences of leading or trailing zeros that represent periods of silence, inactivity, or initialization noise. These "empty" regions increase file size and can skew statistical calculations (like means or variances). This tool identifies and excise these zero-only boundaries, providing a "clean" core dataset that focuses exclusively on the active portion of the signal. It is essential for pre-processing time-series data, stripping padding from audio samples, or cleaning up sparse sensor logs.
    
    How to Use:
    - 'trim':
        - 'f': Remove only leading (front) zeros.
        - 'b': Remove only trailing (back) zeros.
        - 'fb': (Default) Remove both ends.
    - Note: This tool only works on 1D sequences. It does not remove zeros from the "middle" of a signal.
    
    Keywords: zero stripping, signal cleaning, dead-zone removal, trim padding, sequence normalization, data core extraction.
    """
    return await manip_ops.trim_zeros(filt, trim)

@mcp.tool()
async def pad(array: NumericData, pad_width: List[Any], mode: str = 'constant', constant_values: Any = 0) -> List[Any]: 
    """PADS array borders with specific values or patterns. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for frame expansion and convolutional preprocessing. Padding increases the outer dimensions of an array by wrapping it in a "border" of new data. This is an absolute requirement for Computer Vision (allowing Convolutional Neural Networks to process the edges of an image properly) and Signal Processing (preventing "edge artifacts" during filtering). Beyond simple zero-padding, this tool can mirror existing data, replicate edge values, or use linear ramps, ensuring that the "context" at the data boundary is preserved according to the specific needs of the algorithm.
    
    How to Use:
    - 'pad_width': Defines how many elements to add at each edge (e.g., `[[1, 1], [2, 2]]` adds 1 element to top/bottom and 2 to left/right).
    - 'mode':
        - 'constant': Fills with 'constant_values' (usually 0).
        - 'edge': Replicates the last known value.
        - 'reflect': Mirrors the data (standard for image filters).
    - Use this to ensure output shapes remain consistent after mathematical operations that would normally shrink the dataset.
    
    Keywords: border padding, frame expansion, cnn preprocessing, edge mirror, array resizing, signal buffering.
    """
    return await manip_ops.pad(array, pad_width, mode, constant_values)

# ==========================================
# 3. Math
# ==========================================
@mcp.tool()
async def add(x1: NumericData, x2: NumericData) -> List[Any]: 
    """PERFORMS element-wise addition with broadcasting support. [ACTION]
    
    [RAG Context]
    A fundamental high-performance "Super Tool" for vector-based arithmetic. Addition in NumPy is exponentially faster than standard Python loops because it utilizes vectorized SIMD (Single Instruction, Multiple Data) processor instructions. This tool adds two arrays element-by-element; if the arrays have different shapes, it automatically applies "Broadcasting" logic to stretch the smaller array across the larger one (e.g., adding a single value to every element in a 1,000x1,000 matrix). This is the primary engine for layering data, applying bias offsets in neural networks, and combining multi-channel signals into a unified sum.
    
    How to Use:
    - 'x1', 'x2': The arrays or scalars to add.
    - If you are applying a "Correction Factor" to an entire dataset, simply pass the dataset as 'x1' and the factor as 'x2'.
    - Note: This is an element-wise operation, not a matrix concatenation.
    
    Keywords: vectorized addition, broadcasting sum, element-wise plus, numeric layering, signal summation, bias offset.
    """
    return await math_ops.add(x1, x2)

@mcp.tool()
async def subtract(x1: NumericData, x2: NumericData) -> List[Any]: 
    """PERFORMS element-wise subtraction with broadcasting support. [ACTION]
    
    [RAG Context]
    A vital "Super Tool" for calculating differences, residuals, and error rates. Vectorized subtraction allows the system to instantly compute the gap between two large datasets (e.g., 'Predicted Values' minus 'Actual Values') in a single operation. Like 'add', it fully supports broadcasting, allowing you to subtract a mean value from an entire population (Mean Centering) to normalize data. This tool is the mathematical core of anomaly detection, where you subtract a "Normal Baseline" from incoming telemetry to isolate the deviation or "Residual" signal.
    
    How to Use:
    - Computes `x1 - x2` for every corresponding pair of elements.
    - Extremely efficient for "Zero-Centering" data during preprocessing or for calculating the "delta" between two state snapshots.
    - Mandatory step for determining loss functions in machine learning and error-correcting codes.
    
    Keywords: vectorized subtraction, numeric difference, mean centering, residual calculation, error detection, delta estimation.
    """
    return await math_ops.subtract(x1, x2)

@mcp.tool()
async def multiply(x1: NumericData, x2: NumericData) -> List[Any]: 
    """PERFORMS element-wise multiplication (Hadamard Product). [ACTION]
    
    [RAG Context]
    A high-speed "Super Tool" for scaling, masking, and weighting data. In vectorized computing, 'multiply' (often called the Hadamard Product) scales every entry in an array by a corresponding value. This is the primary method for applying "Importance Weights" to features, darkening or brightening images by a fixed factor, and implementing "Masking" (where multiplying a region by 0.0 effectively deletes it). It is significantly faster than standard loops and is essential for signal modulation, gain control, and any scenario where one dataset acts as a "filter" or "scaler" for another.
    
    How to Use:
    - Note: This is NOT Matrix Multiplication (use 'matmul' for that). This tool multiplies 1:1.
    - Ideal for applying percentage-based increases across a pricing table or for weighting historical data to give it less impact in a final average.
    
    Keywords: element-wise product, scaling matrix, hadamard product, data weighting, signal modulation, masking operation.
    """
    return await math_ops.multiply(x1, x2)

@mcp.tool()
async def divide(x1: NumericData, x2: NumericData) -> List[Any]: 
    """PERFORMS element-wise division with floating-point precision. [ACTION]
    
    [RAG Context]
    A precise "Super Tool" for data scaling, normalization, and ratio calculation. Vectorized division (calculating `x1 / x2`) is the standard method for converting raw counts into percentages, normalizing feature ranges to a common [0, 1] scale (Min-Max Scaling), and performing physical calculations like "Price per Unit" across thousands of records simultaneously. NumPy's division is robust, correctly handling float promotion to ensure accuracy even when dividing integers. It is the engine behind "Unit Normalization," which ensures that disparate data scales (like 'Age' and 'Income') can be compared fairly by a machine learning model.
    
    How to Use:
    - Ideal for calculating "Density" (Value / Area) or "Rate of Change."
    - Be aware: Division by zero will result in 'Inf' (infinity) or 'NaN'—use 'check_nan' tools after heavy division tasks to ensure data stability.
    
    Keywords: vectorized division, numeric normalization, ratio calculation, percentage scaling, unit scaling, normalization engine.
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
    """CALCULATES the element-wise remainder (Modulus). [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for cyclic logic, periodic indexing, and data sharding. The modulus operator (%) finds the remainder after dividing 'x1' by 'x2'. In numerical systems, this is the primary tool for implementing circular logic (e.g., "What day of the week is it after 100 days?" or "Which processor core should handle this packet index?"). It is essential for generating "Strobe" signals, creating alternating data patterns (odd vs even rows), and for ensuring that array indices always wrap around correctly during complex data rotations or shuffling.
    
    How to Use:
    - `mod(data, 2)`: Returns 0 for every even number and 1 for every odd number.
    - Essential for partitioning large datasets into 'K' buckets using a simple index-based hash.
    - High-performance alternative to logic-heavy 'if' statements for periodic behavior.
    
    Keywords: modulus operator, remainder calculation, cyclic indexing, sharding logic, periodic behavior, hash bucketization.
    """
    return await math_ops.mod(x1, x2)

# Functions
@mcp.tool()
async def abs_val(x: NumericData) -> List[Any]: 
    """CALCULATES the absolute magnitude of every element. [ACTION]
    
    [RAG Context]
    A fundamental "Super Tool" for magnitude estimation and error quantification. Absolute value (ABS) removes the operational sign (+/-) of numbers, returning only their non-negative magnitude. This is a mandatory step for calculating "Mean Absolute Error" (MAE) in forecasting—where we care about how far off a prediction was, regardless of whether it was too high or too low. It is also the primary engine for finding the "Distance" between points on a number line and for cleaning sensor data where negative values might be invalid or represent a different phase of the same physical magnitude.
    
    How to Use:
    - Pass an array containing negative numbers to receive a version where all numbers are positive.
    - Essential for distance-based calculations, non-parametric statistics, and for preparing data for models that only accept non-negative inputs (like certain log-based transformations).
    
    Keywords: absolute magnitude, non-negative value, distance calculation, error quantification, magnitude transform, sign removal.
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
    """CALCULATES the exponential (Euler's number to the power) of all elements. [ACTION]
    
    [RAG Context]
    A high-level "Super Tool" for modeling growth, probability, and activation in biological systems. This tool calculates `e^x` (roughly 2.718 raised to the power of each element) across the entire dataset. In the Kea system, this is the core engine for implementing "Softmax" layers (converting scores into probabilities) and for modeling phenomena that grow exponentially over time, such as compound interest, bacterial reproduction, or viral spread. It is also the foundation of most "log-linear" models used in econometrics and predictive analytics where small changes in input lead to multiplied changes in output.
    
    How to Use:
    - Ideal for undoing a logarithmic transformation ('Log' inversion).
    - Perfect for normalizing relative scores into a strict [0, 1] probability range when combined with a 'sum' operation.
    
    Keywords: exponential growth, eulers number, softmax foundation, probability conversion, log inversion, growth modeling.
    """
    return await math_ops.exp(x)

@mcp.tool()
async def log(x: NumericData) -> List[Any]: 
    """CALCULATES the natural logarithm of all elements. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for data compression, stabilization, and trend smoothing. The Natural Logarithm (ln) is the most common transformation used in statistics to handle "Skewed Data" (where most values are small but a few are massive, like wealth distribution or city populations). By applying 'log', you compress the range of its data, turning multiplicative relationships into additive ones and making "Heavy-Tailed" distributions look more "Normal." This transformation is a mandatory requirement for many linear regression models and for accurately calculating "Continuously Compounded" growth rates in finance.
    
    How to Use:
    - Base: Euler's number (e).
    - Note: This tool will return 'NaN' for zero or negative values, as the log of non-positive numbers is undefined in real space. Always ensure your data is positive before logging.
    - Essential for linearizing exponential trends for traditional analytical tools.
    
    Keywords: natural logarithm, data smoothing, skewness correction, range compression, log transformation, ln calculation.
    """
    return await math_ops.log(x)

@mcp.tool()
async def log10(x: NumericData) -> List[Any]: 
    """CALCULATES the base-10 logarithm of all elements. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for engineering, physics, and decade-based scaling. While natural logs are for growth modeling, the Base-10 Logarithm is the standard for measuring physical quantities that span vast ranges, such as sound intensity (Decibels), earthquake magnitude (Richter Scale), and chemical acidity (pH). It measures exactly how many "powers of ten" a value represents. This tool is essential for visualizing data that spans several orders of magnitude on a single plot and for performing signal strength analysis where power ratios are expressed in log10 units.
    
    How to Use:
    - Ideal for converting linear measurements into "Order of Magnitude" categories.
    - Note: Only accepts positive inputs.
    - Perfect for creating decibel-scale representations of audio or network signal data.
    
    Keywords: base-10 log, decibel scaling, order of magnitude, rickter scale, ph calculation, power ratio transform.
    """
    return await math_ops.log10(x)

@mcp.tool()
async def sqrt(x: NumericData) -> List[Any]: 
    """CALCULATES the non-negative square root of every element. [ACTION]
    
    [RAG Context]
    A foundational "Super Tool" for Euclidean distance calculation and variance analysis. The square root (SQRT) is the inverse operation of squaring and is fundamental to the Pythagorean theorem. In the Kea system, this tool is the primary engine for calculating the "L2 Norm" (Straight-line distance between two vectors), determining "Standard Deviation" from variance, and normalizing magnitudes in physics-based simulations. It is a mandatory step for converting energy-based metrics (which are often squared) back into their original physical units (like voltage or pressure).
    
    How to Use:
    - Calculates the positive root. If the input is negative, it will return 'NaN' in a real-valued array.
    - Essential for calculating the radius of clusters in data analysis and for stabilizing variance in certain statistical distributions.
    
    Keywords: square root extraction, euclidean distance foundation, radical calculation, variance normalization, standard deviation prep, magnitude scaling.
    """
    return await math_ops.sqrt(x)

@mcp.tool()
async def sin(x: NumericData) -> List[Any]: 
    """CALCULATES the trigonometric sine for all elements. [ACTION]
    
    [RAG Context]
    An essential "Super Tool" for signal processing, oscillation modeling, and rotational physics. The sine function describes the vertical component of circular motion and is the building block of all complex waveforms. In the Kea system, this tool is used for generating synthetic audio signals, modeling seasonal business cycles (via Fourier analysis), and calculating the trajectories of objects in multi-dimensional space. It provides the mathematical foundation for "Frequency Domain" analysis, where complex data is broken down into simple periodic waves.
    
    How to Use:
    - IMPORTANT: Expects input values in **Radians** (not degrees). Use the 'deg2rad' tool if your input is in degrees.
    - Output is always constrained between -1.0 and 1.0.
    - Ideal for modeling time-of-day effects or any phenomenon that repeats on a fixed schedule.
    
    Keywords: trigonometric sine, wave generation, periodic modeling, harmonic analysis, oscillation, phase calculation.
    """
    return await math_ops.sin(x)

@mcp.tool()
async def cos(x: NumericData) -> List[Any]: 
    """CALCULATES the trigonometric cosine for all elements. [ACTION]
    
    [RAG Context]
    A foundational "Super Tool" for angular projection and signal phase analysis. While 'sin' tracks vertical movement, the 'cos' function tracks horizontal circular motion. Together, they form the "Quadrature" pair necessary for representing complex numbers and for calculating the "Dot Product"—the mathematical soul of vector similarity search and machine learning. In data science, cosine is is the primary method for calculating "Cosine Similarity," which measures the angular distance between two documents or user profiles to determine how related they are, regardless of their absolute magnitude.
    
    How to Use:
    - Input must be in **Radians**.
    - Essential for resolving vectors into components and for building seasonal models where the peak occurs at a different time than the sine-based model.
    
    Keywords: trigonometric cosine, cosine similarity, vector projection, angular distance, quadrature signal, phase shift.
    """
    return await math_ops.cos(x)

@mcp.tool()
async def tan(x: NumericData) -> List[Any]: 
    """CALCULATES the trigonometric tangent for all elements. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for calculating slopes, gradients, and perspective. The tangent function represents the ratio of 'sin' to 'cos' and geometrically corresponds to the slope of a line at a given angle. In numerical computing, this is the primary tool for determining the "Look-At" vector in 3D simulations, calculating the pitch or bank of an aerial drone, and for mapping geographical coordinates into flat map projections (like the Mercator projection). It is also a core building block for certain optimization algorithms that utilize the "Tangent Line" to find the minimum of a function.
    
    How to Use:
    - Input must be in **Radians**.
    - Beware of periodic singularities (at 90, 270 degrees) where the value approaches infinity.
    - Ideal for engineering tasks involving incline, friction angles, or visual perspective.
    
    Keywords: trigonometric tangent, slope calculation, gradient descent base, angular ratio, inclinometer logic, perspective mapping.
    """
    return await math_ops.tan(x)

@mcp.tool()
async def rad2deg(x: NumericData) -> List[Any]: 
    """CONVERTS values from Radians to Degrees. [ACTION]
    
    [RAG Context]
    A critical "Standardization Tool" for bridging the gap between mathematical theory and human-readable engineering. Most advanced mathematical tools (like 'sin' and 'cos') operate strictly in Radians, but most humans and field sensors (like compasses or gyroscopes) operate in Degrees. This tool performs the precise conversion `(x * 180 / PI)` across the entire dataset, ensuring that internal algorithmic results can be exported as intuitive circular measurements (0 to 360 degrees). It is a mandatory step for generating human-readable angle reports for navigation, construction, or orientation tasks.
    
    How to Use:
    - Use this at the *end* of a trigonometry pipeline to make the final output "human-friendly."
    - 2*PI radians = 360 degrees.
    
    Keywords: radian to degree, angle conversion, human-readable orientation, compass normalization, circular units conversion.
    """
    return await math_ops.rad2deg(x)

@mcp.tool()
async def deg2rad(x: NumericData) -> List[Any]: 
    """CONVERTS values from Degrees to Radians. [ACTION]
    
    [RAG Context]
    A mandatory "Preparation Tool" for all trigonometric computing. Because computers and mathematical primitives work in Radians, any data sourced from human input, GPS devices, or traditional maps must first be converted into the Radian scale before being processed by tools like 'sin', 'cos', or 'arctan'. This tool performs the precise conversion `(x * PI / 180)` and is the "Gatekeeper" that ensures your orientation data is mathematically valid for the NumPy math engine.
    
    How to Use:
    - Use this at the *beginning* of any arithmetic pipeline involving angles or circular paths.
    - 360 degrees = 2*PI radians.
    
    Keywords: degree to radian, trig preprocessing, angle normalization, mathematical units, radian conversion.
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
    """ROUNDS numeric elements to a specific precision or integer level. [ACTION]
    
    [RAG Context]
    A vital "Sanitization Tool" for reporting stability and data presentation. Advanced mathematical operations often result in "Floating Point Noise"—long sequences of decimals (e.g., 0.999999998) that are technically accurate but practically useless. This tool stabilizes the data by rounding it to a specified number of digits. This is essential for financial reporting (rounding to 2 decimals), for bucketizing data into discrete "bins," and for ensuring that two values that "should" be equal are not seen as different due to minor floating-point errors.
    
    How to Use:
    - 'decimals': The number of places to keep. Set to negative values to round to significant powers of ten (e.g., -2 rounds to the nearest 100).
    - Use this at the final stage of an analysis to prepare clear, executive-grade data tables.
    
    Keywords: numeric rounding, precision control, floating point cleanup, decimal stabilization, significant figures, data quantization.
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
    """CALCULATES the product of all elements along a specified axis. [Data]
    
    [RAG Context]
    A high-level "Aggregation Tool" for probability compounding and cumulative scaling. The 'prod' tool multiplies all elements in a group together. This is a fundamental operation in probability theory (calculating the joint probability of independent events), finance (calculating the compounded return of an asset over multiple periods), and in calculating physical "Volumes" from multi-dimensional bounds. Like 'sum', it can operate on the entire array or act as a "Reduction" tool along specific dimensions.
    
    How to Use:
    - axis=None: Multiplies every single number in the array into one final scalar.
    - axis=0 or 1: Multiplies along columns or rows effectively "reducing" those dimensions.
    - Essential for calculating total growth factors and for implementing multiplicative "OR" logic in soft-probabilistic systems.
    
    Keywords: product accumulation, probability compounding, joint likelihood, multiplicative reduction, growth factor, volume calculation.
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
    """CALCULATES the cumulative product (running multiplication). [Data]
    
    [RAG Context]
    A specialized "Tracking Tool" for exponential progression and compound growth analysis. Unlike 'prod', which returns a single result, 'cumprod' returns an array showing the state of the product after every single step. This is the primary engine for calculating "Equity Curves" in trading (showing how a portfolio grows day-by-day), modeling population explosion over generations, and visualizing "Decay Patterns" where values are being exponentially reduced at each step. It allows the system to see the entire *path* of growth rather than just the final destination.
    
    How to Use:
    - Result at row 'i' is the product of all rows from 0 to 'i'.
    - Essential for time-series analysis where each period depends on the multiplied result of all previous periods.
    
    Keywords: running product, compound growth curve, equity path, exponential tracking, multiplicative integration, lifetime compounding.
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
    """CALCULATES the N-dimensional gradient of an array. [Data]
    
    [RAG Context]
    An elite "Analytical Tool" for edge detection, surface analysis, and directional change modeling. The gradient calculates the rate of change (derivative) in all directions for every point in a multi-dimensional grid. In Image Processing, this tool is the core of "Edge Detection"—it identifies where pixels change color most rapidly, revealing the outlines of objects. In Physics and Engineering, it maps the "Slope" of a terrain or the "Pressure Gradient" in a fluid, showing exactly where and how fast values are moving. It is the multivariable foundation for modern optimization techniques like Gradient Descent.
    
    How to Use:
    - Returns a list of arrays (one for each dimension / axis).
    - Input 'f' represents the sampled values of a function.
    - Essential for identifying boundaries in categorical data and for finding the "Steepest Ascent" path in surface modeling.
    
    Keywords: numerical gradient, spatial derivative, edge detection, rate of change, vector field generation, slope mapping.
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
    """PERFORMS element-wise 'Greater Than' comparison. [ACTION]
    
    [RAG Context]
    A high-speed "Logic Tool" for thresholding and anomaly detection. This vectorized tool compares two datasets element-by-element, returning 'True' only where the value in the first dataset is strictly larger than the corresponding value in the second. It is the primary engine for "Masking"—for example, identifying all temperature readings that exceed a safety limit—and for data filtering where you want to isolate only the positive deviations in a signal. Because it utilizes optimized processor instructions, it can compare millions of data points per second, making it far superior to standard conditional loops.
    
    How to Use:
    - Pass an array and a scalar (e.g., `greater(sensor_data, 100)`) to find all points above 100.
    - Pass two arrays of the same shape to compare two parallel datasets (e.g., `actuals` vs `predictions`) to see where the system over-shot the target.
    
    Keywords: greater than, thresholding, boolean mask, comparison engine, outlier detection, data filtering.
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
    """COMPUTES the element-wise Logical AND of two boolean arrays. [ACTION]
    
    [RAG Context]
    A sophisticated "Logic Combinator" tool for multi-criteria filtering. In complex data analysis, you often need to satisfy multiple conditions simultaneously—for example, "Find all records where Sales > 1000 AND Region == 'West'." This tool takes two boolean masks (True/False arrays) and produces a final mask that is 'True' only where BOTH inputs were 'True'. It is essential for honing in on specific subsets of data, implementing complex decision trees, and for combining independent sensor flags into a unified "Ok to Proceed" signal.
    
    How to Use:
    - First, create two masks using comparison tools like 'greater' or 'equal'.
    - Pass those masks to 'logical_and' to find the intersection of those criteria.
    - Essential for precise data querying and multi-factor authentication logic.
    
    Keywords: logical and, intersection, multi-filter, boolean combination, criteria matching, intersection logic.
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
    """COMPUTES the element-wise Logical NOT (Inversion). [ACTION]
    
    [RAG Context]
    A vital "Logic Inversion" tool for identifying gaps and negatives. 'logical_not' flips every True to False and every False to True. This is the primary method for finding "what is missing"—for example, if you have a mask of "Valid Records," applying 'logical_not' instantly gives you a mask of "Invalid Records" to investigate. It is essential for "inverse-masking" (ignoring a specific region during processing) and for implementing "unless" logic in complex automated workflows.
    
    How to Use:
    - Pass any boolean array to get its polar opposite.
    - Perfect for isolating anomalies by negating a "normal" classification mask.
    
    Keywords: boolean inversion, logical negation, bitwise flip, complement mask, negative isolation, anomaly flip.
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
    """SELECTS elements or FIND indices based on a logical condition. [ACTION]
    
    [RAG Context]
    An elite "Decision-Making Super Tool" that acts as a vectorized, high-performance 'If-Else' operator. 'where' is one of the most powerful tools in the NumPy arsenal because it can either serve as a data filter (finding indices) or a data generator (blending two datasets). When passed three arguments, it builds a new array by choosing elements from 'x' where the condition is True and 'y' where it is False. This allows for complex "branching logic" that runs at the full speed of the CPU, making it indispensable for data cleaning (e.g., "Replace all negative values with zero") and for implementing multi-state simulations where the next state depends on a current threshold.
    
    How to Use:
    - Selection: `where(value > 100, "High", "Low")` instantly labels an entire million-row dataset.
    - Discovery: `where(mask)` returns a list of indices where the mask is True—providing the "addresses" of your outliers or matches.
    - Essential for replacing outliers, building piecewise functions, and for rapid data categorization.
    
    Keywords: conditional selection, vectorized if-else, ternary operator, data discovery, index finding, data blending.
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
    """SORTS an array along a specified axis. [ACTION]
    
    [RAG Context]
    A foundational "Organization Tool" for data hygiene and statistical analysis. Sorting arranges elements in ascending order (default), which is a mandatory prerequisite for many advanced operations like calculating the Median, finding Quantiles (Percentiles), or performing efficient "Binary Search" for specific values. This tool provides a stable, high-performance implementation that can sort multi-dimensional arrays—allowing you to sort each row independently (like organizing daily sales within each month) or sort each column. In a RAG context, sorting is essential for ranking retrieved items by their relevance scores or organizing time-series data chronologically.
    
    How to Use:
    - 'axis': Define the dimension to reorganize (e.g., 0 for vertical sort, 1 for horizontal).
    - Note: This returns a sorted *copy* of the data.
    - Use this before any task that requires "Rank-based" analysis or before visualizing data in a cumulative density plot.
    
    Keywords: data ordering, ascending sort, rank organization, sequence arranging, value-based sorting, data cleanup.
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
    """COMPUTES the dot product of two arrays. [ACTION]
    
    [RAG Context]
    A versatile "Linear Algebra Super Tool" for vector projection and matrix interaction. The Dot Product is the mathematical measure of how much one vector "points" in the same direction as another. For 1D vectors, it returns a single "Scalar" value that represents the sum of the products of their corresponding elements—this is the core calculation for finding the "Average Weighted Score" of a set of features. When applied to 2D matrices, 'dot' performs standard Matrix Multiplication. This tool is the engine behind "Similarity Search," "Weighted Averaging," and "Linear Transformations" where you project data from one coordinate system to another.
    
    How to Use:
    - If both are 1D: Standard vector dot product (magnitude * magnitude * cos(theta)).
    - If 2D: Matrix multiplication (similar to 'matmul').
    - Essential for calculating the "Power" of a signal or the "Correlation" between two data series.
    
    Keywords: dot product, vector projection, scalar product, weight summation, similarity calculation, matrix interaction.
    """
    return await linalg_ops.dot(a, b)

@mcp.tool()
async def matmul(x1: NumericData, x2: NumericData) -> List[Any]: 
    """COMPUTES the matrix product of two arrays. [ACTION]
    
    [RAG Context]
    An elite "Heavyweight Super Tool" for linear transformations and deep learning. Matrix Multiplication (matmul) is the standard row-by-column operation that defines how modern AI models work. Every layer of a neural network is essentially one massive 'matmul' operation followed by an activation function. It allows for the simultaneous transformation of entire blocks of data—for example, converting 1,000 spatial coordinates from "World Space" to "Camera Space" in a single atomic step. It is the primary engine for high-dimensional data rotation, scaling, and feature extraction.
    
    How to Use:
    - Critical Rule: The number of columns in 'x1' MUST match the number of rows in 'x2'.
    - Use this for "Projecting" data into new feature spaces or for solving systems of linear equations.
    - Unlike element-wise 'multiply', 'matmul' involves the interaction of every row with every column.
    
    Keywords: matrix multiplication, linear transformation, tensor product, coordinate rotation, neural network layer, feature projection.
    """
    return await linalg_ops.matmul(x1, x2)

@mcp.tool()
async def inner(a: NumericData, b: NumericData) -> List[Any]: 
    """COMPUTES the inner product of two arrays. [ACTION]
    
    [RAG Context]
    A precise "Linear Algebra Tool" for measuring alignment and calculating weighted sums. For 1D vectors, the inner product is identical to the 'dot' product—it multiplies corresponding elements and sums the result. However, for higher-dimensional arrays, it performs a specific sum-product over the last axes of the inputs. This is a primary requirement for sophisticated signal processing algorithms (like Cross-Correlation), implementing custom kernel functions in machine learning, and for projecting multi-dimensional state vectors onto various coordinate basis. It provides a measure of "Core Similarities" between two complex structures.
    
    How to Use:
    - Pass two vectors to calculate their scalar product.
    - Essential for calculating the intensity of a specific frequency component in a signal or for determining the similarity between two multi-sensor snapshots.
    
    Keywords: inner product, scalar multiplication, projection, weighted sum, cross-correlation component, alignment measure.
    """
    return await linalg_ops.inner(a, b)

@mcp.tool()
async def outer(a: NumericData, b: NumericData) -> List[Any]: 
    """COMPUTES the outer product of two vectors into a 2D matrix. [ACTION]
    
    [RAG Context]
    A generative "Super Tool" for matrix expansion and interaction modeling. While the inner product collapses two vectors into a single number, the 'outer' product expands them into a complete 2D matrix where every element is the product of one row-item and one column-item. This is the fundamental engine for "Cross-Impact Modeling"—for example, determining how every item in a list of 'Features' interacts with every item in a list of 'Scenarios'. It is essential for building "Covariance Matrices," creating custom filter kernels for image processing, and for generating the starting state of many complex linear systems.
    
    How to Use:
    - Pass two 1D vectors of size M and N to receive a resultant matrix of shape [M, N].
    - Ideal for modeling "All-Pairs" relationships in a dataset where every entity interacts with every other entity.
    
    Keywords: outer product, matrix expansion, interaction modeling, covariance base, feature interaction, cross-impact matrix.
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
    """COMPUTES the Cholesky decomposition of a square matrix. [ACTION]
    
    [RAG Context]
    An elite "Factorization Super Tool" for advanced simulation and statistical modeling. The Cholesky decomposition factors a symmetric, positive-definite matrix into the product of a lower-triangular matrix and its transpose. This is the mathematical "Secret Sauce" behind Monte Carlo simulations with correlated variables—for example, when you want to simulate 100 stocks that tend to move together based on their historical covariance. It is significantly faster and more stable than other decompositions and is a mandatory requirement for solving efficient "Linear Least Squares" problems and for initializing Bayesian optimization routines.
    
    How to Use:
    - 'a': Must be square and positive-definite (like a covariance matrix).
    - Perfect for "Sampling from a Multivariate Normal Distribution" when you have a specific correlation goal.
    
    Keywords: cholesky decomposition, matrix factorization, triangular form, correlated simulation, monte carlo engine, least squares solver.
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
    """COMPUTES eigenvalues and eigenvectors of a square matrix. [ACTION]
    
    [RAG Context]
    A grand-master "Analytical Super Tool" for system stability and characteristic feature extraction. Eigen-decomposition reveals the "Hidden Backbone" of a linear system—the eigenvalues tell you the "scaling power" of the system, while the eigenvectors tell you the "directions" of its primary influence. In business analytics, this is the core engine for "Principal Component Analysis" (PCA), which allows the system to compress 100 different columns of data into the 3 most important "Factors" that explain most of the variation. It is also used in economics to determine the long-term equilibrium and stability of complex oscillating markets.
    
    How to Use:
    - Returns a dictionary with 'eigenvalues' (magnitudes) and 'eigenvectors' (directions).
    - Essential for dimensionality reduction, structural vibration analysis, and for identifying the most influential nodes in a graph (PageRank-style analysis).
    
    Keywords: eigen decomposition, spectral analysis, pca core, characteristic roots, feature extraction, system stability.
    """
    return await linalg_ops.eig(a)

@mcp.tool()
async def norm(x: NumericData, ord: Any = None, axis: Any = None) -> float: 
    """CALCULATES the numeric norm (magnitude) of a vector or matrix. [DATA]
    
    [RAG Context]
    A high-precision "Magnitude Tool" for assessing distance, error, and signal strength. 'norm' provides a single aggregate measure of the "size" of an array. The L2 norm (Euclidean distance) is the standard measure of the distance from the origin to a point in space—critical for k-Nearest Neighbors and cluster analysis. The L1 norm (Manhattan distance) is used in robust statistics and "Lasso Regularization" to ensure models remain simple and don't overfit. This tool is the primary way the Kea system determines when an optimization algorithm has "Converged"—meaning the 'error norm' has dropped below a specific tolerance level.
    
    How to Use:
    - 'ord': The type of norm (e.g., 2 for Euclidean, 1 for Manhattan).
    - 'axis': Define the dimension to measure (e.g., finding the magnitude of each row independently).
    - Mandatory for "Unit Normalization" (dividing a vector by its norm) to ensure all data vectors have a length of 1.0.
    
    Keywords: vector norm, euclidean magnitude, l2 distance, normalization, error magnitude, convergence metric.
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
    """CALCULATES the determinant of a square matrix. [DATA]
    
    [RAG Context]
    A critical "System Diagnostic Tool" for assessing matrix invertibility and volume scaling. The determinant is a single scalar that summarizes whether a linear transformation is "healthy" or "collapsed." If the determinant is exactly 0.0, the matrix is "Singular"—meaning it has lost data dimensions and cannot be inverted. This is a mandatory pre-flight check before trying to solve systems of equations or calculate a matrix inverse. In geometry, the determinant also represents the "scaling factor" for the area or volume of a shape after it has been processed by the matrix.
    
    How to Use:
    - Use this to verify that a matrix is "Invertible" (non-zero determinant).
    - If the determinant is negative, the transformation includes a "flip" or reflection of the data space.
    - Essential for checking the stability and validity of linear models.
    
    Keywords: matrix determinant, singularity check, volume scaling, invertibility test, linear transformation check, stability metric.
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
    """SOLVES a linear system of equations (Ax = b). [ACTION]
    
    [RAG Context]
    An elite "Inference Super Tool" for finding exact solutions to multi-variable problems. Instead of manually trying to "Invert" a matrix (which is slow and numerically unstable), 'solve' uses advanced Gaussian elimination techniques to find the precise values of 'x' that satisfy a set of linear constraints. This is the primary engine for "Equilibrium Modeling" in economics, "Load Analysis" in engineering, and "Exact Least Squares" fitting. It is the gold standard for anytime you need to find the "input" that caused a specific "output" in a linear system.
    
    How to Use:
    - 'a': The coefficient matrix (must be square).
    - 'b': The results or "Target" vector.
    - Result 'x' is the solution.
    - This tool is mathematically superior to calculating `inv(a) @ b` in terms of both speed and precision.
    
    Keywords: linear solver, system of equations, coefficient matching, exact inference, mathematical equilibrium, matrix division.
    """
    return await linalg_ops.solve(a, b)

@mcp.tool()
async def inv(a: NumericData) -> List[Any]: 
    """CALCULATES the formal multiplicative inverse of a square matrix. [ACTION]
    
    [RAG Context]
    A foundational "Reverse Engineering Tool" for undoing linear transformations. The matrix inverse (A^-1) is the mathematical equivalent of the "reciprocal" (1/x). If a matrix represents a specific transformation (like rotating an object 30 degrees), the inverse represents the exact opposite (rotating back 30 degrees). It is a core requirement for calculating "Mahalanobis Distance" in outlier detection and for various theoretical derivations in econometrics. However, for solving equations, the 'solve' tool is generally preferred for its numerical stability.
    
    How to Use:
    - 'a': Must be a square matrix with a non-zero determinant.
    - Essential for calculating the "Precision Matrix" (inverse covariance) used in sophisticated Gaussian models.
    
    Keywords: matrix inversion, reciprocal matrix, undo transformation, precision matrix, reverse engineering, matrix reciprocal.
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
    """GENERATES uniformly distributed random floating-point numbers in the range [0.0, 1.0). [ENTRY]
    
    [RAG Context]
    A fundamental "Stochastic Super Tool" for simulation, randomization, and noise injection. Generative AI and modern analytics rely heavily on the ability to produce "Pure Randomness." This tool provides a reliable stream of numbers where every value between zero and one is equally likely to occur. It is the primary engine for "Shuffle Logic," creating "Random Search" grids for hyperparameter optimization, and implementing "Dropout" in neural networks to prevent overfitting. It also serves as the baseline for choosing "yes/no" decisions based on probability (e.g., if rand_float() < 0.7, then 'Success').
    
    How to Use:
    - 'size': Determines the shape of the output (e.g., `[1000]` for a simple vector, `[10, 10]` for a noise grid).
    - Perfect for initializing "Weights" in a model or for adding small amounts of noise to a dataset to improve its robustness.
    
    Keywords: uniform random, stochastic sampler, noise generation, probability baseline, random initializing, jitter injection.
    """
    return await random_ops.rand_float(size)

@mcp.tool()
async def rand_int(low: int, high: Optional[int] = None, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random integers from a uniform discrete distribution. [ENTRY]
    
    [RAG Context]
    A versatile "Discrete Randomness Tool" for sampling and indexing. Unlike 'rand_float', this tool produces whole numbers, making it essential for simulations that involve "Countable" items—like rolling a die (1 to 6), assigning a random "User ID" to a test account, or picking a random "Category Index" from a list. It is the primary engine for "Bootstrap Sampling"—a technique in statistics where you randomly select records with replacement to estimate the uncertainty of a model. It is also used in "Random Forest" algorithms to pick random subsets of features for each tree.
    
    How to Use:
    - `low`: Min value (inclusive).
    - `high`: Max value (exclusive). If only 'low' is provided, it returns [0, low).
    - Ideal for "Sub-sampling" a large dataset by picking a random list of row indices.
    
    Keywords: random integer, discrete sampling, die roll simulation, index shuffling, bootstrap engine, random index generator.
    """
    return await random_ops.rand_int(low, high, size)

@mcp.tool()
async def rand_normal(loc: float = 0.0, scale: float = 1.0, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples from a Normal (Gaussian) distribution. [ENTRY]
    
    [RAG Context]
    An elite "Natural Variability Super Tool" for modeling the real world. Most natural phenomena—from human height to sensor noise to stock market returns—follow the "Bell Curve" (Normal Distribution). This tool allows you to simulate data that clusters around a "Mean" value with a specific "Spread." It is the cornerstone of Monte Carlo risk analysis, allowing a corporation to simulate thousands of possible futures to determine the probability of success. It is also a mandatory requirement for "Weight Initialization" in nearly all modern neural networks, ensuring that the initial brain of the AI starts with a healthy, varied signal rather than all zeros.
    
    How to Use:
    - 'loc': The center (mean) of the distribution.
    - 'scale': The "width" or standard deviation (variability).
    - Used to generate "Synthetic Realism" in testing data or to add "White Noise" to audio and signal datasets.
    
    Keywords: gaussian sampler, bell curve, normal distribution, white noise, natural variability, stochastic modeling.
    """
    return await random_ops.rand_normal(loc, scale, size)

@mcp.tool()
async def rand_uniform(low: float = 0.0, high: float = 1.0, size: Optional[List[int]] = None) -> List[Any]: 
    """GENERATES random samples from a Uniform distribution. [ENTRY]
    
    [RAG Context]
    A foundational "Stochastic Super Tool" for unbiased sampling and scenario generation. The Uniform distribution ensures that every number within the specified 'low' and 'high' range has an equal mathematical probability of being selected. This is the primary tool for "Random Search" optimizations (where you want to explore a parameter space without any prior bias), creating "Salt-and-Pepper Noise" for image robustness testing, and for implementing "A/B Testing" logic where users are assigned to groups with perfect fairness. It is the "Flat Baseline" from which many complex probability models are derived.
    
    How to Use:
    - 'low' (inclusive) and 'high' (exclusive).
    - Perfect for initializing hyper-parameters of a machine learning model when the optimal range is known but the specific best value is not.
    - Essential for simulating "Fair Systems" like lottery draws or equal-opportunity resource allocation.
    
    Keywords: uniform sampling, random search, unbiased selection, stochastic baseline, noise generation, scenario simulation.
    """
    return await random_ops.rand_uniform(low, high, size)

@mcp.tool()
async def rand_choice(a: NumericData, size: Optional[List[int]] = None, replace: bool = True, p: Optional[NumericData] = None) -> List[Any]: 
    """GENERATES a random sample from a provided 1-D array or sequence. [ENTRY]
    
    [RAG Context]
    A powerful "Categorical Sampling Super Tool" for picking items from a custom set. Unlike tools that generate numbers from a math formula, 'rand_choice' allows the system to pull real entities—like random User IDs from a database, random words from a dictionary, or random categories from a label set. Most importantly, it supports "Weighted Sampling" via the 'p' argument, allowing you to simulate real-world biases (e.g., "70% of visitors are from the US, 30% are International"). This is essential for building "Synthetic Data Generators" that must mimic the specific statistical distribution of a real-world population.
    
    How to Use:
    - 'a': The pool of items to pick from.
    - 'p': An array of probabilities (must sum to 1.0).
    - 'replace': Set to False to perform "Sampling without Replacement" (like drawing names from a hat where each name can only be picked once).
    - Perfect for choosing test subjects, simulating customer behavior, and shuffling training batches.
    
    Keywords: weighted selection, categorical sampling, bootstrap engine, random selection, pick from list, probability-based choice.
    """
    return await random_ops.rand_choice(a, size, replace, p)

@mcp.tool()
async def shuffle(x: NumericData) -> List[Any]: 
    """SHUFFLES an array's contents in-place along its first axis. [ACTION]
    
    [RAG Context]
    A mandatory "Data Randomization Tool" for training preparation and bias elimination. In machine learning, the order of your data can accidentally leak information to the model—for example, if all "Successful" cases appear at the start of the file. 'shuffle' effectively "scrambles the deck," ensuring that every time you process the dataset, the sequence is different. This forced randomness is essential for "Stochastic Gradient Descent" (SGD) to work properly and for ensuring that "Batch Normalization" sees a varied mix of examples. It is the primary way the Kea system prevents "Sequential Bias" in its reasoning and automated learning cycles.
    
    How to Use:
    - Modifies the array directly (randomizes the row order).
    - Only shuffles along the first axis (0), keeping the internal structure of each row/record intact.
    - Mandatory step before splitting data into training and validation sets.
    
    Keywords: data shuffling, random scramble, bias elimination, sgd preparation, dataset mixing, row randomization.
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
    """GENERATES random samples from a Poisson distribution. [ENTRY]
    
    [RAG Context]
    An elite "Event Modeling Super Tool" for queueing theory and arrival rate simulations. The Poisson distribution models the number of times an event occurs in a fixed interval of time or space (e.g., "How many emails will arrive between 9 AM and 10 AM?" or "How many typos are on a page?"). This tool is essential for "Wait-Time Modeling" in call centers, simulating website traffic spikes for load testing, and analyzing the "Rarity" of anomalies in a steady-state system. It allows the corporate kernel to predict resource demands and plan for bursty, unpredictable event clusters.
    
    How to Use:
    - 'lam': The average number of events (mean) per interval.
    - Ideal for modeling any process that involves independent, discrete arrivals (clicks, calls, decays).
    - Use this to build "Stress Test" scenarios for microservices based on expected request rates.
    
    Keywords: poisson modeling, event rate, arrival frequency, queueing simulation, discrete events, website traffic modeling.
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
    """COMPUTES the 1-D Discrete Fourier Transform (FFT). [ACTION]
    
    [RAG Context]
    A grand-master "Frequency Analysis Super Tool" for signal processing and pattern recognition. The FFT reveals the "Hidden Harmony" in any sequence of numbers by transforming data from the "Time Domain" to the "Frequency Domain." This allows the system to see exactly which periodic waves (like sine or cosine) were combined to create the raw signal. It is the core engine for audio processing (noise cancellation), financial analysis (finding seasonal cycles in stock prices), and data compression. By isolating specific frequencies, you can "filter out" noise or identify specific repetitive patterns that are invisible to the naked eye.
    
    How to Use:
    - Pass a 1D sequence of measurements.
    - Returns a dictionary with 'real' and 'imaginary' parts. These represent the amplitude and phase of the detected frequencies.
    - Critical for "Spectral Analysis" and converting raw sensor telemetry into actionable frequency reports.
    
    Keywords: fourier transform, frequency spectrum, signal decomposition, periodic pattern, harmonic analysis, spectral density.
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
    """PERFORMS a comprehensive, deep-dive analysis of an array. [ENTRY]
    
    [RAG Context]
    An all-in-one "Master Diagnostic Super Tool" for initial data exploration and quality auditing. 'analyze_array' is usually the first tool called when the system encounters a new, unknown dataset. It automatically calculates the complete "Statistical Profile" of the data—including the Mean, Median, Standard Deviation, and Variance—while simultaneously scanning for "Data Health" issues like NaN (missing) values, Infinite numbers, and outliers that could crash downstream models. It even generates a frequency histogram to show the "Shape" of the data, allowing the reasoning engine to immediately determine if the dataset is healthy, skewed, or in need of cleaning.
    
    How to Use:
    - Pass any newly loaded array to get an instant 360-degree report.
    - Use the 'outlier_count' and 'nan_count' from the result to trigger automated "cleaning DAGs" if they exceed threshold limits.
    - The ultimate "Auto-Profiling" tool for rapid knowledge extraction.
    
    Keywords: data profiling, automated audit, health report, statistical summary, outlier detection, distribution analysis.
    """
    return await super_ops.analyze_array(data)

@mcp.tool()
async def matrix_dashboard(data: NumericData) -> Dict[str, Any]: 
    """GENERATES a complete numerical health dashboard for 2D matrices. [ENTRY]
    
    [RAG Context]
    An elite "Linear Algebra Diagnostic Super Tool" for assessing matrix stability and suitability for inversion. Before performing complex matrix operations like 'inv' or 'solve', 'matrix_dashboard' provides a critical "readiness report." It calculates the "Condition Number" (detecting if the matrix is too unstable to trust), the "Numerical Rank" (identifying if some columns are just redundant copies of others), and the "Sparsity" (showing how many zeros are present). This allows the system to choose the fastest and most stable algorithm—deciding, for example, whether to use a "Dense" solver or a "Sparse" optimized approach.
    
    How to Use:
    - Mandatory for any high-stakes financial or engineering calculation involving matrix systems.
    - Use the 'condition_number' to detect "ill-posed" problems that would result in massive rounding errors.
    
    Keywords: matrix dashboard, stability index, rank analysis, condition check, numerical health, sparsity report.
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
    """COMPUTES the element-wise bitwise AND of two integer datasets. [ACTION]
    
    [RAG Context]
    A low-level "Instructional Super Tool" for bit-masking, privacy filtering, and hardware-level interaction. Bitwise AND works at the most fundamental binary level, comparing the 'bits' of two numbers. It is the primary engine for "Permission Masking"—for example, determining if a user has specific access flags set in their profile—and for "Bit-Packing," where multiple pieces of information are compressed into a single integer. It is essential for efficient data compression, cryptography, and for isolating status flags in complex hardware telemetry streams.
    
    How to Use:
    - Pass two integer arrays.
    - Commonly used with a "Mask" (e.g., `bitwise_and(value, 0xFF)`) to isolate only the lower 8 bits of a larger number.
    - Essential for high-performance bit-level manipulation where standard arithmetic is too slow or imprecise.
    
    Keywords: bit masking, binary intersection, bitwise logic, permission check, bit-level filter, binary intersection.
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
    """CONCATENATES strings element-wise across two arrays. [ACTION]
    
    [RAG Context]
    A vital "Text Transformation Tool" for automated report generation and metadata construction. While most NumPy tools handle numbers, 'char_add' brings vectorized performance to text. It allows the system to combine thousands of strings simultaneously—for example, merging a list of 'First Names' with a list of 'Last Names' or prepending a 'URL Prefix' to a column of file paths. This is essential for preparing clean, human-readable labels for charts, generating unique database keys, and for building structured prompts for downstream LLM cycles where specific data fields must be joined into a single coherent sentence.
    
    How to Use:
    - Pass two string arrays of the same length to join them pairwise.
    - If one argument is a single string (scalar), it will be added to every element in the array.
    - Essential for bulk formatting and data preparation tasks.
    
    Keywords: string concatenation, vectorized text join, label generation, metadata construction, bulk string merging, text formatting.
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
    """RETURNS a structured frequency breakdown of all unique elements. [DATA]
    
    [RAG Context]
    A cornerstone "Categorical Analysis Super Tool" for understanding data diversity and identifying dominant patterns. 'unique_counts' does more than just list the distinct values in a dataset; it calculates exactly how many times each value appears. This is the primary engine for creating "Bar Chart" data, identifying the "Mode" of a distribution, and performing "Category Audits" to see if certain labels are over-represented. In the Kea system, this is used to detect "Data Drifts"—changes in the frequency of specific event types over time—and for verifying the balance of training labels in machine learning workflows.
    
    How to Use:
    - Pass any array (numbers or strings).
    - Returns a dictionary with 'values' (the unique items) and 'counts' (their frequency).
    - Perfect for "Inventory Checks," "Log File Parsing," and "Voter/Sentiment Analysis."
    
    Keywords: frequency distribution, value counts, uniqueness audit, categorical breakdown, data diversity, modal analysis.
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
    """FITS a polynomial of a specific degree to the provided data (Least Squares). [ACTION]
    
    [RAG Context]
    An elite "Predictive Modeling Super Tool" for curve fitting and trend smoothing. 'poly_fit' finds the mathematical "Best Fit" line or curve that minimizes the error between your actual data points (x, y). A degree-1 fit is a standard "Linear Regression" (a straight line), while higher degrees allow the model to follow complex curves and oscillations. This is essential for "Trend Forecasting"—predicting future sales based on historical growth—and for "Noise Reduction," where a smooth curve is used to represent a jittery sensor signal. It provides the system with a summarized, mathematical "Rule" that represents the relationship between two variables.
    
    How to Use:
    - 'deg': The complexity of the curve (1 = linear, 2 = quadratic, etc.).
    - Returns the coefficients of the polynomial.
    - Essential for identifying hidden trends and generating "Best-Guess" predictions for missing data points.
    
    Keywords: polynomial regression, least squares fit, curve smoothing, trend line optimization, predictive modeling, regression engine.
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
    """COMPUTES the frequency distribution (histogram) of a numeric dataset. [DATA]
    
    [RAG Context]
    A grand-master "Visualization Super Tool" for understanding the "Topology" of data. While 'unique_counts' works for discrete labels, 'histogram' is the primary tool for analyzing "Continuous Data" like temperatures, prices, or time-intervals. it groups values into "Bins" and counts how many data points fall into each bin. This reveals the "Shape" of the data—whether it is Normal (bell-curved), Uniform (flat), or Bimodal (two peaks). In the Kea corporate system, histograms are mandatory for defining "Safety Thresholds"—identifying where 'normal' behavior ends and 'anomalous' behavior begins by looking at the density of historical records.
    
    How to Use:
    - 'bins': Either a fixed number of buckets or an auto-calculation method (like 'sturges').
    - Returns 'hist' (counts) and 'bin_edges' (the boundaries of each bucket).
    - Perfect for "Anomaly Detection" and for generating the underlying data for probability density charts.
    
    Keywords: data distribution, binning analysis, density estimation, frequency mapping, population shape, bucket analysis.
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
    """COMPUTES the cross-correlation of two 1-D sequences. [ACTION]
    
    [RAG Context]
    An elite "Pattern Matching Super Tool" for finding similarities and lags between two signals. Cross-correlation effectively slides one array over another and calculates their alignment at every possible "Offset." This is the primary engine for "Time-Delay Estimation"—for example, determining the exact delay between a command being sent and a sensor reacting. It is also a fundamental tool for "Signal Search," where you look for a "Known Pattern" (like a specific keyword or heart rhythm) within a long, noisy stream of data. If the correlation peaks at a specific offset, you have found a match.
    
    How to Use:
    - Pass two sequences to find where they align most strongly.
    - 'mode': Determines the size of the output ('full', 'same', or 'valid').
    - Essential for synchronization, echo cancellation, and identifying leading/lagging indicators in economic time-series.
    
    Keywords: cross-correlation, pattern matching, time-delay estimation, signal synchronization, lag detection, signal search.
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

