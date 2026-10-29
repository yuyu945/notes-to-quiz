from pathlib import Path

MAX_BYTES = 256 * 1024
MAX_CHARS = 20_000
ALLOWED_SUFFIXES = {".txt", ".md"}


class NoteError(ValueError):
    pass


def parse_note(filename: str, data: bytes) -> str:
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise NoteError("Upload a .txt or .md file.")
    if len(data) > MAX_BYTES:
        raise NoteError("The file must be at most 256 KiB.")
    try:
        text = data.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise NoteError("Save the note as UTF-8 and upload it again.") from exc
    if not text:
        raise NoteError("The note is empty.")
    if len(text) > MAX_CHARS:
        raise NoteError("The note must be at most 20,000 characters.")
    return text
