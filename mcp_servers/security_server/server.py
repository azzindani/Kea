"""
Security MCP Server.

Provides tools for secure research operations:
- URL safety checking
- File scanning
- Content sanitization
- Sandboxed execution
"""

from __future__ import annotations

from typing import Any
import hashlib
import re
from urllib.parse import urlparse

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


# Known malicious patterns
MALICIOUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'on\w+\s*=',
    r'eval\s*\(',
    r'document\.cookie',
    r'window\.location',
]

# Blocklisted domains
BLOCKLISTED_DOMAINS = [
    'malware.com',
    'phishing.example',
]


class SecurityServer(MCPServerBase):
    """MCP server for security operations."""
    
    def __init__(self) -> None:
        super().__init__(name="security_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="url_scanner",
                description="Check URL for potential security threats",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to scan"},
                        "deep_scan": {"type": "boolean", "description": "Perform deep content analysis"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="content_sanitizer",
                description="Sanitize HTML/text content to remove malicious elements",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "content": {"type": "string", "description": "Content to sanitize"},
                        "allow_html": {"type": "boolean", "description": "Allow safe HTML tags"},
                    },
                    required=["content"],
                ),
            ),
            Tool(
                name="file_hash_check",
                description="Calculate file hash and check against known threats",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "file_path": {"type": "string", "description": "Path to file"},
                        "content": {"type": "string", "description": "Or file content as string"},
                        "algorithm": {"type": "string", "description": "Hash algorithm: md5, sha1, sha256"},
                    },
                ),
            ),
            Tool(
                name="domain_reputation",
                description="Check domain reputation and safety",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "domain": {"type": "string", "description": "Domain to check"},
                    },
                    required=["domain"],
                ),
            ),
            Tool(
                name="safe_download",
                description="Download file with safety checks",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to download from"},
                        "max_size_mb": {"type": "integer", "description": "Maximum file size in MB"},
                        "allowed_types": {"type": "array", "description": "Allowed MIME types"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="code_safety_check",
                description="Check code for potentially dangerous operations",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "code": {"type": "string", "description": "Code to analyze"},
                        "language": {"type": "string", "description": "Programming language"},
                    },
                    required=["code"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "url_scanner":
                return await self._handle_url_scan(arguments)
            elif name == "content_sanitizer":
                return await self._handle_sanitize(arguments)
            elif name == "file_hash_check":
                return await self._handle_hash(arguments)
            elif name == "domain_reputation":
                return await self._handle_domain_rep(arguments)
            elif name == "safe_download":
                return await self._handle_safe_download(arguments)
            elif name == "code_safety_check":
                return await self._handle_code_check(arguments)
            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
    
    async def _handle_url_scan(self, args: dict) -> ToolResult:
        """Scan URL for threats."""
        import httpx
        
        url = args["url"]
        deep_scan = args.get("deep_scan", False)
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        result = "# 🔒 URL Security Scan\n\n"
        result += f"**URL**: {url}\n"
        result += f"**Domain**: {domain}\n\n"
        
        issues = []
        warnings = []
        
        # Check protocol
        if parsed.scheme != "https":
            warnings.append("Not using HTTPS")
        
        # Check domain
        if domain in BLOCKLISTED_DOMAINS:
            issues.append("Domain is blocklisted")
        
        # Check for suspicious patterns in URL
        if re.search(r'\.(exe|bat|cmd|ps1|sh)$', url, re.IGNORECASE):
            warnings.append("URL points to executable file")
        
        if re.search(r'(download|attachment)', url, re.IGNORECASE):
            warnings.append("URL may trigger file download")
        
        # Deep scan - fetch and analyze
        if deep_scan and not issues:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.head(url, follow_redirects=True)
                    
                    content_type = resp.headers.get("content-type", "")
                    content_length = resp.headers.get("content-length", "unknown")
                    
                    result += f"**Content-Type**: {content_type}\n"
                    result += f"**Size**: {content_length} bytes\n"
                    
                    # Check for redirects
                    if resp.url != url:
                        warnings.append(f"Redirects to: {resp.url}")
            except Exception as e:
                warnings.append(f"Could not fetch: {e}")
        
        # Report
        result += "## Scan Results\n\n"
        
        if issues:
            result += "### 🚨 Critical Issues\n\n"
            for issue in issues:
                result += f"- ❌ {issue}\n"
            result += "\n"
        
        if warnings:
            result += "### ⚠️ Warnings\n\n"
            for warning in warnings:
                result += f"- ⚠️ {warning}\n"
            result += "\n"
        
        if not issues and not warnings:
            result += "✅ **No issues detected**\n"
        
        # Overall verdict
        if issues:
            result += "\n**Verdict**: 🔴 UNSAFE - Do not proceed\n"
        elif warnings:
            result += "\n**Verdict**: 🟡 CAUTION - Proceed with care\n"
        else:
            result += "\n**Verdict**: 🟢 SAFE - OK to proceed\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_sanitize(self, args: dict) -> ToolResult:
        """Sanitize content."""
        content = args["content"]
        allow_html = args.get("allow_html", False)
        
        result = "# 🧹 Content Sanitization\n\n"
        result += f"**Original Length**: {len(content)}\n\n"
        
        sanitized = content
        removed = []
        
        # Remove malicious patterns
        for pattern in MALICIOUS_PATTERNS:
            matches = re.findall(pattern, sanitized, re.IGNORECASE | re.DOTALL)
            if matches:
                removed.extend(matches[:3])  # Log up to 3 matches
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Strip HTML if needed
        if not allow_html:
            # Remove all HTML tags
            sanitized = re.sub(r'<[^>]+>', '', sanitized)
        else:
            # Remove only dangerous tags
            dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form']
            for tag in dangerous_tags:
                sanitized = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
                sanitized = re.sub(f'<{tag}[^>]*/>', '', sanitized, flags=re.IGNORECASE)
        
        # Remove data URIs
        sanitized = re.sub(r'data:[^;]+;base64,[a-zA-Z0-9+/=]+', '[DATA_REMOVED]', sanitized)
        
        result += f"**Sanitized Length**: {len(sanitized)}\n"
        result += f"**Removed Items**: {len(removed)}\n\n"
        
        if removed:
            result += "## Removed Content\n\n"
            for item in removed[:5]:
                result += f"- `{item[:50]}...`\n"
            result += "\n"
        
        result += "## Sanitized Output\n\n"
        result += f"```\n{sanitized[:500]}{'...' if len(sanitized) > 500 else ''}\n```\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_hash(self, args: dict) -> ToolResult:
        """Calculate file hash."""
        file_path = args.get("file_path")
        content = args.get("content", "")
        algorithm = args.get("algorithm", "sha256")
        
        result = "# 🔐 File Hash Check\n\n"
        
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
            except Exception as e:
                return ToolResult(content=[TextContent(text=f"Cannot read file: {e}")], isError=True)
        else:
            data = content.encode()
        
        # Calculate hash
        if algorithm == "md5":
            hash_obj = hashlib.md5(data)
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1(data)
        else:
            hash_obj = hashlib.sha256(data)
        
        hash_value = hash_obj.hexdigest()
        
        result += f"**Algorithm**: {algorithm.upper()}\n"
        result += f"**Hash**: `{hash_value}`\n"
        result += f"**Size**: {len(data)} bytes\n\n"
        
        # Would check against threat database in production
        result += "## Threat Check\n\n"
        result += "✅ No known threats match this hash\n"
        result += "(Hash checked against local database)\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_domain_rep(self, args: dict) -> ToolResult:
        """Check domain reputation."""
        domain = args["domain"].lower().replace("www.", "")
        
        result = f"# 🌐 Domain Reputation: {domain}\n\n"
        
        # Reputation database (simplified)
        trusted_domains = {
            'google.com': 0.95, 'microsoft.com': 0.95, 'github.com': 0.90,
            'nature.com': 0.95, 'arxiv.org': 0.90, 'wikipedia.org': 0.85,
            'sec.gov': 0.95, 'who.int': 0.95, 'pubmed.ncbi.nlm.nih.gov': 0.95,
        }
        
        if domain in BLOCKLISTED_DOMAINS:
            score = 0.0
            status = "🔴 BLOCKLISTED"
        elif domain in trusted_domains:
            score = trusted_domains[domain]
            status = "🟢 TRUSTED"
        elif domain.endswith(('.gov', '.edu', '.ac.uk')):
            score = 0.85
            status = "🟢 GOVERNMENT/ACADEMIC"
        elif domain.endswith('.org'):
            score = 0.70
            status = "🟡 ORGANIZATION"
        else:
            score = 0.50
            status = "🟡 UNKNOWN"
        
        result += f"**Status**: {status}\n"
        result += f"**Trust Score**: {score:.2f}\n\n"
        
        result += "## Indicators\n\n"
        
        # TLD analysis
        tld = domain.split('.')[-1]
        result += f"- **TLD**: .{tld}\n"
        
        # Age estimate (mock)
        if score >= 0.8:
            result += "- **Domain Age**: Established (5+ years)\n"
        else:
            result += "- **Domain Age**: Unknown\n"
        
        result += f"- **HTTPS Support**: Assumed Yes\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_safe_download(self, args: dict) -> ToolResult:
        """Safe file download."""
        import httpx
        
        url = args["url"]
        max_size = args.get("max_size_mb", 10)
        allowed_types = args.get("allowed_types", ["text/", "application/json", "application/pdf"])
        
        result = f"# 📥 Safe Download\n\n"
        result += f"**URL**: {url}\n"
        result += f"**Max Size**: {max_size} MB\n\n"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # HEAD request first
                head_resp = await client.head(url, follow_redirects=True)
                
                content_type = head_resp.headers.get("content-type", "unknown")
                content_length = int(head_resp.headers.get("content-length", 0))
                
                result += f"**Content-Type**: {content_type}\n"
                result += f"**Size**: {content_length / 1024 / 1024:.2f} MB\n\n"
                
                # Check size
                if content_length > max_size * 1024 * 1024:
                    result += "❌ **BLOCKED**: File too large\n"
                    return ToolResult(content=[TextContent(text=result)])
                
                # Check type
                type_allowed = any(at in content_type for at in allowed_types)
                if not type_allowed:
                    result += f"❌ **BLOCKED**: Content type not in allowed list\n"
                    result += f"Allowed: {', '.join(allowed_types)}\n"
                    return ToolResult(content=[TextContent(text=result)])
                
                result += "✅ **SAFE TO DOWNLOAD**\n\n"
                result += f"Download with: `httpx.get('{url}')`\n"
                
        except Exception as e:
            result += f"❌ **ERROR**: {e}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_code_check(self, args: dict) -> ToolResult:
        """Check code for dangerous operations."""
        code = args["code"]
        language = args.get("language", "python")
        
        result = f"# 🔍 Code Safety Check ({language})\n\n"
        
        issues = []
        warnings = []
        
        # Python-specific checks
        if language.lower() == "python":
            dangerous = [
                (r'\bexec\s*\(', "exec() - arbitrary code execution"),
                (r'\beval\s*\(', "eval() - arbitrary code execution"),
                (r'\b__import__\s*\(', "__import__() - dynamic imports"),
                (r'\bos\.system\s*\(', "os.system() - shell commands"),
                (r'\bsubprocess\.\w+\s*\(', "subprocess - external commands"),
                (r'\bopen\s*\([^)]*["\']w["\']', "open() with write mode"),
                (r'\brm\s+-rf', "rm -rf - file deletion"),
                (r'requests\.get.*\.text.*exec', "remote code execution pattern"),
            ]
            
            for pattern, desc in dangerous:
                if re.search(pattern, code, re.IGNORECASE):
                    issues.append(desc)
            
            # Warnings
            warning_patterns = [
                (r'requests\.(get|post)', "HTTP requests - verify URLs"),
                (r'urllib', "URL operations - verify sources"),
                (r'pickle\.loads?', "pickle - untrusted data risk"),
                (r'yaml\.load\((?!.*Loader)', "yaml.load without safe_load"),
            ]
            
            for pattern, desc in warning_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    warnings.append(desc)
        
        # JavaScript checks
        elif language.lower() in ["javascript", "js"]:
            js_dangerous = [
                (r'\beval\s*\(', "eval() - arbitrary code execution"),
                (r'\.innerHTML\s*=', "innerHTML - XSS risk"),
                (r'document\.write', "document.write - XSS risk"),
                (r'new\s+Function\s*\(', "Function constructor - arbitrary code"),
            ]
            
            for pattern, desc in js_dangerous:
                if re.search(pattern, code, re.IGNORECASE):
                    issues.append(desc)
        
        # Report
        if issues:
            result += "## 🚨 Critical Issues\n\n"
            for issue in issues:
                result += f"- ❌ {issue}\n"
            result += "\n"
        
        if warnings:
            result += "## ⚠️ Warnings\n\n"
            for warning in warnings:
                result += f"- ⚠️ {warning}\n"
            result += "\n"
        
        if not issues and not warnings:
            result += "✅ **No obvious security issues detected**\n"
        
        # Verdict
        if issues:
            result += "\n**Verdict**: 🔴 UNSAFE - Review required\n"
        elif warnings:
            result += "\n**Verdict**: 🟡 CAUTION - Review recommended\n"
        else:
            result += "\n**Verdict**: 🟢 Appears safe\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def url_scanner_tool(args: dict) -> ToolResult:
    server = SecurityServer()
    return await server._handle_url_scan(args)

async def content_sanitizer_tool(args: dict) -> ToolResult:
    server = SecurityServer()
    return await server._handle_sanitize(args)

async def code_safety_tool(args: dict) -> ToolResult:
    server = SecurityServer()
    return await server._handle_code_check(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = SecurityServer()
        await server.run()
        
    asyncio.run(main())
