from urllib.parse import urlparse
from typing import List

async def source_validator(url: str, check_type: str = "basic") -> str:
    """Validate if a source/website is credible and legitimate."""
    parsed = urlparse(url)
    domain = parsed.netloc
    
    result = f"# ✅ Source Validation\n\n"
    result += f"**URL**: {url}\n"
    result += f"**Domain**: {domain}\n"
    result += f"**Check Type**: {check_type}\n\n"
    
    # Credibility indicators
    indicators = {}
    
    # Domain age and trust signals
    # Academic/government TLDs
    if domain.endswith(('.edu', '.gov', '.ac.uk', '.go.id')):
        indicators["tld_trust"] = ("High", "Government/Academic TLD")
    elif domain.endswith(('.org', '.int')):
        indicators["tld_trust"] = ("Medium-High", "Organization TLD")
    else:
        indicators["tld_trust"] = ("Standard", "Commercial TLD")
    
    # Known authoritative domains
    authoritative = [
        'nature.com', 'science.org', 'sciencedirect.com',
        'pubmed.ncbi.nlm.nih.gov', 'arxiv.org', 'springer.com',
        'reuters.com', 'bbc.com', 'nytimes.com', 'wsj.com',
        'sec.gov', 'imf.org', 'worldbank.org', 'who.int',
    ]
    
    is_authoritative = any(auth in domain for auth in authoritative)
    indicators["authoritative"] = ("Yes" if is_authoritative else "No", "Known authoritative source")
    
    # HTTPS check
    indicators["https"] = ("Yes" if parsed.scheme == "https" else "No", "Secure connection")
    
    # Calculate score
    score = 0.5  # Base score
    if indicators["tld_trust"][0] == "High":
        score += 0.3
    elif indicators["tld_trust"][0] == "Medium-High":
        score += 0.15
    if is_authoritative:
        score += 0.2
    if parsed.scheme == "https":
        score += 0.1
    
    score = min(1.0, score)
    
    result += "## Credibility Indicators\n\n"
    result += "| Indicator | Value | Note |\n|-----------|-------|------|\n"
    for name, (value, note) in indicators.items():
        result += f"| {name} | {value} | {note} |\n"
    
    result += f"\n## Overall Score: {score:.2f}/1.0\n\n"
    
    if score >= 0.8:
        result += "🟢 **Highly Credible** - Authoritative source\n"
    elif score >= 0.6:
        result += "🟡 **Moderately Credible** - Verify claims\n"
    else:
        result += "🔴 **Low Credibility** - Cross-reference required\n"
    
    return result

async def domain_scorer(domains: List[str]) -> str:
    """Score domain trustworthiness for research."""
    result = "# 🏆 Domain Trust Scores\n\n"
    
    # Trust database
    trust_db = {
        # Academic
        'nature.com': 0.95, 'science.org': 0.95, 'arxiv.org': 0.90,
        'pubmed.ncbi.nlm.nih.gov': 0.95, 'ncbi.nlm.nih.gov': 0.95,
        'sciencedirect.com': 0.90, 'springer.com': 0.90,
        # Government
        'sec.gov': 0.95, 'data.gov': 0.90, 'irs.gov': 0.95,
        'who.int': 0.95, 'worldbank.org': 0.90, 'imf.org': 0.90,
        # News
        'reuters.com': 0.85, 'bbc.com': 0.85, 'nytimes.com': 0.80,
        'wsj.com': 0.80, 'ft.com': 0.80,
        # General
        'wikipedia.org': 0.70, 'britannica.com': 0.85,
    }
    
    result += "| Domain | Trust Score | Category |\n|--------|-------------|----------|\n"
    
    for domain in domains:
        domain_clean = domain.lower().replace("www.", "")
        
        if domain_clean in trust_db:
            score = trust_db[domain_clean]
        elif any(tld in domain_clean for tld in ['.edu', '.gov']):
            score = 0.85
        elif any(tld in domain_clean for tld in ['.org']):
            score = 0.70
        else:
            score = 0.50
        
        # Categorize
        if score >= 0.9:
            category = "🟢 Highly Trusted"
        elif score >= 0.7:
            category = "🟡 Trusted"
        elif score >= 0.5:
            category = "🟠 Moderate"
        else:
            category = "🔴 Low Trust"
        
        result += f"| {domain} | {score:.2f} | {category} |\n"
    
    return result
