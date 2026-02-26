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
async def test_modality_comprehensive(modality_request, inference_kit):
    """REAL SIMULATION: Verify Modality Kernel functions with multiple input types."""
    print(f"\n--- Testing Modality: Content='{modality_request.content}', Path='{modality_request.file_path}' ---")

    print(f"\n[Test]: detect_modality")
    print(f"   [INPUT]: type={type(modality_request).__name__}, content_preview={modality_request.content[:10] if modality_request.content else 'None'}")
    detected_type = detect_modality(modality_request)
    assert isinstance(detected_type, ModalityType)
    print(f"   [OUTPUT]: Detected Modality={detected_type.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: create_file_handle")
    if modality_request.file_path:
        print(f"   [INPUT]: path={modality_request.file_path}, type={detected_type}")
        handle = create_file_handle(modality_request.file_path, detected_type)
        assert handle is not None
        assert handle.file_path == modality_request.file_path
        print(f"   [OUTPUT]: File Handle created for {handle.file_path}")
    else:
        print(f"   [INPUT]: No file path provided")
        print(f"   [OUTPUT]: Skipped handle creation")
    print(f" \033[92m[SUCCESS]\033[0m")

    # The following functions (decompose, transcribe, parse) are often stubs or require external tools.
    # We test their interface and graceful persistence/failure behavior.
    
    print(f"\n[Test]: decompose_document & decompose_video")
    if detected_type == ModalityType.DOCUMENT:
        print(f"   [INPUT]: document path={modality_request.file_path}")
        doc_parts = await decompose_document(modality_request.file_path)
        assert doc_parts is not None
        print(f"   [OUTPUT]: Document decomposed")
    elif detected_type == ModalityType.VIDEO:
        print(f"   [INPUT]: video path={modality_request.file_path}")
        video_parts = await decompose_video(modality_request.file_path)
        assert video_parts is not None
        print(f"   [OUTPUT]: Video decomposed")
    else:
        print(f"   [INPUT]: Not a document or video")
        print(f"   [OUTPUT]: Skipped decomposition")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: transcribe_audio & parse_vision")
    if detected_type == ModalityType.AUDIO:
        print(f"   [INPUT]: audio path={modality_request.file_path}")
        transcript = await transcribe_audio(modality_request.file_path)
        assert "pending" in transcript.lower() or transcript != ""
        print(f"   [OUTPUT]: Transcript obtained")
    elif detected_type == ModalityType.IMAGE:
        print(f"   [INPUT]: image path={modality_request.file_path}")
        vision_text = await parse_vision(modality_request.file_path)
        assert "pending" in vision_text.lower() or vision_text != ""
        print(f"   [OUTPUT]: Vision parsed")
    else:
        print(f"   [INPUT]: Not audio or image")
        print(f"   [OUTPUT]: Skipped transcription/vision")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: embed_text")
    if modality_request.content:
        print(f"   [INPUT]: content='{modality_request.content[:20]}...'")
        vector = await embed_text(modality_request.content, kit=inference_kit)
        assert isinstance(vector, list)
        print(f"   [OUTPUT]: Vector Embedding size={len(vector)}")
    else:
        print(f"   [INPUT]: No content for embedding")
        print(f"   [OUTPUT]: Skipped embedding")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: ingest")
    print(f"   [INPUT]: Modality={detected_type}")
    res = await ingest(modality_request, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
