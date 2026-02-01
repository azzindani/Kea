from __future__ import annotations
import asyncio
from shared.logging import get_logger
import json
import os
import uuid
import base64
from datetime import datetime
from typing import Any, Optional
from shared.schemas import ToolOutput, DataPayload, FileReference, FileType


logger = get_logger(__name__)

async def browser_scrape_tool(url: str, wait_for: Optional[str] = None, extract_tables: bool = True, screenshot: bool = False, max_tables: int = 50, max_rows: int = 1000) -> str:
    """Scrape URL using headless browser with JavaScript execution."""
    if not url: return "Error: URL is required"
    
    try:
        from playwright.async_api import async_playwright
        from fake_useragent import UserAgent
    except ImportError:
        return "Error: Playwright or fake-useragent not installed. Run: pip install playwright fake-useragent"
    
    try:
        ua = UserAgent()
        user_agent = ua.random
        
        async with async_playwright() as p:
            # ... (launch logic remains same)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-infobars",
                ]
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent,
                locale="en-US",
                timezone_id="Asia/Jakarta"
            )
            
            page = await context.new_page()
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            status_code = response.status if response else 0
            
            if status_code in [403, 401]:
                await browser.close()
                return ToolOutput(text=f"Error: Access Denied (HTTP {status_code}). Site blocked the scraper.", success=False).model_dump_json()
            
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=10000)
                except Exception:
                    pass
            
            await asyncio.sleep(3)
            
            text_content = await page.evaluate("() => document.body.innerText")
            
            if not text_content or len(text_content.strip()) < 50:
                 await browser.close()
                 return ToolOutput(text="Error: Empty content retrieved. Possible Captcha or Block.", success=False).model_dump_json()
            
            # Structured Output
            output_data = {
                "url": url,
                "status": status_code,
                "content": text_content[:100000],  # Limit to 100k chars to avoid blowing up context
                "tables": [],
                "metadata": {
                    "title": await page.title()
                }
            }
            
            if extract_tables:
                # Use helper for formatted markdown
                markdown_tables = await _extract_tables(page, max_tables, max_rows)
                # Also get raw data for json
                tables_data = await page.evaluate("""
                    () => {
                        const tables = document.querySelectorAll('table');
                        return Array.from(tables).map(t => {
                            const rows = Array.from(t.innerText.split('\\n'));
                            return rows.filter(r => r.trim().length > 0);
                        });
                    }
                """)
                output_data["tables"] = tables_data
                output_data["markdown_tables"] = markdown_tables
            
            # Screenshot capture
            screenshot_path = None
            if screenshot:
                try:
                    # Create screenshots directory if not exists
                    screenshots_dir = os.path.join(os.getcwd(), "artifacts", "screenshots")
                    os.makedirs(screenshots_dir, exist_ok=True)
                    
                    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
                    screenshot_path = os.path.join(screenshots_dir, filename)
                    
                    await page.screenshot(path=screenshot_path, full_page=False)
                    output_data["metadata"]["screenshot_captured"] = True
                    output_data["metadata"]["screenshot_path"] = screenshot_path
                except Exception as e:
                    logger.error(f"Screenshot failed: {e}")
                    output_data["metadata"]["screenshot_error"] = str(e)
            
            await browser.close()
            
            # Construct ToolOutput
            files = []
            if screenshot_path and os.path.exists(screenshot_path):
                files.append(FileReference(
                    file_id=os.path.basename(screenshot_path),
                    file_type=FileType.IMAGE,
                    path=screenshot_path,
                    size_bytes=os.path.getsize(screenshot_path)
                ))
            
            summary_text = f"Scraped {url} ({len(text_content)} chars)"
            if extract_tables:
                 summary_text += f"\n\n{output_data.get('markdown_tables', '')}"
            else:
                 summary_text += f"\n\n{text_content[:2000]}..."

            return ToolOutput(
                text=summary_text,
                data=DataPayload(
                    data_type="dict",
                    data=output_data
                ),
                files=files,
                tool_name="browser_scrape",
                success=True
            ).model_dump_json()
            
    except Exception as e:
        logger.error(f"Browser scrape failed: {e}")
        return ToolOutput(
            text=f"Error: {str(e)}",
            success=False,
            error=str(e)
        ).model_dump_json()

async def _extract_tables(page: Any, max_tables: int, max_rows: int) -> str:
    """Extract tables from page as markdown."""
    try:
        # We process in python to respect limits easier
        # But we need raw data first. Re-use eval.
        tables_data = await page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                const results = [];
                tables.forEach((table) => {
                    const rows = [];
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = [];
                        tr.querySelectorAll('th, td').forEach(cell => {
                            cells.push(cell.innerText.trim().replace(/\\n/g, ' '));
                        });
                        if (cells.length > 0) rows.push(cells);
                    });
                    if (rows.length > 0) results.push(rows);
                });
                return results;
            }
        """)
        
        if not tables_data: return ""
        
        output = []
        for i, table in enumerate(tables_data[:max_tables]):
            output.append(f"## Table {i + 1}")
            for j, row in enumerate(table[:max_rows]):
                output.append("| " + " | ".join(str(c)[:50] for c in row) + " |")
                if j == 0:
                    output.append("|" + "|".join("---" for _ in row) + "|")
            output.append("")
        
        return "\n".join(output)
        
    except Exception as e:
        return ""
