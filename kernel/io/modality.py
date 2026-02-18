"""
Multimodal Input/Output Handler.

Handles extraction and processing of various input modalities.
Provides output sockets for future multimodal generation.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from shared.logging import get_logger


logger = get_logger(__name__)


# ============================================================================
# Modality Types
# ============================================================================

class ModalityType(Enum):
    """Supported input/output modalities."""
    TEXT = "text"
    URL = "url"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"       # PDF, DOCX, XLSX
    CODE = "code"
    DATA = "data"               # CSV, JSON, XML
    ARCHIVE = "archive"         # ZIP, TAR
    MODEL_3D = "model_3d"       # OBJ, GLTF, STL


# MIME type mappings
MIME_TO_MODALITY = {
    # Images
    "image/jpeg": ModalityType.IMAGE,
    "image/png": ModalityType.IMAGE,
    "image/gif": ModalityType.IMAGE,
    "image/webp": ModalityType.IMAGE,
    "image/svg+xml": ModalityType.IMAGE,
    "image/bmp": ModalityType.IMAGE,
    # Audio
    "audio/mpeg": ModalityType.AUDIO,
    "audio/wav": ModalityType.AUDIO,
    "audio/ogg": ModalityType.AUDIO,
    "audio/mp4": ModalityType.AUDIO,
    "audio/webm": ModalityType.AUDIO,
    "audio/flac": ModalityType.AUDIO,
    # Video
    "video/mp4": ModalityType.VIDEO,
    "video/webm": ModalityType.VIDEO,
    "video/mpeg": ModalityType.VIDEO,
    "video/quicktime": ModalityType.VIDEO,
    "video/x-msvideo": ModalityType.VIDEO,
    # Documents
    "application/pdf": ModalityType.DOCUMENT,
    "application/msword": ModalityType.DOCUMENT,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ModalityType.DOCUMENT,
    "application/vnd.ms-excel": ModalityType.DOCUMENT,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ModalityType.DOCUMENT,
    "application/vnd.ms-powerpoint": ModalityType.DOCUMENT,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ModalityType.DOCUMENT,
    # Data
    "text/csv": ModalityType.DATA,
    "application/json": ModalityType.DATA,
    "application/xml": ModalityType.DATA,
    "text/xml": ModalityType.DATA,
    # Code
    "text/x-python": ModalityType.CODE,
    "text/javascript": ModalityType.CODE,
    "text/html": ModalityType.CODE,
    "text/css": ModalityType.CODE,
    # Archives
    "application/zip": ModalityType.ARCHIVE,
    "application/x-tar": ModalityType.ARCHIVE,
    "application/gzip": ModalityType.ARCHIVE,
    "application/x-rar-compressed": ModalityType.ARCHIVE,
    # 3D Models
    "model/gltf+json": ModalityType.MODEL_3D,
    "model/gltf-binary": ModalityType.MODEL_3D,
    "model/obj": ModalityType.MODEL_3D,
    "model/stl": ModalityType.MODEL_3D,
}

# Extension mappings (fallback)
EXT_TO_MODALITY = {
    # Images
    ".jpg": ModalityType.IMAGE, ".jpeg": ModalityType.IMAGE,
    ".png": ModalityType.IMAGE, ".gif": ModalityType.IMAGE,
    ".webp": ModalityType.IMAGE, ".svg": ModalityType.IMAGE,
    # Audio
    ".mp3": ModalityType.AUDIO, ".wav": ModalityType.AUDIO,
    ".ogg": ModalityType.AUDIO, ".m4a": ModalityType.AUDIO,
    ".flac": ModalityType.AUDIO,
    # Video
    ".mp4": ModalityType.VIDEO, ".webm": ModalityType.VIDEO,
    ".avi": ModalityType.VIDEO, ".mov": ModalityType.VIDEO,
    ".mkv": ModalityType.VIDEO,
    # Documents
    ".pdf": ModalityType.DOCUMENT, ".doc": ModalityType.DOCUMENT,
    ".docx": ModalityType.DOCUMENT, ".xls": ModalityType.DOCUMENT,
    ".xlsx": ModalityType.DOCUMENT, ".ppt": ModalityType.DOCUMENT,
    ".pptx": ModalityType.DOCUMENT,
    # Data
    ".csv": ModalityType.DATA, ".json": ModalityType.DATA,
    ".xml": ModalityType.DATA, ".yaml": ModalityType.DATA,
    ".yml": ModalityType.DATA,
    # Code
    ".py": ModalityType.CODE, ".js": ModalityType.CODE,
    ".ts": ModalityType.CODE, ".html": ModalityType.CODE,
    ".css": ModalityType.CODE, ".sql": ModalityType.CODE,
    # Archives
    ".zip": ModalityType.ARCHIVE, ".tar": ModalityType.ARCHIVE,
    ".gz": ModalityType.ARCHIVE, ".rar": ModalityType.ARCHIVE,
    # 3D
    ".obj": ModalityType.MODEL_3D, ".gltf": ModalityType.MODEL_3D,
    ".glb": ModalityType.MODEL_3D, ".stl": ModalityType.MODEL_3D,
    ".fbx": ModalityType.MODEL_3D,
}


# ============================================================================
# Input Modalities
# ============================================================================

@dataclass
class ModalityInput:
    """Single input modality."""
    modality_type: ModalityType
    content: bytes | str        # Raw content or URL/path
    mime_type: str = ""
    filename: str = ""
    size_bytes: int = 0
    metadata: dict = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_url(self) -> bool:
        """Check if content is a URL."""
        if isinstance(self.content, str):
            return self.content.startswith(("http://", "https://"))
        return False


@dataclass
class ProcessedModality:
    """Processed modality ready for use."""
    original: ModalityInput
    text_content: str = ""      # Extracted text (if applicable)
    structured_data: dict = field(default_factory=dict)
    embeddings: list[float] = field(default_factory=list)
    processing_time_ms: float = 0
    error: str | None = None


# ============================================================================
# Modality Extractor
# ============================================================================

class ModalityExtractor:
    """
    Extract modalities from user input.
    
    Detects:
    - URLs anywhere in text
    - File uploads
    - Embedded base64 content
    
    Example:
        extractor = ModalityExtractor()
        
        # Extract URLs from text
        modalities = extractor.extract(
            "Check this article: https://example.com and this image: https://img.com/photo.jpg"
        )
        #   [ModalityInput(URL), ModalityInput(URL)]
        
        # With file uploads
        modalities = extractor.extract(
            "Analyze this document",
            files=[uploaded_pdf]
        )
    """
    
    # URL pattern - matches most URLs
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]()\'"]+'
    
    # Base64 pattern
    BASE64_PATTERN = r'data:([a-zA-Z0-9/+-]+);base64,([A-Za-z0-9+/=]+)'
    
    def __init__(self):
        self._url_regex = re.compile(self.URL_PATTERN)
        self._base64_regex = re.compile(self.BASE64_PATTERN)
        logger.debug("ModalityExtractor initialized")
    
    def extract(
        self, 
        text: str, 
        files: list[dict] = None,
    ) -> list[ModalityInput]:
        """
        Extract all modalities from input.
        
        Args:
            text: User's input text
            files: List of file dicts with keys: content, filename, mime_type
            
        Returns:
            List of extracted modalities
        """
        modalities = []
        
        # Extract URLs from text
        urls = self.extract_urls(text)
        for url in urls:
            modality_type = self._detect_url_type(url)
            modalities.append(ModalityInput(
                modality_type=modality_type,
                content=url,
                metadata={"source": "url_in_text"},
            ))
        
        # Extract base64 embedded content
        base64_matches = self._base64_regex.findall(text)
        for mime_type, content in base64_matches:
            import base64
            try:
                decoded = base64.b64decode(content)
                modality_type = MIME_TO_MODALITY.get(mime_type, ModalityType.DATA)
                modalities.append(ModalityInput(
                    modality_type=modality_type,
                    content=decoded,
                    mime_type=mime_type,
                    size_bytes=len(decoded),
                    metadata={"source": "base64_embedded"},
                ))
            except Exception as e:
                logger.warning(f"Failed to decode base64: {e}")
        
        # Process file uploads
        if files:
            for file_info in files:
                modality = self._process_file(file_info)
                if modality:
                    modalities.append(modality)
        
        logger.info(f"Extracted {len(modalities)} modalities from input")
        return modalities
    
    def extract_urls(self, text: str) -> list[str]:
        """Extract all URLs from text."""
        return self._url_regex.findall(text)
    
    def _detect_url_type(self, url: str) -> ModalityType:
        """Detect modality type from URL."""
        url_lower = url.lower()
        
        # Check extension
        for ext, modality in EXT_TO_MODALITY.items():
            if url_lower.endswith(ext):
                return modality
        
        # Default to URL (will be fetched and analyzed)
        return ModalityType.URL
    
    def _process_file(self, file_info: dict) -> ModalityInput | None:
        """Process uploaded file."""
        try:
            content = file_info.get("content", b"")
            filename = file_info.get("filename", "")
            mime_type = file_info.get("mime_type", "")
            
            # Detect type from MIME
            modality_type = MIME_TO_MODALITY.get(mime_type)
            
            # Fallback to extension
            if not modality_type and filename:
                import os
                ext = os.path.splitext(filename)[1].lower()
                modality_type = EXT_TO_MODALITY.get(ext, ModalityType.DATA)
            
            if not modality_type:
                modality_type = ModalityType.DATA
            
            return ModalityInput(
                modality_type=modality_type,
                content=content,
                mime_type=mime_type,
                filename=filename,
                size_bytes=len(content) if isinstance(content, bytes) else 0,
                metadata={"source": "file_upload"},
            )
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return None
    
    def detect_type(self, content: bytes, filename: str = "") -> ModalityType:
        """Detect modality type from content and filename."""
        # Try extension first
        if filename:
            import os
            ext = os.path.splitext(filename)[1].lower()
            if ext in EXT_TO_MODALITY:
                return EXT_TO_MODALITY[ext]
        
        # Magic bytes detection
        magic_bytes = {
            b'\xff\xd8\xff': ModalityType.IMAGE,      # JPEG
            b'\x89PNG': ModalityType.IMAGE,           # PNG
            b'GIF87a': ModalityType.IMAGE,            # GIF
            b'GIF89a': ModalityType.IMAGE,            # GIF
            b'RIFF': ModalityType.AUDIO,              # WAV
            b'ID3': ModalityType.AUDIO,               # MP3
            b'\x00\x00\x00': ModalityType.VIDEO,      # MP4 (partial)
            b'%PDF': ModalityType.DOCUMENT,           # PDF
            b'PK\x03\x04': ModalityType.ARCHIVE,      # ZIP
        }
        
        for magic, modality in magic_bytes.items():
            if content.startswith(magic):
                return modality
        
        return ModalityType.DATA


# ============================================================================
# Modality Processor
# ============================================================================

class ModalityProcessor:
    """
    Process modalities into usable format.
    
    Processing by type:
    - URL   Fetch content, extract text/data
    - Image   Vision model / OCR (placeholder)
    - Audio   Transcription (placeholder)
    - Video   Frame extraction + audio (placeholder)
    - Document   Text extraction
    """
    
    def __init__(self):
        logger.debug("ModalityProcessor initialized")
    
    async def process(self, modality: ModalityInput) -> ProcessedModality:
        """
        Process a modality input.
        
        Args:
            modality: Input to process
            
        Returns:
            ProcessedModality with extracted content
        """
        import time
        start = time.time()
        
        try:
            if modality.modality_type == ModalityType.URL:
                result = await self._process_url(modality)
            elif modality.modality_type == ModalityType.IMAGE:
                result = await self._process_image(modality)
            elif modality.modality_type == ModalityType.DOCUMENT:
                result = await self._process_document(modality)
            elif modality.modality_type == ModalityType.AUDIO:
                result = await self._process_audio(modality)
            elif modality.modality_type == ModalityType.VIDEO:
                result = await self._process_video(modality)
            elif modality.modality_type in [ModalityType.DATA, ModalityType.CODE]:
                result = await self._process_data(modality)
            else:
                result = ProcessedModality(
                    original=modality,
                    error=f"Unsupported modality: {modality.modality_type}",
                )
            
            result.processing_time_ms = (time.time() - start) * 1000
            return result
            
        except Exception as e:
            logger.error(f"Error processing modality: {e}")
            return ProcessedModality(
                original=modality,
                error=str(e),
                processing_time_ms=(time.time() - start) * 1000,
            )
    
    async def _process_url(self, modality: ModalityInput) -> ProcessedModality:
        """Fetch and process URL."""
        url = modality.content
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "")
                content = response.content
                
                # Detect actual type
                if "text/html" in content_type:
                    # Extract text from HTML
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, "html.parser")
                    
                    # Remove script/style
                    for tag in soup(["script", "style"]):
                        tag.decompose()
                    
                    text = soup.get_text(separator="\n", strip=True)
                    
                    return ProcessedModality(
                        original=modality,
                        text_content=text[:10000],  # Limit
                        structured_data={"url": url, "title": soup.title.string if soup.title else ""},
                    )
                
                elif "application/json" in content_type:
                    import json
                    data = json.loads(content)
                    return ProcessedModality(
                        original=modality,
                        text_content=str(data)[:5000],
                        structured_data=data if isinstance(data, dict) else {"data": data},
                    )
                
                else:
                    return ProcessedModality(
                        original=modality,
                        text_content=f"Fetched {len(content)} bytes from {url}",
                        structured_data={"url": url, "content_type": content_type},
                    )
                    
        except Exception as e:
            return ProcessedModality(
                original=modality,
                error=f"Failed to fetch URL: {e}",
            )
    
    async def _process_image(self, modality: ModalityInput) -> ProcessedModality:
        """Process image using Vision Server."""
        try:
            from kernel.interfaces.tool_registry import get_tool_registry
            registry = get_tool_registry()
            
            if not registry:
                raise RuntimeError("ToolRegistry not available")
            
            # Prepare args - prefer base64 for direct processing
            import base64
            if isinstance(modality.content, bytes):
                b64_data = base64.b64encode(modality.content).decode("utf-8")
                args = {"image_base64": b64_data, "extraction_type": "all"}
            else:
                # specific handling if content is path/url string
                args = {"image_url": str(modality.content), "extraction_type": "all"}
                
            tool_res = await registry.execute_tool("screenshot_extract", args)
            
            if tool_res.isError:
                raise RuntimeError(f"Vision tool failed: {tool_res.content}")
                
            text_content = ""
            structured_data = {}
            
            # Parse result
            for content in tool_res.content:
                if content.type == "text":
                    text_content += content.text + "\n"
            
            return ProcessedModality(
                original=modality,
                text_content=text_content.strip(),
                structured_data={"vision_response": text_content, "server": server_name},
            )
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return ProcessedModality(
                original=modality,
                text_content=f"[Image processing failed: {e}]",
                error=str(e)
            )
    
    async def _process_audio(self, modality: ModalityInput) -> ProcessedModality:
        """Process audio - placeholder for transcription."""
        # TODO: Integrate with Whisper or similar
        return ProcessedModality(
            original=modality,
            text_content="[Audio processing - requires transcription model]",
            structured_data={
                "status": "pending_implementation",
                "modality": "audio",
            },
        )
    
    async def _process_video(self, modality: ModalityInput) -> ProcessedModality:
        """Process video - placeholder."""
        # TODO: Frame extraction + audio transcription
        return ProcessedModality(
            original=modality,
            text_content="[Video processing - requires frame extraction + transcription]",
            structured_data={
                "status": "pending_implementation",
                "modality": "video",
            },
        )
    
    async def _process_document(self, modality: ModalityInput) -> ProcessedModality:
        """Process document using Document/Scraper Server."""
        # Discover tools dynamically if registry available
        tools = []
        try:
            from kernel.interfaces.tool_registry import get_tool_registry
            registry = get_tool_registry()
            if registry:
                tools_data = await registry.list_tools()
                tools = [t.get("name") for t in tools_data]
        except Exception:
            pass
        logger.warning(f"Could not load tool registry for dynamic tool discovery.")

        # Try document tools
        # We need a tool that handles file content. 
        # If we don't have direct file upload tool, we might use 'read_file' if it's a path
        
        server_name = "document_server" 
        # Check if we can get a session
        try:
            session = await registry.get_session(server_name)
        except:
            # Fallback to scraper if document server missing
            server_name = "scraper_server"
            session = await registry.get_session(server_name)

            # NOTE: For now, assuming content is a path string or we save it to temp
            path_to_read = ""
            if isinstance(modality.content, str) and os.path.exists(modality.content):
                path_to_read = modality.content
            elif modality.filename:
                # Save temp
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(modality.filename)[1]) as tmp:
                    if isinstance(modality.content, str):
                        tmp.write(modality.content.encode())
                    else:
                        tmp.write(modality.content)
                    path_to_read = tmp.name
            
            if not path_to_read:
                 return ProcessedModality(
                    original=modality,
                    text_content="[Document Content: Memory object (extraction requires file path)]",
                )

            # Call text extraction
            # Assuming 'read_file' or 'parse_document' exists in these servers
            # If strictly following README, scraper has 'pdf_extract'
            
            tool_name = "pdf_extract" if path_to_read.endswith(".pdf") else "read_file"
            
            # Check if tool exists on linked server (optimization)
            # For this patch, we'll try 'pdf_extract' then 'read_file'
            
            try:
                tool_res = await session.call_tool(tool_name, {"file_path": path_to_read})
            except:
                tool_res = await session.call_tool("read_file", {"path": path_to_read})

            if tool_res.isError:
                 raise RuntimeError(f"Document tool failed: {tool_res.content}")
            
            text = ""
            for c in tool_res.content:
                if hasattr(c, 'text'): text += c.text + "\n"
                
            return ProcessedModality(
                original=modality,
                text_content=text.strip()[:50000], # Cap at 50k chars
                structured_data={"server": server_name, "source_path": path_to_read}
            )

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return ProcessedModality(
                original=modality,
                text_content=f"[Document processing failed: {e}]",
                error=str(e)
            )
    
    async def _process_data(self, modality: ModalityInput) -> ProcessedModality:
        """Process data files (CSV, JSON, etc.)."""
        content = modality.content
        
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")
        
        return ProcessedModality(
            original=modality,
            text_content=content[:5000] if isinstance(content, str) else "",
            structured_data={"preview": content[:1000] if isinstance(content, str) else ""},
        )


# ============================================================================
# Output Sockets (Interface for future implementation)
# ============================================================================

@dataclass
class ModalityOutput:
    """Output modality."""
    modality_type: ModalityType
    content: bytes | str
    mime_type: str = ""
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class OutputSocket(Protocol):
    """Protocol for output modality generation."""
    
    async def generate(self, prompt: str, context: dict) -> ModalityOutput:
        """Generate output modality from prompt."""
        ...
    
    async def is_available(self) -> bool:
        """Check if this socket is available."""
        ...


class TextOutputSocket:
    """Text output - always available."""
    
    async def generate(self, prompt: str, context: dict = None) -> ModalityOutput:
        return ModalityOutput(
            modality_type=ModalityType.TEXT,
            content=prompt,
            mime_type="text/plain",
        )
    
    async def is_available(self) -> bool:
        return True


class ImageOutputSocket:
    """Image generation socket - placeholder."""
    
    async def generate(self, prompt: str, context: dict = None) -> ModalityOutput:
        # TODO: Integrate with DALL-E, Stable Diffusion, etc.
        raise NotImplementedError("Image generation not yet implemented")
    
    async def is_available(self) -> bool:
        return False


class AudioOutputSocket:
    """Audio generation socket - placeholder."""
    
    async def generate(self, prompt: str, context: dict = None) -> ModalityOutput:
        # TODO: Integrate with TTS models
        raise NotImplementedError("Audio generation not yet implemented")
    
    async def is_available(self) -> bool:
        return False


class VideoOutputSocket:
    """Video generation socket - placeholder."""
    
    async def generate(self, prompt: str, context: dict = None) -> ModalityOutput:
        # TODO: Integrate with video generation
        raise NotImplementedError("Video generation not yet implemented")
    
    async def is_available(self) -> bool:
        return False


class DocumentOutputSocket:
    """Document generation socket - placeholder."""
    
    async def generate(self, prompt: str, context: dict = None) -> ModalityOutput:
        # TODO: Generate PDF, DOCX from content
        raise NotImplementedError("Document generation not yet implemented")
    
    async def is_available(self) -> bool:
        return False


# ============================================================================
# Output Socket Registry
# ============================================================================

class OutputSocketRegistry:
    """Registry for output sockets."""
    
    def __init__(self):
        self._sockets: dict[ModalityType, OutputSocket] = {
            ModalityType.TEXT: TextOutputSocket(),
            ModalityType.IMAGE: ImageOutputSocket(),
            ModalityType.AUDIO: AudioOutputSocket(),
            ModalityType.VIDEO: VideoOutputSocket(),
            ModalityType.DOCUMENT: DocumentOutputSocket(),
        }
    
    def register(self, modality_type: ModalityType, socket: OutputSocket):
        """Register an output socket."""
        self._sockets[modality_type] = socket
        logger.info(f"Registered output socket for {modality_type.value}")
    
    def get(self, modality_type: ModalityType) -> OutputSocket | None:
        """Get socket for modality type."""
        return self._sockets.get(modality_type)
    
    async def get_available(self) -> list[ModalityType]:
        """Get list of available output modalities."""
        available = []
        for modality_type, socket in self._sockets.items():
            if await socket.is_available():
                available.append(modality_type)
        return available


# ============================================================================
# Singleton instances
# ============================================================================

_extractor: ModalityExtractor | None = None
_processor: ModalityProcessor | None = None
_output_registry: OutputSocketRegistry | None = None


def get_modality_extractor() -> ModalityExtractor:
    """Get singleton extractor."""
    global _extractor
    if _extractor is None:
        _extractor = ModalityExtractor()
    return _extractor


def get_modality_processor() -> ModalityProcessor:
    """Get singleton processor."""
    global _processor
    if _processor is None:
        _processor = ModalityProcessor()
    return _processor


def get_output_registry() -> OutputSocketRegistry:
    """Get singleton output registry."""
    global _output_registry
    if _output_registry is None:
        _output_registry = OutputSocketRegistry()
    return _output_registry
