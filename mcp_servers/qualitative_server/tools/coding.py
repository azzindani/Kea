
import re
from collections import defaultdict, Counter
from shared.mcp.protocol import ToolResult, TextContent

async def text_coding(
    text: str, 
    codes: list[str] = [], 
    auto_code: bool = True
) -> ToolResult:
    """Code qualitative text with categories/themes."""
    
    result = "# 🏷️ Text Coding Analysis\n\n"
    
    # Apply predefined codes
    code_matches = {}
    for code in codes:
        pattern = re.compile(re.escape(code), re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            code_matches[code] = len(matches)
    
    if code_matches:
        result += "## Predefined Codes\n\n"
        result += "| Code | Frequency |\n|------|----------|\n"
        for code, freq in sorted(code_matches.items(), key=lambda x: -x[1]):
            result += f"| {code} | {freq} |\n"
        result += "\n"
    
    # Auto-generate codes (simple keyword extraction)
    if auto_code:
        result += "## Auto-Generated Codes\n\n"
        
        # Simple word frequency
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        # Filter common words
        stopwords = {'that', 'this', 'with', 'have', 'from', 'they', 'been', 'were', 'their', 'which', 'would', 'there', 'about'}
        top_words = sorted(
            [(w, f) for w, f in word_freq.items() if w not in stopwords and f >= 2],
            key=lambda x: -x[1]
        )[:10]
        
        result += "| Potential Code | Frequency |\n|----------------|----------|\n"
        for word, freq in top_words:
            result += f"| {word} | {freq} |\n"
    
    result += f"\n**Text Length**: {len(text)} characters\n"
    result += f"**Word Count**: {len(text.split())}\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def theme_extractor(
    texts: list[str], 
    min_theme_freq: int = 2
) -> ToolResult:
    """Extract themes from multiple text sources."""
    
    result = "# 🎯 Theme Extraction\n\n"
    result += f"**Sources Analyzed**: {len(texts)}\n\n"
    
    # Combine and analyze
    all_words = []
    for text in texts:
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        all_words.extend(words)
    
    # N-gram themes (bigrams)
    bigrams = []
    words_list = re.findall(r'\b[a-zA-Z]{3,}\b', " ".join(texts).lower())
    for i in range(len(words_list) - 1):
        bigrams.append(f"{words_list[i]} {words_list[i+1]}")
    
    bigram_freq = Counter(bigrams)
    
    result += "## Emerging Themes (Bigrams)\n\n"
    result += "| Theme | Frequency | Sources |\n|-------|-----------|--------|\n"
    
    for theme, freq in bigram_freq.most_common(10):
        if freq >= min_theme_freq:
            # Count sources containing theme
            source_count = sum(1 for t in texts if theme in t.lower())
            result += f"| {theme} | {freq} | {source_count}/{len(texts)} |\n"
    
    # Single word themes
    word_freq = Counter(all_words)
    
    result += "\n## Key Concepts (Single Words)\n\n"
    stopwords = {'about', 'would', 'could', 'should', 'their', 'there', 'these', 'those', 'which', 'where', 'while'}
    
    for word, freq in word_freq.most_common(15):
        if word not in stopwords and freq >= min_theme_freq:
            result += f"- **{word}**: {freq} occurrences\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def sentiment_analysis(
    text: str, 
    granularity: str = "document"
) -> ToolResult:
    """Analyze sentiment and emotional tone of text."""
    
    result = "# 💭 Sentiment Analysis\n\n"
    
    # Simple rule-based sentiment
    positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'growth', 'increase', 'improve', 'benefit', 'advantage']
    negative_words = ['bad', 'poor', 'negative', 'fail', 'decline', 'decrease', 'problem', 'risk', 'concern', 'issue']
    
    text_lower = text.lower()
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    total = pos_count + neg_count
    if total > 0:
        sentiment_score = (pos_count - neg_count) / total
    else:
        sentiment_score = 0
    
    result += f"**Positive indicators**: {pos_count}\n"
    result += f"**Negative indicators**: {neg_count}\n"
    result += f"**Sentiment Score**: {sentiment_score:.2f} (-1 to +1)\n\n"
    
    if sentiment_score > 0.3:
        result += "📈 **Overall: Positive**\n"
    elif sentiment_score < -0.3:
        result += "📉 **Overall: Negative**\n"
    else:
        result += "➡️ **Overall: Neutral**\n"
    
    if granularity == "sentence":
        result += "\n## Sentence-Level Analysis\n\n"
        sentences = text.split('.')[:5]
        for i, sent in enumerate(sentences):
            if sent.strip():
                s_pos = sum(1 for w in positive_words if w in sent.lower())
                s_neg = sum(1 for w in negative_words if w in sent.lower())
                emoji = "📈" if s_pos > s_neg else ("📉" if s_neg > s_pos else "➡️")
                result += f"{i+1}. {emoji} {sent.strip()[:60]}...\n"
    
    return ToolResult(content=[TextContent(text=result)])
