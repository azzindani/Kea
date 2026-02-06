# 🔌 Seaborn Server

The `seaborn_server` is an MCP server providing tools for **Seaborn Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `relplot` | Execute relplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, kind: str = 'scatter', height: float = 5, aspect: float = 1` |
| `scatterplot` | Execute scatterplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None` |
| `lineplot` | Execute lineplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None` |
| `displot` | Execute displot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'hist', height: float = 5, aspect: float = 1` |
| `histplot` | Execute histplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, bins: Union[int, str] = 'auto', kde: bool = False, title: Optional[str] = None` |
| `kdeplot` | Execute kdeplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, fill: bool = False, title: Optional[str] = None` |
| `ecdfplot` | Execute ecdfplot operation | `data: DataInput, x: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None` |
| `rugplot` | Execute rugplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, height: float = 0.05` |
| `catplot` | Execute catplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'strip', height: float = 5, aspect: float = 1` |
| `boxplot` | Execute boxplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None` |
| `violinplot` | Execute violinplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, split: bool = False, title: Optional[str] = None` |
| `barplot` | Execute barplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None` |
| `countplot` | Execute countplot operation | `data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None` |
| `lmplot` | Execute lmplot operation | `data: DataInput, x: str, y: str, hue: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, height: float = 5, aspect: float = 1` |
| `regplot` | Execute regplot operation | `data: DataInput, x: str, y: str, title: Optional[str] = None` |
| `residplot` | Execute residplot operation | `data: DataInput, x: str, y: str, title: Optional[str] = None` |
| `heatmap` | Execute heatmap operation | `data: DataInput, annot: bool = False, cmap: str = 'viridis', title: Optional[str] = None` |
| `clustermap` | Execute clustermap operation | `data: DataInput, cmap: str = 'viridis', standard_scale: Optional[int] = None` |
| `pairplot` | Execute pairplot operation | `data: DataInput, hue: Optional[str] = None, kind: str = 'scatter', diag_kind: str = 'auto'` |
| `jointplot` | Execute jointplot operation | `data: DataInput, x: str, y: str, kind: str = 'scatter', hue: Optional[str] = None` |
| `set_theme` | Execute set theme operation | `style: str = "darkgrid", palette: str = "deep", font_scale: float = 1.0` |
| `get_palette` | Execute get palette operation | `palette: str = "deep", n_colors: int = 10, as_hex: bool = True` |
| `auto_plot` | Execute auto plot operation | `data: DataInput, x: str, y: Optional[str] = None` |
| `create_dashboard` | Execute create dashboard operation | `data: DataInput, plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]` |

## 📦 Dependencies

The following packages are required:
- `seaborn`
- `matplotlib`
- `pandas`
- `numpy`
- `scipy`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.seaborn_server.server
```
