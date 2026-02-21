"""
Table OCR Tool.

Extract tables from images using vision LLM.
"""

from __future__ import annotations

import os

import httpx

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger


logger = get_logger(__name__)


async def table_ocr_tool(arguments: dict) -> ToolResult:
    """
    Extract tables from images.
    
    Args:
        arguments: Tool arguments containing:
            - image_url: URL of the image
            - image_base64: Base64 encoded image
            - output_format: csv, markdown, json (default: markdown)
    
    Returns:
        ToolResult with extracted table data
    """
    image_url = arguments.get("image_url")
    image_b64 = arguments.get("image_base64")
    output_format = arguments.get("output_format", "markdown")
    
    if not image_url and not image_b64:
        return ToolResult(
            content=[TextContent(text="Error: Either image_url or image_base64 is required")],
            isError=True
        )
    
    try:
        result = await _extract_table_with_vision(
            image_url=image_url,
            image_b64=image_b64,
            output_format=output_format,
        )
        return ToolResult(content=[TextContent(text=result)])
    except Exception as e:
        logger.error(f"Table OCR error: {e}")
        return ToolResult(
            content=[TextContent(text=f"Error: {str(e)}")],
            isError=True
        )


async def _extract_table_with_vision(
    image_url: str | None,
    image_b64: str | None,
    output_format: str,
) -> str:
    """Use vision LLM to extract tables."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    
    # Build image content
    if image_url:
        image_content = {"type": "image_url", "image_url": {"url": image_url}}
    else:
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
        }
    
    format_instructions = {
        "markdown": "Format the table as a markdown table with | separators and --- header row.",
        "csv": "Format the table as CSV with comma separators. First row should be headers.",
        "json": "Format the table as a JSON array of objects where each object is a row with column names as keys.",
    }
    
    prompt = f"""Extract ALL tables from this image.

Instructions:
1. Identify every table in the image
2. Extract all headers and cell values precisely
3. Preserve numbers exactly as shown
4. {format_instructions.get(output_format, format_instructions['markdown'])}

If there are multiple tables, separate them with a blank line and label each (Table 1, Table 2, etc.)

Be extremely precise with numbers and text. Do not summarize or omit any data."""
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            image_content,
                        ]
                    }
                ],
                "max_tokens": 4096,
            }
        )
        response.raise_for_status()
        data = response.json()
    
    return data["choices"][0]["message"]["content"]
