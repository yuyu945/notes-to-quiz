from pathlib import Path

import dotenv
from streamlit.testing.v1 import AppTest

import study
from tests.test_study import VALID_QUESTIONS

APP = Path(__file__).resolve().parents[1] / "app.py"


def _upload(app: AppTest, filename: str, content: bytes) -> AppTest:
    return app.file_uploader[0].set_value((filename, content, "text/plain")).run()


def test_initial_page_shows_upload_without_errors():
    app = AppTest.from_file(str(APP)).run()
    assert len(app.exception) == 0
    assert len(app.file_uploader) == 1
    assert "课程笔记学习助手" in app.title[0].value
    assert len(app.button) == 0


def test_invalid_upload_shows_validation_message():
    app = _upload(AppTest.from_file(str(APP)).run(), "bad.txt", b"\xff")
    assert len(app.exception) == 0
    assert any("UTF-8" in item.value for item in app.error)


def test_missing_key_shows_actionable_message(monkeypatch):
    monkeypatch.setattr(dotenv, "load_dotenv", lambda: False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    app = _upload(AppTest.from_file(str(APP)).run(), "notes.md", b"# Topic")
    app.button(key="summarize").click().run()
    assert any("DEEPSEEK_API_KEY" in item.value for item in app.error)


def test_changing_file_clears_old_summary(monkeypatch):
    monkeypatch.setattr(study, "create_model", lambda: object())
    monkeypatch.setattr(study, "summarize", lambda note, model: "First note summary")
    app = _upload(AppTest.from_file(str(APP)).run(), "first.txt", b"First content")
    app.button(key="summarize").click().run()
    assert any("First note summary" in item.value for item in app.markdown)

    app = _upload(app, "second.md", b"Second content")
    assert not any("First note summary" in item.value for item in app.markdown)


def test_quiz_hides_answers_until_submission(monkeypatch):
    monkeypatch.setattr(study, "create_model", lambda: object())
    monkeypatch.setattr(
        study,
        "generate_quiz",
        lambda note, model: study.Quiz.model_validate({"questions": VALID_QUESTIONS}),
    )
    app = _upload(AppTest.from_file(str(APP)).run(), "notes.txt", b"Course notes")
    app.button(key="generate_quiz").click().run()
    assert len(app.radio) == 3
    assert not any("Reason 1" in item.value for item in app.markdown)

    for radio, answer in zip(app.radio, ("A", "B", "D")):
        radio.set_value(answer)
    app.button[2].click().run()
    assert any("2 / 3" in item.value for item in app.markdown)
    assert any("Reason 1" in item.value for item in app.markdown)
