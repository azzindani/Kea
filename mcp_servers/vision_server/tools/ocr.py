
import os
import httpx
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger

logger = get_logger(__name__)

async def _call_vision_llm(
    prompt: str,
    image_url: str | None = None,
    image_b64: str | None = None,
) -> str:
    """Call vision LLM via OpenRouter."""
    
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return "Error: OPENROUTER_API_KEY not set"
    
    # Build image content
    if image_url:
        image_content = {"type": "image_url", "image_url": {"url": image_url}}
    elif image_b64:
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
        }
    else:
        return "Error: No image source provided"
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-2.0-flash-exp:free",  # Vision-capable free model
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
    except Exception as e:
        logger.error(f"Vision API error: {e}")
        return f"Error calling Vision API: {str(e)}"

async def screenshot_extract(
    image_url: str = None, 
    image_base64: str = None, 
    extraction_type: str = "all"
) -> ToolResult:
    """Extract text, tables, and structured data from a screenshot or image."""
    
    if not image_url and not image_base64:
        return ToolResult(
            content=[TextContent(text="Error: Either image_url or image_base64 is required")],
            isError=True
        )
    
    prompt = f"""Analyze this image and extract {extraction_type} content.

If extracting tables, format as markdown tables.
If extracting text, preserve structure.
If extracting structured data, output as JSON.

Be precise and thorough."""

    result = await _call_vision_llm(prompt, image_url, image_base64)
    
    return ToolResult(content=[TextContent(text=result)])

async def chart_reader(
    image_url: str = None, 
    image_base64: str = None, 
    chart_type: str = "unknown"
) -> ToolResult:
    """Interpret charts and graphs, extract data points and trends."""
    
    if not image_url and not image_base64:
        return ToolResult(
            content=[TextContent(text="Error: Either image_url or image_base64 is required")],
            isError=True
        )
    
    prompt = f"""Analyze this {chart_type} chart/graph.

Extract:
1. Chart title and axis labels
2. All data points with values
3. Trends and patterns
4. Key insights

Format data as a markdown table where applicable.
Be precise with numbers."""

    result = await _call_vision_llm(prompt, image_url, image_base64)
    
    return ToolResult(content=[TextContent(text=result)])
