from extractor.converters.text import to_text


def test_plain_text_utf8() -> None:
    data = "Hello, world!".encode("utf-8")
    assert to_text(data, "text/plain") == "Hello, world!"


def test_plain_text_by_extension() -> None:
    data = "Part: ABC-123".encode("utf-8")
    assert to_text(data, "application/octet-stream", "rfq.txt") == "Part: ABC-123"


def test_html_strips_tags() -> None:
    data = b"<html><body><p>Hello <b>world</b></p></body></html>"
    result = to_text(data, "text/html")
    assert result is not None
    assert "Hello" in result
    assert "<b>" not in result


def test_unknown_type_returns_none() -> None:
    result = to_text(b"binary", "application/octet-stream", "file.bin")
    assert result is None
