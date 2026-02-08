# 🔌 Plotly Server

The `plotly_server` is an MCP server providing tools for **Plotly Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `plot_scatter` | Execute plot scatter operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_line` | Execute plot line operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png'` |
| `plot_bar` | Execute plot bar operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, barmode: str = 'relative', title: Optional[str] = None, format: str = 'png'` |
| `plot_pie` | Execute plot pie operation | `data: DataInput, names: str, values: str, hole: float = 0.0, title: Optional[str] = None, format: str = 'png'` |
| `plot_histogram` | Execute plot histogram operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, nbins: Optional[int] = None, marginal: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_box` | Execute plot box operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, points: str = 'outliers', title: Optional[str] = None, format: str = 'png'` |
| `plot_violin` | Execute plot violin operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, box: bool = False, points: str = 'outliers', title: Optional[str] = None, format: str = 'png'` |
| `plot_strip` | Execute plot strip operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, stripmode: str = 'group', title: Optional[str] = None, format: str = 'png'` |
| `plot_ecdf` | Execute plot ecdf operation | `data: DataInput, x: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png'` |
| `plot_candlestick` | Execute plot candlestick operation | `data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png'` |
| `plot_ohlc` | Execute plot ohlc operation | `data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png'` |
| `plot_waterfall` | Execute plot waterfall operation | `data: DataInput, x: str, y: str, measure: Optional[str] = None, text: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_funnel` | Execute plot funnel operation | `data: DataInput, x: str, y: str, title: Optional[str] = None, format: str = 'png'` |
| `plot_indicator` | Execute plot indicator operation | `value: float, delta_ref: Optional[float] = None, title: Optional[str] = None, mode: str = "number+delta", format: str = 'png'` |
| `plot_scatter_map` | Execute plot scatter map operation | `data: DataInput, lat: str, lon: str, color: Optional[str] = None, size: Optional[str] = None, hover_name: Optional[str] = None, zoom: int = 3, title: Optional[str] = None, format: str = 'png'` |
| `plot_choropleth` | Execute plot choropleth operation | `data: DataInput, locations: str, color: str, locationmode: str = 'ISO-3', hover_name: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_density_map` | Execute plot density map operation | `data: DataInput, lat: str, lon: str, z: Optional[str] = None, radius: int = 10, title: Optional[str] = None, format: str = 'png'` |
| `plot_sunburst` | Execute plot sunburst operation | `data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_treemap` | Execute plot treemap operation | `data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_icicle` | Execute plot icicle operation | `data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_scatter3d` | Execute plot scatter3d operation | `data: DataInput, x: str, y: str, z: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_surface` | Execute plot surface operation | `z: List[List[float]], x: Optional[List[Any]] = None, y: Optional[List[Any]] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_mesh3d` | Execute plot mesh3d operation | `data: DataInput, x: str, y: str, z: str, alphahull: int = 0, title: Optional[str] = None, format: str = 'png'` |
| `plot_animated_scatter` | Execute plot animated scatter operation | `data: DataInput, x: str, y: str, animation_frame: str, animation_group: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, range_x: Optional[List[float]] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_animated_bar` | Execute plot animated bar operation | `data: DataInput, x: str, y: str, animation_frame: str, color: Optional[str] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_animated_choropleth` | Execute plot animated choropleth operation | `data: DataInput, locations: str, color: str, animation_frame: str, locationmode: str = 'ISO-3', title: Optional[str] = None, format: str = 'png'` |
| `plot_parallel_coordinates` | Execute plot parallel coordinates operation | `data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_parallel_categories` | Execute plot parallel categories operation | `data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_sankey` | Execute plot sankey operation | `labels: List[str], source: List[int], target: List[int], value: List[float], title: Optional[str] = None, format: str = 'png'` |
| `plot_table` | Execute plot table operation | `header: List[str], cells: List[List[Any]], title: Optional[str] = None, format: str = 'png'` |
| `plot_scatter_polar` | Execute plot scatter polar operation | `data: DataInput, r: str, theta: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `plot_line_polar` | Execute plot line polar operation | `data: DataInput, r: str, theta: str, color: Optional[str] = None, line_close: bool = True, title: Optional[str] = None, format: str = 'png'` |
| `plot_bar_polar` | Execute plot bar polar operation | `data: DataInput, r: str, theta: str, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png'` |
| `auto_plot` | Execute auto plot operation | `data: DataInput, x: str, y: Optional[str] = None, color: Optional[str] = None, format: str = 'png'` |
| `create_dashboard` | Execute create dashboard operation | `plots: List[Dict[str, Any]], layout: List[int] = [2, 2], width: int = 1200, height: int = 800, format: str = 'png'` |

## 📦 Dependencies

The following packages are required:
- `plotly`
- `kaleido`
- `pandas`
- `numpy`
- `scipy`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.plotly_server.server
```
