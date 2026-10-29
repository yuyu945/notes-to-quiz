from pathlib import Path

MAX_BYTES = 256 * 1024
MAX_CHARS = 20_000
ALLOWED_SUFFIXES = {".txt", ".md"}


class NoteError(ValueError):
    pass


def parse_note(filename: str, data: bytes) -> str:
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise NoteError("仅支持 .txt 或 .md 文件。")
    if len(data) > MAX_BYTES:
        raise NoteError("文件不能超过 256 KiB。")
    try:
        text = data.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise NoteError("请将笔记保存为 UTF-8 编码后重新上传。") from exc
    if not text:
        raise NoteError("笔记内容为空。")
    if len(text) > MAX_CHARS:
        raise NoteError("笔记不能超过 20,000 字符。")
    return text
