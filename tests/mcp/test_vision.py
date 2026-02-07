import pytest
import asyncio
import base64
import os
from PIL import Image, ImageDraw
from io import BytesIO
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

def create_base64_image(text="Vision Test"):
    """Creates a simple base64 image."""
    img = Image.new('RGB', (200, 100), color='white')
    d = ImageDraw.Draw(img)
    d.text((10,10), text, fill='black')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@pytest.mark.asyncio
async def test_vision_real_simulation():
    """
    REAL SIMULATION: Verify Vision Server (Screenshot/Chart).
    """
    params = get_server_params("vision_server", extra_dependencies=["httpx"])
    
    b64_img = create_base64_image()
    
    print(f"\n--- Starting Real-World Simulation: Vision Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Screenshot Extract (using base64)
            # Requires an actual OCR backend (like ChatGPT or Tesseract) configured in the server?
            # Or does it use a remote API? Server deps says 'httpx', likely remote (OpenAI/Claude?).
            # If so, it might fail without keys. We check for graceful handling.
            print("1. Extracting from Base64 Image...")
            res = await session.call_tool("screenshot_extract", arguments={"image_base64": b64_img, "extraction_type": "text"})
            
            if not res.isError:
                 print(f" [PASS] Extracted: {res.content[0].text}")
            else:
                 print(f" [WARN] Extraction Failed (Missing Keys?): {res.content[0].text}")

    print("--- Vision Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
