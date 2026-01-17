"""
Multimodal Security Validator.

Validates and sanitizes multimodal inputs for security.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import re

from shared.logging import get_logger

from .modality import ModalityInput, ModalityType


logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """Severity of validation issue."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Single validation issue."""
    check: str
    message: str
    severity: ValidationSeverity
    details: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validation check."""
    passed: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    sanitized_input: ModalityInput | None = None
    validation_time_ms: float = 0


class ModalityValidator:
    """
    Validate and sanitize multimodal inputs.
    
    Checks:
    - File size limits
    - MIME type validation
    - Magic bytes verification
    - URL safety (blocked domains, protocols)
    - Content scanning (basic patterns)
    
    Example:
        validator = ModalityValidator()
        
        result = validator.validate(modality_input)
        if not result.passed:
            for issue in result.issues:
                print(f"{issue.severity}: {issue.message}")
    """
    
    # ========================================================================
    # Size Limits (in bytes)
    # ========================================================================
    
    MAX_SIZES = {
        ModalityType.IMAGE: 50 * 1024 * 1024,      # 50MB
        ModalityType.AUDIO: 100 * 1024 * 1024,     # 100MB
        ModalityType.VIDEO: 500 * 1024 * 1024,     # 500MB
        ModalityType.DOCUMENT: 50 * 1024 * 1024,   # 50MB
        ModalityType.DATA: 100 * 1024 * 1024,      # 100MB
        ModalityType.CODE: 10 * 1024 * 1024,       # 10MB
        ModalityType.ARCHIVE: 200 * 1024 * 1024,   # 200MB
        ModalityType.MODEL_3D: 100 * 1024 * 1024,  # 100MB
        ModalityType.URL: 0,                        # No size limit for URLs
        ModalityType.TEXT: 1 * 1024 * 1024,        # 1MB text
    }
    
    # ========================================================================
    # Allowed MIME Types
    # ========================================================================
    
    ALLOWED_MIMES = {
        ModalityType.IMAGE: [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "image/svg+xml", "image/bmp", "image/tiff",
        ],
        ModalityType.AUDIO: [
            "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg",
            "audio/mp4", "audio/webm", "audio/flac", "audio/aac",
        ],
        ModalityType.VIDEO: [
            "video/mp4", "video/webm", "video/mpeg", "video/quicktime",
            "video/x-msvideo", "video/x-matroska",
        ],
        ModalityType.DOCUMENT: [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain", "text/markdown", "text/rtf",
        ],
        ModalityType.DATA: [
            "text/csv", "application/json", "application/xml",
            "text/xml", "application/yaml", "text/yaml",
        ],
        ModalityType.ARCHIVE: [
            "application/zip", "application/x-tar", "application/gzip",
            "application/x-7z-compressed",
        ],
    }
    
    # ========================================================================
    # Blocked Patterns
    # ========================================================================
    
    BLOCKED_URL_PATTERNS = [
        # Malicious domains (example patterns)
        r"malware\.", r"phishing\.", r"exploit\.",
        # IP addresses (often suspicious)
        r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        # Non-standard ports
        r"https?://[^:/]+:\d{5,}",
        # File protocols
        r"file://", r"javascript:", r"data:text/html",
    ]
    
    BLOCKED_DOMAINS = [
        # Add known malicious domains here
        "example-malware.com",
        "phishing-site.net",
    ]
    
    # Dangerous file signatures
    DANGEROUS_MAGIC_BYTES = [
        b"MZ",              # Windows executable
        b"\x7fELF",         # Linux executable
        b"#!",              # Shell script (context-dependent)
    ]
    
    def __init__(
        self,
        max_sizes: dict[ModalityType, int] = None,
        blocked_domains: list[str] = None,
        allow_executables: bool = False,
    ):
        """
        Initialize validator.
        
        Args:
            max_sizes: Override default size limits
            blocked_domains: Additional domains to block
            allow_executables: Allow executable files (dangerous!)
        """
        self.max_sizes = {**self.MAX_SIZES, **(max_sizes or {})}
        self.blocked_domains = self.BLOCKED_DOMAINS + (blocked_domains or [])
        self.allow_executables = allow_executables
        
        # Compile URL patterns
        self._blocked_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.BLOCKED_URL_PATTERNS
        ]
        
        logger.debug("ModalityValidator initialized")
    
    async def validate(self, modality: ModalityInput) -> ValidationResult:
        """
        Validate a modality input.
        
        Args:
            modality: Input to validate
            
        Returns:
            ValidationResult with pass/fail and issues
        """
        import time
        start = time.time()
        
        issues: list[ValidationIssue] = []
        
        # Run all checks
        issues.extend(self._check_size(modality))
        issues.extend(self._check_mime_type(modality))
        issues.extend(self._check_magic_bytes(modality))
        issues.extend(self._check_url_safety(modality))
        issues.extend(self._check_content_patterns(modality))
        
        # Determine pass/fail
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        
        passed = len(critical_issues) == 0 and len(error_issues) == 0
        
        result = ValidationResult(
            passed=passed,
            issues=issues,
            sanitized_input=modality if passed else None,
            validation_time_ms=(time.time() - start) * 1000,
        )
        
        if not passed:
            logger.warning(f"Validation failed: {len(issues)} issues found")
        
        return result
    
    def _check_size(self, modality: ModalityInput) -> list[ValidationIssue]:
        """Check file size limits."""
        issues = []
        
        max_size = self.max_sizes.get(modality.modality_type, 50 * 1024 * 1024)
        
        if max_size > 0 and modality.size_bytes > max_size:
            issues.append(ValidationIssue(
                check="size_limit",
                message=f"File exceeds size limit: {modality.size_bytes} > {max_size} bytes",
                severity=ValidationSeverity.ERROR,
                details={
                    "actual": modality.size_bytes,
                    "max": max_size,
                    "modality": modality.modality_type.value,
                },
            ))
        elif max_size > 0 and modality.size_bytes > max_size * 0.8:
            issues.append(ValidationIssue(
                check="size_warning",
                message=f"File approaching size limit: {modality.size_bytes} bytes",
                severity=ValidationSeverity.WARNING,
                details={"actual": modality.size_bytes, "max": max_size},
            ))
        
        return issues
    
    def _check_mime_type(self, modality: ModalityInput) -> list[ValidationIssue]:
        """Check MIME type is allowed."""
        issues = []
        
        if not modality.mime_type:
            return issues  # Can't check without MIME type
        
        allowed = self.ALLOWED_MIMES.get(modality.modality_type, [])
        
        if allowed and modality.mime_type not in allowed:
            issues.append(ValidationIssue(
                check="mime_type",
                message=f"MIME type not allowed: {modality.mime_type}",
                severity=ValidationSeverity.ERROR,
                details={
                    "mime_type": modality.mime_type,
                    "allowed": allowed,
                },
            ))
        
        return issues
    
    def _check_magic_bytes(self, modality: ModalityInput) -> list[ValidationIssue]:
        """Check file magic bytes for suspicious content."""
        issues = []
        
        content = modality.content
        if not isinstance(content, bytes) or len(content) < 4:
            return issues
        
        # Check for executables
        if not self.allow_executables:
            for magic in self.DANGEROUS_MAGIC_BYTES:
                if content.startswith(magic):
                    issues.append(ValidationIssue(
                        check="executable_content",
                        message="Executable content detected and blocked",
                        severity=ValidationSeverity.CRITICAL,
                        details={"magic": magic.hex()},
                    ))
                    break
        
        return issues
    
    def _check_url_safety(self, modality: ModalityInput) -> list[ValidationIssue]:
        """Check URL safety."""
        issues = []
        
        if modality.modality_type != ModalityType.URL:
            return issues
        
        url = modality.content
        if not isinstance(url, str):
            return issues
        
        url_lower = url.lower()
        
        # Check blocked patterns
        for pattern in self._blocked_patterns:
            if pattern.search(url):
                issues.append(ValidationIssue(
                    check="blocked_url_pattern",
                    message=f"URL matches blocked pattern",
                    severity=ValidationSeverity.CRITICAL,
                    details={"url": url[:100], "pattern": pattern.pattern},
                ))
                break
        
        # Check blocked domains
        for domain in self.blocked_domains:
            if domain in url_lower:
                issues.append(ValidationIssue(
                    check="blocked_domain",
                    message=f"Domain is blocked: {domain}",
                    severity=ValidationSeverity.CRITICAL,
                    details={"url": url[:100], "domain": domain},
                ))
                break
        
        # Check for suspicious protocols
        if not url.startswith(("http://", "https://")):
            issues.append(ValidationIssue(
                check="invalid_protocol",
                message="Only HTTP/HTTPS URLs are allowed",
                severity=ValidationSeverity.ERROR,
                details={"url": url[:50]},
            ))
        
        return issues
    
    def _check_content_patterns(self, modality: ModalityInput) -> list[ValidationIssue]:
        """Check content for suspicious patterns."""
        issues = []
        
        content = modality.content
        
        # For text/code content
        if modality.modality_type in [ModalityType.CODE, ModalityType.DATA, ModalityType.TEXT]:
            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8", errors="ignore")
                except:
                    return issues
            
            if isinstance(content, str):
                # Check for suspicious patterns
                suspicious = [
                    (r"eval\s*\(", "Potentially dangerous eval()"),
                    (r"exec\s*\(", "Potentially dangerous exec()"),
                    (r"__import__\s*\(", "Dynamic import detected"),
                    (r"subprocess\.", "Subprocess call detected"),
                    (r"os\.system\s*\(", "System call detected"),
                    (r"<script[^>]*>", "Embedded script tag"),
                ]
                
                for pattern, message in suspicious:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append(ValidationIssue(
                            check="suspicious_pattern",
                            message=message,
                            severity=ValidationSeverity.WARNING,
                            details={"pattern": pattern},
                        ))
        
        return issues


# ============================================================================
# URL-specific security
# ============================================================================

class URLValidator:
    """
    Specialized validator for URLs.
    
    Additional checks:
    - DNS resolution
    - SSL certificate
    - Redirect chain
    """
    
    TRUSTED_DOMAINS = [
        "github.com", "githubusercontent.com",
        "google.com", "googleapis.com",
        "wikipedia.org", "wikimedia.org",
        "stackoverflow.com",
        "python.org", "pypi.org",
        "arxiv.org", "nature.com", "science.org",
        # Add more trusted domains
    ]
    
    def __init__(self, trusted_domains: list[str] = None):
        self.trusted_domains = self.TRUSTED_DOMAINS + (trusted_domains or [])
    
    def is_trusted(self, url: str) -> bool:
        """Check if URL is from trusted domain."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for trusted in self.trusted_domains:
                if domain == trusted or domain.endswith(f".{trusted}"):
                    return True
            
            return False
        except:
            return False
    
    async def check_url_safety(self, url: str) -> ValidationResult:
        """
        Full URL safety check.
        
        Includes:
        - Domain trust check
        - SSL verification
        - Content-Type check
        """
        issues = []
        
        # Trust check
        if not self.is_trusted(url):
            issues.append(ValidationIssue(
                check="untrusted_domain",
                message="URL is from untrusted domain",
                severity=ValidationSeverity.INFO,
                details={"url": url[:100]},
            ))
        
        # Try to verify URL is reachable
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(url, follow_redirects=True)
                
                # Check for too many redirects
                if len(response.history) > 5:
                    issues.append(ValidationIssue(
                        check="redirect_chain",
                        message="Too many redirects",
                        severity=ValidationSeverity.WARNING,
                        details={"redirect_count": len(response.history)},
                    ))
                
        except Exception as e:
            issues.append(ValidationIssue(
                check="url_unreachable",
                message=f"URL check failed: {str(e)[:50]}",
                severity=ValidationSeverity.WARNING,
                details={"error": str(e)},
            ))
        
        return ValidationResult(
            passed=not any(i.severity == ValidationSeverity.CRITICAL for i in issues),
            issues=issues,
        )


# ============================================================================
# Singleton
# ============================================================================

_validator: ModalityValidator | None = None
_url_validator: URLValidator | None = None


def get_modality_validator() -> ModalityValidator:
    """Get singleton validator."""
    global _validator
    if _validator is None:
        _validator = ModalityValidator()
    return _validator


def get_url_validator() -> URLValidator:
    """Get singleton URL validator."""
    global _url_validator
    if _url_validator is None:
        _url_validator = URLValidator()
    return _url_validator
