import pytest

from notes import NoteError, parse_note


@pytest.mark.parametrize("name", ["lecture.txt", "lecture.md", "LECTURE.MD"])
def test_accepts_text_and_markdown(name):
    assert parse_note(name, b"\xef\xbb\xbf# Intro\n") == "# Intro"


def test_rejects_other_extensions():
    with pytest.raises(NoteError, match="仅支持"):
        parse_note("lecture.pdf", b"content")


def test_rejects_invalid_utf8():
    with pytest.raises(NoteError, match="UTF-8"):
        parse_note("lecture.txt", b"\xff")


def test_rejects_blank_note():
    with pytest.raises(NoteError, match="空"):
        parse_note("lecture.md", b" \n\t ")


def test_rejects_large_file():
    with pytest.raises(NoteError, match="256 KiB"):
        parse_note("lecture.txt", b"a" * (256 * 1024 + 1))


def test_rejects_overlong_note():
    with pytest.raises(NoteError, match="20,000"):
        parse_note("lecture.md", b"a" * 20_001)


def test_accepts_exact_character_limit():
    assert len(parse_note("lecture.txt", b"a" * 20_000)) == 20_000
