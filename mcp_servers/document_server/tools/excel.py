
import httpx
import pandas as pd
import io
import json
from shared.logging.structured import get_logger

logger = get_logger(__name__)

async def parse_excel(url: str, sheet_name: str = None, preview_rows: int = 10) -> str:
    """Parse Excel file."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            response.raise_for_status()
            xlsx_bytes = response.content
        
        excel_file = pd.ExcelFile(io.BytesIO(xlsx_bytes))
        
        output_data = {
            "source": url,
            "sheets_available": excel_file.sheet_names,
            "sheets_parsed": []
        }
        
        sheets_to_parse = excel_file.sheet_names if sheet_name == "all" or not sheet_name else [sheet_name]
        
        for sheet in sheets_to_parse:
            if sheet in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet)
                
                # Convert first N rows to dict
                preview_data = df.head(preview_rows).to_dict(orient='records')
                
                sheet_data = {
                    "name": sheet,
                    "rows_total": len(df),
                    "columns": list(df.columns),
                    "preview": preview_data
                }
                output_data["sheets_parsed"].append(sheet_data)
        
        return json.dumps(output_data, indent=2, default=str)
    except Exception as e:
        logger.error(f"Excel Parser error: {e}")
        return f"Error: {str(e)}"
