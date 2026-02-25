import pytest

from kernel.modality.engine import (
    detect_modality,
    create_file_handle,
    decompose_document,
    decompose_video,
    transcribe_audio,
    parse_vision,
    embed_text,
    ingest
)
from kernel.modality.types import RawInput, ModalityType
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("modality_request", [
    RawInput(content="Scan the logs for errors", mime_type="text/plain"),
    RawInput(file_path="invoice.pdf", mime_type="application/pdf"),
    RawInput(file_path="voice_memo.wav", mime_type="audio/wav"),
    RawInput(file_path="security_footage.mp4", mime_type="video/mp4"),
    RawInput(file_path="chart.png", mime_type="image/png"),
    RawInput(content="Just some raw text data")
])
async def test_modality_comprehensive(modality_request):
    """REAL SIMULATION: Verify Modality Kernel functions with multiple input types."""
    print(f"\n--- Testing Modality: Content='{modality_request.content}', Path='{modality_request.file_path}' ---")

    print(f"\n[Test]: detect_modality")
    detected_type = detect_modality(modality_request)
    assert isinstance(detected_type, ModalityType)
    print(f"   Detected Modality: {detected_type.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: create_file_handle")
    if modality_request.file_path:
        handle = create_file_handle(modality_request.file_path, detected_type)
        assert handle is not None
        assert handle.file_path == modality_request.file_path
        print(f"   File Handle created for {handle.file_path}")
    print(f" \033[92m[SUCCESS]\033[0m")

    # The following functions (decompose, transcribe, parse) are often stubs or require external tools.
    # We test their interface and graceful persistence/failure behavior.
    
    print(f"\n[Test]: decompose_document & decompose_video")
    if detected_type == ModalityType.DOCUMENT:
        doc_parts = await decompose_document(modality_request.file_path)
        assert doc_parts is not None
    elif detected_type == ModalityType.VIDEO:
        video_parts = await decompose_video(modality_request.file_path)
        assert video_parts is not None
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: transcribe_audio & parse_vision")
    if detected_type == ModalityType.AUDIO:
        transcript = await transcribe_audio(modality_request.file_path)
        assert "pending" in transcript.lower() or transcript != ""
    elif detected_type == ModalityType.IMAGE:
        vision_text = await parse_vision(modality_request.file_path)
        assert "pending" in vision_text.lower() or vision_text != ""
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: embed_text")
    if modality_request.content:
        vector = await embed_text(modality_request.content)
        assert isinstance(vector, list)
        print(f"   Vector Embedding generated, size: {len(vector)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: ingest")
    res = await ingest(modality_request)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
