from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Dict, Any, List

async def get_accessibility_tree(selector: str = None) -> Dict[str, Any]:
    """
    Get the accessibility tree for the page or specific element.
    """
    page = await BrowserSession.get_page()
    element = await page.locator(selector).element_handle() if selector else None
    return await page.accessibility.snapshot(root=element)

async def check_accessibility(selector: str = "body") -> Dict[str, Any]:
    """
    Perform a basic accessibility check using a simple audit script injected into the page.
    Checks for: missing alt text, empty buttons, missing form labels.
    """
    page = await BrowserSession.get_page()
    
    # We inject a simple JS audit
    audit_script = """(sel) => {
        const root = document.querySelector(sel);
        if (!root) return {error: "Root element not found"};
        
        const issues = [];
        
        // 1. Check Images
        root.querySelectorAll('img').forEach(img => {
            if (!img.alt && img.getAttribute('role') !== 'presentation') {
                issues.push({type: 'missing_alt', element: img.src || 'img', message: 'Image missing alt text'});
            }
        });
        
        // 2. Check Buttons
        root.querySelectorAll('button').forEach(btn => {
            if (!btn.innerText.trim() && !btn.getAttribute('aria-label') && !btn.getAttribute('aria-labelledby')) {
                issues.push({type: 'empty_button', element: btn.class || 'button', message: 'Button text empty and no label'});
            }
        });
        
        // 3. Check Inputs
        root.querySelectorAll('input').forEach(input => {
            if (input.type === 'hidden' || input.type === 'submit') return;
            if (!input.id || !document.querySelector(`label[for="${input.id}"]`)) {
                if (!input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
                   issues.push({type: 'missing_label', element: input.name || input.id, message: 'Input missing associated label'}); 
                }
            }
        });
        
        return {
            total_issues: issues.length,
            issues: issues
        };
    }"""
    
    return await page.evaluate(audit_script, selector)

async def audit_seo() -> Dict[str, Any]:
    """
    Check basic SEO tags: Title, Meta Description, H1 existence, Canonical.
    """
    page = await BrowserSession.get_page()
    
    return await page.evaluate("""() => {
        const title = document.title;
        const metaDesc = document.querySelector('meta[name="description"]')?.content;
        const h1 = document.querySelector('h1')?.innerText;
        const canonical = document.querySelector('link[rel="canonical"]')?.href;
        
        const h1Count = document.querySelectorAll('h1').length;
        
        return {
            title: title,
            title_length: title ? title.length : 0,
            meta_description: metaDesc || null,
            h1_content: h1 || null,
            h1_count: h1Count,
            canonical_url: canonical || null,
            issues: [
                !title ? "Missing Title" : null,
                !metaDesc ? "Missing Meta Description" : null,
                h1Count === 0 ? "Missing H1" : null,
                h1Count > 1 ? "Multiple H1 tags" : null
            ].filter(Boolean)
        };
    }""")
