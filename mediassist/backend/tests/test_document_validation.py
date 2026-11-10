from app.routers.documents import detect_content_type


def test_detect_pdf_by_signature():
    assert detect_content_type(b"%PDF-1.7 sample") == "application/pdf"


def test_detect_png_by_signature():
    assert detect_content_type(b"\x89PNG\r\n\x1a\nrest") == "image/png"


def test_detect_jpeg_by_signature():
    assert detect_content_type(b"\xff\xd8\xffrest") == "image/jpeg"


def test_reject_unknown_or_extension_only_file():
    assert detect_content_type(b"not really a pdf") is None
