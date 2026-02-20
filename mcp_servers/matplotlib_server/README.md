# 🔌 Matplotlib Server

The `matplotlib_server` is an MCP server providing tools for **Matplotlib Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `plot_line` | Execute plot line operation | `x: VectorInput, y: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', linestyle: str = '-', marker: Optional[str] = None, label: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_scatter` | Execute plot scatter operation | `x: VectorInput, y: VectorInput, s: Optional[VectorInput] = None, c: Optional[VectorInput] = None, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, alpha: float = 1.0, figsize: List[int] = [10, 6]` |
| `plot_bar` | Execute plot bar operation | `x: VectorInput, height: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]` |
| `plot_pie` | Execute plot pie operation | `x: VectorInput, labels: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [8, 8]` |
| `plot_area` | Execute plot area operation | `x: VectorInput, y: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_step` | Execute plot step operation | `x: VectorInput, y: VectorInput, where: str = 'pre', title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_hist` | Execute plot hist operation | `x: VectorInput, bins: int = 10, title: Optional[str] = None, xlabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]` |
| `plot_boxplot` | Execute plot boxplot operation | `data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_violin` | Execute plot violin operation | `data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_errorbar` | Execute plot errorbar operation | `x: VectorInput, y: VectorInput, yerr: VectorInput, title: Optional[str] = None, fmt: str = '-o', figsize: List[int] = [10, 6]` |
| `plot_hexbin` | Execute plot hexbin operation | `x: VectorInput, y: VectorInput, gridsize: int = 50, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_contour` | Execute plot contour operation | `X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_contourf` | Execute plot contourf operation | `X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_heatmap` | Execute plot heatmap operation | `data: DataInput, title: Optional[str] = None, cmap: str = 'viridis', figsize: List[int] = [10, 8]` |
| `plot_stream` | Execute plot stream operation | `X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_quiver` | Execute plot quiver operation | `X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_scatter3d` | Execute plot scatter3d operation | `x: VectorInput, y: VectorInput, z: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_surface` | Execute plot surface operation | `X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_wireframe` | Execute plot wireframe operation | `X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]` |
| `plot_polar` | Execute plot polar operation | `theta: VectorInput, r: VectorInput, title: Optional[str] = None, figsize: List[int] = [8, 8]` |
| `plot_stem` | Execute plot stem operation | `x: VectorInput, y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_stair` | Execute plot stair operation | `y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `create_mosaic` | Execute create mosaic operation | `layout: str, plots: Dict[str, Dict[str, Any]], figsize: List[int] = [12, 8], title: Optional[str] = None` |
| `create_animation` | Execute create animation operation | `frames_data: List[DataInput], plot_type: str = 'line', x: Optional[DataInput] = None, title: Optional[str] = None, interval: int = 200, figsize: List[int] = [10, 6]` |
| `draw_shapes` | Execute draw shapes operation | `shapes: List[Dict[str, Any]], title: Optional[str] = None, x_lim: List[float] = [0, 10], y_lim: List[float] = [0, 10], figsize: List[int] = [10, 8]` |
| `plot_sankey` | Execute plot sankey operation | `flows: VectorInput, labels: Optional[VectorInput] = None, orientations: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_table` | Execute plot table operation | `data: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `plot_broken_barh` | Execute plot broken barh operation | `xranges: List[tuple], yrange: tuple, facecolors: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]` |
| `create_dashboard` | Execute create dashboard operation | `plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]` |
| `set_style` | Execute set style operation | `style: str` |
| `get_styles` | Execute get styles operation | `` |

## 📦 Dependencies

The following packages are required:
- `matplotlib`
- `pandas`
- `numpy`
- `seaborn`
- `scipy`
- `pillow`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.matplotlib_server.server
```
