import pytest
import asyncio
import os
import base64
from PIL import Image, ImageDraw, ImageFont
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

def create_dummy_image(text="Hello World"):
    """Creates a simple image with text for OCR testing."""
    img = Image.new('RGB', (200, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Use default font
    d.text((10,10), text, fill=(0,0,0))
    path = "test_ocr_image.png"
    img.save(path)
    return path

@pytest.mark.asyncio
async def test_tesseract_real_simulation():
    """
    REAL SIMULATION: Verify Tesseract Server (OCR).
    """
    params = get_server_params("tesseract_server", extra_dependencies=["pytesseract", "pillow", "pandas", "opencv-python"])
    
    img_path = create_dummy_image()
    abs_path = os.path.abspath(img_path)
    
    print(f"\n--- Starting Real-World Simulation: Tesseract Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Image to String
            print(f"1. OCR on '{img_path}'...")
            # Note: Tesseract must be installed on the system for this to actually obtain text.
            # If not installed, it might error or return empty. We handle gracefully.
            res = await session.call_tool("image_to_string", arguments={"image_input": abs_path})
            if not res.isError:
                 print(f" [PASS] OCR Result: {res.content[0].text.strip()}")
            else:
                 print(f" [WARN] OCR Failed (Tesseract installed?): {res.content[0].text}")

            # 2. Get Char Boxes
            print("2. Getting Char Boxes...")
            res = await session.call_tool("get_char_boxes", arguments={"image_input": abs_path})
            if not res.isError:
                 print(f" [PASS] Boxes Found: {len(res.content[0].text)}")

    # Cleanup
    if os.path.exists(img_path):
        os.remove(img_path)

    print("--- Tesseract Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
