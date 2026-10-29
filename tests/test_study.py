import json

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from study import (
    QUIZ_PROMPT,
    Question,
    Quiz,
    StudyError,
    create_model,
    generate_quiz,
    grade,
    summarize,
)

VALID_QUESTIONS = [
    {
        "stem": f"Question {index}",
        "options": {"A": "alpha", "B": "beta", "C": "gamma", "D": "delta"},
        "answer": answer,
        "explanation": f"Reason {index}",
    }
    for index, answer in enumerate(("A", "C", "D"), start=1)
]


def test_quiz_prompt_preserves_json_example():
    messages = QUIZ_PROMPT.format_messages(note="Course notes")
    assert '{"questions":' in messages[0].content
    assert "Course notes" in messages[1].content


def test_summarize_returns_model_text():
    model = FakeListChatModel(responses=["1. A key concept\n2. Another concept"])
    assert "A key concept" in summarize("Course notes", model)


def test_generate_quiz_parses_three_questions():
    model = FakeListChatModel(responses=[json.dumps({"questions": VALID_QUESTIONS})])
    quiz = generate_quiz("Course notes", model)
    assert len(quiz.questions) == 3
    assert quiz.questions[1].answer == "C"


@pytest.mark.parametrize(
    "payload",
    [
        "not JSON",
        json.dumps({"questions": VALID_QUESTIONS[:2]}),
        json.dumps({"questions": [dict(VALID_QUESTIONS[0], options={"A": "a"})] * 3}),
        json.dumps({"questions": [dict(VALID_QUESTIONS[0], answer="E")] * 3}),
        json.dumps({"questions": [dict(VALID_QUESTIONS[0], stem=" ")] * 3}),
    ],
)
def test_generate_quiz_rejects_malformed_response(payload):
    model = FakeListChatModel(responses=[payload])
    with pytest.raises(StudyError, match="格式"):
        generate_quiz("Course notes", model)


def test_grade_compares_answers_without_model_call():
    quiz = Quiz(questions=[Question.model_validate(item) for item in VALID_QUESTIONS])
    assert grade(quiz, ["A", "B", "D"]) == [True, False, True]


def test_grade_requires_one_answer_per_question():
    quiz = Quiz(questions=[Question.model_validate(item) for item in VALID_QUESTIONS])
    with pytest.raises(ValueError, match="三"):
        grade(quiz, ["A"])


def test_create_model_requires_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(StudyError, match="DEEPSEEK_API_KEY"):
        create_model()
