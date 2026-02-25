from kernel.modality.engine import create_file_handle, detect_modality
from kernel.modality.types import ModalityType, RawInput


def test_detect_modality(monkeypatch):
    class MockSettings:
        modality_supported_extensions = {".txt": "text", ".jpg": "image"}
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.modality.engine.get_settings", lambda: MockKernelSettings())

    inp = RawInput(file_path="test.jpg")
    mod = detect_modality(inp)
    assert mod == ModalityType.IMAGE

    inp2 = RawInput(mime_type="audio/mpeg")
    assert detect_modality(inp2) == ModalityType.AUDIO

def test_create_file_handle():
    fh = create_file_handle("/tmp/test.txt", ModalityType.TEXT)
    assert fh.modality == ModalityType.TEXT
    assert fh.file_path == "/tmp/test.txt"
