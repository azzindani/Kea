from __future__ import annotations
import asyncio
from shared.logging import get_logger
import json
from typing import Any, Optional

logger = get_logger(__name__)

async def browser_scrape_tool(url: str, wait_for: Optional[str] = None, extract_tables: bool = True, screenshot: bool = False) -> str:
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
                return f"Error: Access Denied (HTTP {status_code}). Site blocked the scraper."
            
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=10000)
                except Exception:
                    pass
            
            await asyncio.sleep(3)
            
            text_content = await page.evaluate("() => document.body.innerText")
            
            if not text_content or len(text_content.strip()) < 50:
                 await browser.close()
                 return "Error: Empty content retrieved. Possible Captcha or Block."
            
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
            
            if screenshot:
                output_data["metadata"]["screenshot_captured"] = True
                # In future we could base64 encode here if needed
            
            await browser.close()
            return json.dumps(output_data, indent=2)
            
    except Exception as e:
        return f"Error: {str(e)}"

async def _extract_tables(page: Any) -> str:
    """Extract tables from page as markdown."""
    try:
        tables_data = await page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                const results = [];
                tables.forEach((table, tableIndex) => {
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
        for i, table in enumerate(tables_data[:5]):
            output.append(f"## Table {i + 1}")
            for j, row in enumerate(table[:50]):
                output.append("| " + " | ".join(str(c)[:50] for c in row) + " |")
                if j == 0:
                    output.append("|" + "|".join("---" for _ in row) + "|")
            output.append("")
        
        return "\n".join(output)
        
    except Exception as e:
        return ""
