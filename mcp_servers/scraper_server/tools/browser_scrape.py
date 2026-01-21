"""
Browser Scrape Tool.

Headless browser scraping with Playwright and stealth capabilities.
"""

from __future__ import annotations

import asyncio
from typing import Any

from shared.mcp.protocol import ToolResult, TextContent, ImageContent
from shared.logging import get_logger


logger = get_logger(__name__)


async def browser_scrape_tool(arguments: dict) -> ToolResult:
    """
    Scrape URL using headless browser.
    
    Args:
        arguments: Tool arguments containing:
            - url: URL to scrape
            - wait_for: CSS selector to wait for
            - extract_tables: Extract tables as structured data
            - screenshot: Take screenshot
    
    Returns:
        ToolResult with page content, tables, and optional screenshot
    """
    url = arguments.get("url", "")
    wait_for = arguments.get("wait_for")
    extract_tables = arguments.get("extract_tables", True)
    take_screenshot = arguments.get("screenshot", False)
    
    if not url:
        return ToolResult(
            content=[TextContent(text="Error: URL is required")],
            isError=True
        )
    
    try:
        from playwright.async_api import async_playwright
        from fake_useragent import UserAgent
    except ImportError:
        return ToolResult(
            content=[TextContent(text="Error: Playwright or fake-useragent not installed. Run: pip install playwright fake-useragent")],
            isError=True
        )
    
    try:
        ua = UserAgent()
        user_agent = ua.random
        
        async with async_playwright() as p:
            # Launch browser with stealth settings
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
            
            # Anti-detection scripts
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Navigate to URL
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            status_code = response.status if response else 0
            
            if status_code in [403, 401]:
                await browser.close()
                logger.warning(f"⛔ Access Denied ({status_code}) for {url}")
                return ToolResult(
                    content=[TextContent(text=f"Error: Access Denied (HTTP {status_code}). Site blocked the scraper.")],
                    isError=True
                )
            
            # Wait for specific element if requested
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=10000)
                except Exception:
                    logger.warning(f"Selector '{wait_for}' not found, continuing anyway")
            
            # Allow dynamic content to load
            await asyncio.sleep(3)
            
            results: list[TextContent | ImageContent] = []
            
            # Get page content
            text_content = await page.evaluate("() => document.body.innerText")
            
            if not text_content or len(text_content.strip()) < 50:
                 # Likely a blocked page alias or captcha
                 await browser.close()
                 return ToolResult(
                     content=[TextContent(text="Error: Empty content retrieved. Possible Captcha or Block.")],
                     isError=True
                 )
            
            results.append(TextContent(text=f"# Page Content\n\n{text_content[:30000]}"))
            
            # Extract tables if requested
            if extract_tables:
                tables = await _extract_tables(page)
                if tables:
                    results.append(TextContent(text=f"\n\n# Extracted Tables\n\n{tables}"))
            
            # Take screenshot if requested
            if take_screenshot:
                screenshot_bytes = await page.screenshot(type="png")
                import base64
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                results.append(ImageContent(data=screenshot_b64, mimeType="image/png"))
            
            await browser.close()
            
            logger.info(
                "Browser scrape completed",
                extra={"url": url, "content_length": len(text_content)}
            )
            
            return ToolResult(content=results)
            
    except Exception as e:
        logger.error(f"Browser scrape error for {url}: {e}")
        return ToolResult(
            content=[TextContent(text=f"Error: {str(e)}")],
            isError=True
        )


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
                        if (cells.length > 0) {
                            rows.push(cells);
                        }
                    });
                    if (rows.length > 0) {
                        results.push(rows);
                    }
                });
                
                return results;
            }
        """)
        
        if not tables_data:
            return ""
        
        # Convert to markdown
        output = []
        for i, table in enumerate(tables_data[:5]):  # Limit to 5 tables
            output.append(f"## Table {i + 1}")
            
            for j, row in enumerate(table[:50]):  # Limit rows
                output.append("| " + " | ".join(str(c)[:50] for c in row) + " |")
                if j == 0:
                    output.append("|" + "|".join("---" for _ in row) + "|")
            
            output.append("")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.warning(f"Table extraction failed: {e}")
        return ""
