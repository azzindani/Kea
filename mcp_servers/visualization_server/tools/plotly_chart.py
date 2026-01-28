import pandas as pd
import plotly.express as px
import plotly.io as pio

async def plotly_chart(data_url: str, chart_type: str, x_column: str = None, y_column: str = None, color_column: str = None, title: str = None) -> str:
    """Create interactive Plotly chart."""
    try:
        if not title:
            title = f"{chart_type.title()} Chart"
        
        df = pd.read_csv(data_url)
        
        # Create chart based on type
        if chart_type == "line":
            fig = px.line(df, x=x_column, y=y_column, color=color_column, title=title)
        elif chart_type == "bar":
            fig = px.bar(df, x=x_column, y=y_column, color=color_column, title=title)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x_column, y=y_column, color=color_column, title=title)
        elif chart_type == "histogram":
            fig = px.histogram(df, x=x_column or y_column, color=color_column, title=title)
        elif chart_type == "box":
            fig = px.box(df, x=x_column, y=y_column, color=color_column, title=title)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_column, values=y_column, title=title)
        elif chart_type == "heatmap":
            numeric_df = df.select_dtypes(include=['number'])
            fig = px.imshow(numeric_df.corr(), title=title)
        else:
            return f"Error: Unknown chart type: {chart_type}"
        
        # Generate HTML
        html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False)
        
        result = f"# 📊 {title}\n\n"
        result += f"**Chart Type**: {chart_type}\n"
        result += f"**Data Shape**: {df.shape}\n\n"
        result += "## Interactive Chart\n\n"
        result += f"```html\n{html[:500]}...\n```\n\n"
        result += "(Full HTML available for rendering)\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
