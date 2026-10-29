# Study Notes Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small Streamlit app that summarizes an uploaded note and generates a three-question quiz using LangChain and DeepSeek.

**Architecture:** File validation is pure and separate from model calls. LangChain prompts produce a summary and a JSON quiz; the app validates quiz data and grades answers locally in Streamlit session state.

**Tech Stack:** Python 3.10+, Streamlit, langchain-core, langchain-deepseek, pydantic, python-dotenv, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-10-29-study-notes-assistant-design.md`

## Global Constraints

- Only UTF-8 `.txt` and `.md`, one file at a time; reject empty or overlong text.
- Exactly three single-choice questions with four options, one answer and one explanation each.
- No account, database, PDF, RAG, or conversation history.
- Only user-triggered generation sends notes to DeepSeek. No note or model raw response is written to disk.
- Read `DEEPSEEK_API_KEY` from environment or ignored `.env`; never commit a real key.
- Never invent a public repository URL; add it to README only after publishing.

---

### Task 1: File validation and project setup

**Files:**
- Create: `notes.py`, `tests/test_notes.py`, `pyproject.toml`, `.gitignore`, `.env.example`

**Interfaces:**
- Produces: `parse_note(filename: str, data: bytes) -> str`, raising `NoteError` with a user-safe message.
- Limit: at most 20,000 Unicode characters and 256 KiB file bytes.

- [x] **Step 1: Write failing tests** for accepted UTF-8 text and Markdown, invalid extension, invalid UTF-8, blank input, byte limit and character limit.

```python
from notes import NoteError, parse_note


def test_markdown_note():
    assert parse_note("lecture.md", "# Intro\n".encode()) == "# Intro"


def test_invalid_encoding():
    with pytest.raises(NoteError, match="UTF-8"):
        parse_note("lecture.txt", b"\xff")
```

- [x] **Step 2: Run** `uv run --python 3.10 pytest tests/test_notes.py -q`; expect import failure.
- [x] **Step 3: Implement** a pure validator. Check suffix with `Path(filename).suffix.lower()`, byte length, `data.decode("utf-8-sig")`, `strip()`, then character length; raise `NoteError` for each failure. Configure dependencies, tests, lint and ignored `.venv`, `.env`, caches.
- [x] **Step 4: Run** `uv run --python 3.10 pytest tests/test_notes.py -q` and `uv run --python 3.10 ruff check .`; expect pass.
- [x] **Step 5: Review diff and commit** `feat: validate uploaded study notes`.

### Task 2: Model flow and grading

**Files:**
- Create: `study.py`, `tests/test_study.py`

**Interfaces:**
- Consumes: a validated note string from `parse_note`.
- Produces: `summarize(note: str, model: BaseChatModel) -> str`,
  `generate_quiz(note: str, model: BaseChatModel) -> Quiz`,
  `grade(quiz: Quiz, answers: list[str]) -> list[bool]`,
  `create_model() -> BaseChatModel`.
- `Quiz` contains exactly three `Question` values; each `Question` has `stem: str`,
  `options: dict[str, str]` with A-D, `answer: str` in A-D and `explanation: str`.

- [x] **Step 1: Write failing tests** using a fake chat model for summary and valid JSON quiz. Add bad JSON, wrong question count, duplicate/missing options, invalid correct answer, missing Key and grading cases.

```python
def test_grade_counts_exact_matches():
    quiz = Quiz(questions=[question("A"), question("C"), question("D")])
    assert grade(quiz, ["A", "B", "D"]) == [True, False, True]
```

- [x] **Step 2: Run** `uv run --python 3.10 pytest tests/test_study.py -q`; expect import failure.
- [x] **Step 3: Implement** prompt templates and `StrOutputParser`, JSON parsing with Pydantic validation, and a single `ChatDeepSeek` constructor reading `DEEPSEEK_API_KEY` and configurable `DEEPSEEK_MODEL`. Catch format problems as `StudyError` without exposing raw model output; keep provider errors classified for the UI.
- [x] **Step 4: Run** targeted tests, all tests, and Ruff; expect pass.
- [x] **Step 5: Review diff and commit** `feat: generate and grade study exercises`.

### Task 3: Streamlit workflow and delivery

**Files:**
- Create: `app.py`, `tests/test_app.py`, `README.md`, `examples/formal-methods.md`

**Interfaces:**
- Consumes: `parse_note`, `create_model`, `summarize`, `generate_quiz`, `grade`.
- A file identity consists of its name and SHA-256 of its bytes; when identity changes,
  clear summary, quiz, answers and result. Session state stores only current in-memory data.

- [x] **Step 1: Write failing AppTest and state tests** for missing Key guidance, no upload, invalid file and cleared results after changing file; use stubs for model requests so tests do not spend API credits.
- [x] **Step 2: Run** `uv run --python 3.10 pytest tests/test_app.py -q`; expect failure.
- [x] **Step 3: Implement** a compact Streamlit page with upload preview, summary and quiz commands, answer radio inputs and submit button. Keep answers hidden before submission; show actionable validation, auth, rate-limit, network and response-format errors.
- [x] **Step 4: Write README** with Windows PowerShell setup using `uv`, `.env.example` copy, model configuration, `uv run streamlit run app.py`, screenshots or demonstration steps, privacy/cost note, tests, and a repository link only if one has actually been created. Include a small sample note.
- [x] **Step 5: Run** all tests, Ruff and `git diff --check`; start Streamlit and inspect desktop UI. A real Key exists, and summary, quiz and grading ran with DeepSeek. Mobile-specific visual QA was not available in this browser surface.
- [x] **Step 6: Review diff and commit** `feat: add study assistant UI and documentation`. Do not push without explicit request.
