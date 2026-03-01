# 🔌 Numpy Server

The `numpy_server` is an MCP server providing tools for **Numpy Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `create_array` | Execute create array operation | `data: NumericData` |
| `create_zeros` | Execute create zeros operation | `shape: List[int]` |
| `create_ones` | Execute create ones operation | `shape: List[int]` |
| `create_full` | Execute create full operation | `shape: List[int], fill_value: Union[float, int]` |
| `arange` | Execute arange operation | `start: float, stop: float = None, step: float = 1` |
| `linspace` | Execute linspace operation | `start: float, stop: float, num: int = 50` |
| `logspace` | Execute logspace operation | `start: float, stop: float, num: int = 50, base: float = 10.0` |
| `geomspace` | Execute geomspace operation | `start: float, stop: float, num: int = 50` |
| `eye` | Execute eye operation | `N: int, M: Optional[int] = None, k: int = 0` |
| `identity` | Execute identity operation | `n: int` |
| `diag` | Execute diag operation | `v: NumericData, k: int = 0` |
| `vander` | Execute vander operation | `x: List[float], N: Optional[int] = None` |
| `reshape` | Execute reshape operation | `a: NumericData, newshape: List[int]` |
| `flatten` | Execute flatten operation | `a: NumericData` |
| `transpose` | Execute transpose operation | `a: NumericData, axes: Optional[List[int]] = None` |
| `flip` | Execute flip operation | `m: NumericData, axis: Optional[Union[int, List[int]]] = None` |
| `roll` | Execute roll operation | `a: NumericData, shift: Union[int, List[int]], axis: Optional[Union[int, List[int]]] = None` |
| `concatenate` | Execute concatenate operation | `arrays: List[NumericData], axis: int = 0` |
| `stack` | Execute stack operation | `arrays: List[NumericData], axis: int = 0` |
| `vstack` | Execute vstack operation | `tup: List[NumericData]` |
| `hstack` | Execute hstack operation | `tup: List[NumericData]` |
| `split` | Execute split operation | `ary: NumericData, indices_or_sections: Union[int, List[int]], axis: int = 0` |
| `tile` | Execute tile operation | `A: NumericData, reps: List[int]` |
| `repeat` | Execute repeat operation | `a: NumericData, repeats: Union[int, List[int]], axis: Optional[int] = None` |
| `unique` | Execute unique operation | `ar: NumericData` |
| `trim_zeros` | Execute trim zeros operation | `filt: NumericData, trim: str = 'fb'` |
| `pad` | Execute pad operation | `array: NumericData, pad_width: List[Any], mode: str = 'constant', constant_values: Any = 0` |
| `add` | Execute add operation | `x1: NumericData, x2: NumericData` |
| `subtract` | Execute subtract operation | `x1: NumericData, x2: NumericData` |
| `multiply` | Execute multiply operation | `x1: NumericData, x2: NumericData` |
| `divide` | Execute divide operation | `x1: NumericData, x2: NumericData` |
| `power` | Execute power operation | `x1: NumericData, x2: NumericData` |
| `mod` | Execute mod operation | `x1: NumericData, x2: NumericData` |
| `abs_val` | Execute abs val operation | `x: NumericData` |
| `sign` | Execute sign operation | `x: NumericData` |
| `exp` | Execute exp operation | `x: NumericData` |
| `log` | Execute log operation | `x: NumericData` |
| `log10` | Execute log10 operation | `x: NumericData` |
| `sqrt` | Execute sqrt operation | `x: NumericData` |
| `sin` | Execute sin operation | `x: NumericData` |
| `cos` | Execute cos operation | `x: NumericData` |
| `tan` | Execute tan operation | `x: NumericData` |
| `rad2deg` | Execute rad2deg operation | `x: NumericData` |
| `deg2rad` | Execute deg2rad operation | `x: NumericData` |
| `clip` | Execute clip operation | `a: NumericData, a_min: float, a_max: float` |
| `round_val` | Execute round val operation | `a: NumericData, decimals: int = 0` |
| `sum_val` | Execute sum val operation | `a: NumericData, axis: Optional[int] = None` |
| `prod` | Execute prod operation | `a: NumericData, axis: Optional[int] = None` |
| `cumsum` | Execute cumsum operation | `a: NumericData, axis: Optional[int] = None` |
| `cumprod` | Execute cumprod operation | `a: NumericData, axis: Optional[int] = None` |
| `diff` | Execute diff operation | `a: NumericData, n: int = 1, axis: int = -1` |
| `gradient` | Execute gradient operation | `f: NumericData` |
| `cross` | Execute cross operation | `a: NumericData, b: NumericData` |
| `greater` | Execute greater operation | `x1: NumericData, x2: NumericData` |
| `less` | Execute less operation | `x1: NumericData, x2: NumericData` |
| `equal` | Execute equal operation | `x1: NumericData, x2: NumericData` |
| `not_equal` | Execute not equal operation | `x1: NumericData, x2: NumericData` |
| `logical_and` | Execute logical and operation | `x1: NumericData, x2: NumericData` |
| `logical_or` | Execute logical or operation | `x1: NumericData, x2: NumericData` |
| `logical_not` | Execute logical not operation | `x: NumericData` |
| `all_true` | Execute all true operation | `a: NumericData, axis: Optional[int] = None` |
| `any_true` | Execute any true operation | `a: NumericData, axis: Optional[int] = None` |
| `where` | Execute where operation | `condition: NumericData, x: Optional[NumericData] = None, y: Optional[NumericData] = None` |
| `argmax` | Execute argmax operation | `a: NumericData, axis: Optional[int] = None` |
| `argmin` | Execute argmin operation | `a: NumericData, axis: Optional[int] = None` |
| `argsort` | Execute argsort operation | `a: NumericData, axis: int = -1` |
| `sort` | Execute sort operation | `a: NumericData, axis: int = -1` |
| `searchsorted` | Execute searchsorted operation | `a: NumericData, v: NumericData, side: str = 'left'` |
| `dot` | Execute dot operation | `a: NumericData, b: NumericData` |
| `matmul` | Execute matmul operation | `x1: NumericData, x2: NumericData` |
| `inner` | Execute inner operation | `a: NumericData, b: NumericData` |
| `outer` | Execute outer operation | `a: NumericData, b: NumericData` |
| `kron` | Execute kron operation | `a: NumericData, b: NumericData` |
| `matrix_power` | Execute matrix power operation | `a: NumericData, n: int` |
| `cholesky` | Execute cholesky operation | `a: NumericData` |
| `qr_decomp` | Execute qr decomp operation | `a: NumericData, mode: str = 'reduced'` |
| `svd_decomp` | Execute svd decomp operation | `a: NumericData, full_matrices: bool = True` |
| `eig` | Execute eig operation | `a: NumericData` |
| `norm` | Execute norm operation | `x: NumericData, ord: Any = None, axis: Any = None` |
| `cond` | Execute cond operation | `x: NumericData, p: Any = None` |
| `det` | Execute det operation | `a: NumericData` |
| `matrix_rank` | Execute matrix rank operation | `M: NumericData` |
| `solve` | Execute solve operation | `a: NumericData, b: NumericData` |
| `inv` | Execute inv operation | `a: NumericData` |
| `pinv` | Execute pinv operation | `a: NumericData` |
| `lstsq` | Execute lstsq operation | `a: NumericData, b: NumericData, rcond: str = 'warn'` |
| `rand_float` | Execute rand float operation | `size: Optional[List[int]] = None` |
| `rand_int` | Execute rand int operation | `low: int, high: Optional[int] = None, size: Optional[List[int]] = None` |
| `rand_normal` | Execute rand normal operation | `loc: float = 0.0, scale: float = 1.0, size: Optional[List[int]] = None` |
| `rand_uniform` | Execute rand uniform operation | `low: float = 0.0, high: float = 1.0, size: Optional[List[int]] = None` |
| `rand_choice` | Execute rand choice operation | `a: NumericData, size: Optional[List[int]] = None, replace: bool = True, p: Optional[NumericData] = None` |
| `shuffle` | Execute shuffle operation | `x: NumericData` |
| `permutation` | Execute permutation operation | `x: Union[int, NumericData]` |
| `rand_beta` | Execute rand beta operation | `a: float, b: float, size: Optional[List[int]] = None` |
| `rand_binomial` | Execute rand binomial operation | `n: int, p: float, size: Optional[List[int]] = None` |
| `rand_chisquare` | Execute rand chisquare operation | `df: float, size: Optional[List[int]] = None` |
| `rand_gamma` | Execute rand gamma operation | `shape: float, scale: float = 1.0, size: Optional[List[int]] = None` |
| `rand_poisson` | Execute rand poisson operation | `lam: float = 1.0, size: Optional[List[int]] = None` |
| `rand_exponential` | Execute rand exponential operation | `scale: float = 1.0, size: Optional[List[int]] = None` |
| `fft` | Execute fft operation | `a: NumericData, n: Optional[int] = None, axis: int = -1` |
| `ifft` | Execute ifft operation | `a_real: NumericData, a_imag: Optional[NumericData] = None, n: Optional[int] = None, axis: int = -1` |
| `fft2` | Execute fft2 operation | `a: NumericData, s: Optional[List[int]] = None` |
| `fftfreq` | Execute fftfreq operation | `n: int, d: float = 1.0` |
| `analyze_array` | Execute analyze array operation | `data: NumericData` |
| `matrix_dashboard` | Execute matrix dashboard operation | `data: NumericData` |
| `compare_arrays` | Execute compare arrays operation | `a: NumericData, b: NumericData` |
| `bitwise_and` | Execute bitwise and operation | `x1: NumericData, x2: NumericData` |
| `bitwise_or` | Execute bitwise or operation | `x1: NumericData, x2: NumericData` |
| `bitwise_xor` | Execute bitwise xor operation | `x1: NumericData, x2: NumericData` |
| `bitwise_not` | Execute bitwise not operation | `x: NumericData` |
| `left_shift` | Execute left shift operation | `x1: NumericData, x2: NumericData` |
| `right_shift` | Execute right shift operation | `x1: NumericData, x2: NumericData` |
| `binary_repr` | Execute binary repr operation | `num: int, width: Optional[int] = None` |
| `char_add` | Execute char add operation | `x1: Union[List[str], str], x2: Union[List[str], str]` |
| `char_multiply` | Execute char multiply operation | `a: Union[List[str], str], i: int` |
| `char_upper` | Execute char upper operation | `a: Union[List[str], str]` |
| `char_lower` | Execute char lower operation | `a: Union[List[str], str]` |
| `char_replace` | Execute char replace operation | `a: Union[List[str], str], old: str, new: str, count: Optional[int] = None` |
| `char_compare_equal` | Execute char compare equal operation | `x1: Union[List[str], str], x2: Union[List[str], str]` |
| `char_count` | Execute char count operation | `a: Union[List[str], str], sub: str, start: int = 0, end: Optional[int] = None` |
| `char_find` | Execute char find operation | `a: Union[List[str], str], sub: str, start: int = 0, end: Optional[int] = None` |
| `unique_counts` | Execute unique counts operation | `ar: NumericData` |
| `union1d` | Execute union1d operation | `ar1: NumericData, ar2: NumericData` |
| `intersect1d` | Execute intersect1d operation | `ar1: NumericData, ar2: NumericData` |
| `setdiff1d` | Execute setdiff1d operation | `ar1: NumericData, ar2: NumericData` |
| `setxor1d` | Execute setxor1d operation | `ar1: NumericData, ar2: NumericData` |
| `isin` | Execute isin operation | `element: NumericData, test_elements: NumericData` |
| `poly_fit` | Execute poly fit operation | `x: NumericData, y: NumericData, deg: int` |
| `poly_val` | Execute poly val operation | `coef: List[float], x: NumericData` |
| `poly_roots` | Execute poly roots operation | `coef: List[float]` |
| `poly_from_roots` | Execute poly from roots operation | `roots: List[float]` |
| `poly_derivative` | Execute poly derivative operation | `coef: List[float], m: int = 1` |
| `poly_integrate` | Execute poly integrate operation | `coef: List[float], m: int = 1` |
| `histogram` | Execute histogram operation | `a: NumericData, bins: Union[int, str] = 10, range: Optional[List[float]] = None` |
| `bincount` | Execute bincount operation | `x: NumericData, minlength: int = 0` |
| `digitize` | Execute digitize operation | `x: NumericData, bins: List[float], right: bool = False` |
| `correlate` | Execute correlate operation | `a: NumericData, v: NumericData, mode: str = 'valid'` |
| `convolve` | Execute convolve operation | `a: NumericData, v: NumericData, mode: str = 'full'` |
| `cov` | Execute cov operation | `m: NumericData` |

## 📦 Dependencies

The following packages are required:
- `numpy`
- `pandas`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.numpy_server.server
```
