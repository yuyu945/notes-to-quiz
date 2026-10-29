import json
import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator


class StudyError(ValueError):
    pass


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stem: str
    options: dict[str, str]
    answer: str
    explanation: str

    @field_validator("stem", "explanation")
    @classmethod
    def nonempty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question text cannot be empty.")
        return value.strip()

    @model_validator(mode="after")
    def valid_choices(self) -> "Question":
        if set(self.options) != {"A", "B", "C", "D"}:
            raise ValueError("Each question needs options A-D.")
        if any(not option.strip() for option in self.options.values()):
            raise ValueError("Options cannot be empty.")
        if self.answer not in self.options:
            raise ValueError("The answer must be one of A-D.")
        return self


class Quiz(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[Question]

    @field_validator("questions")
    @classmethod
    def exactly_three(cls, questions: list[Question]) -> list[Question]:
        if len(questions) != 3:
            raise ValueError("The quiz must have three questions.")
        return questions


SUMMARY_SYSTEM = (
    "You are a study assistant. Extract 3-5 key points from the uploaded notes. "
    "Write concise Chinese numbered points. Use only information supported by the notes; "
    "if the notes are incomplete, say so."
)
QUIZ_SYSTEM = (
    "Based only on the notes, create exactly 3 distinct Chinese multiple-choice questions. "
    "Return only a JSON object, with no Markdown fence or other text. "
    'Schema: {"questions":[{"stem":"question","options":{"A":"text","B":"text",'
    '"C":"text","D":"text"},"answer":"A","explanation":"reason"}]}. '
    "Each question must have four nonempty choices, exactly one correct answer and a "
    "short explanation grounded in the notes. Do not refer to facts missing from the notes."
)
SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [SystemMessage(content=SUMMARY_SYSTEM), ("human", "笔记内容：\n{note}")]
)
QUIZ_PROMPT = ChatPromptTemplate.from_messages(
    [SystemMessage(content=QUIZ_SYSTEM), ("human", "笔记内容：\n{note}")]
)


def create_model() -> BaseChatModel:
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not key or key == "replace-with-your-own-key":
        raise StudyError("Set DEEPSEEK_API_KEY in your local .env file first.")
    return ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=key,
        timeout=45,
        max_retries=1,
    )


def _invoke(prompt: ChatPromptTemplate, note: str, model: BaseChatModel) -> str:
    try:
        return (prompt | model | StrOutputParser()).invoke({"note": note}).strip()
    except (AuthenticationError, PermissionDeniedError) as exc:
        raise StudyError("API authentication failed. Check your DeepSeek API Key.") from exc
    except RateLimitError as exc:
        raise StudyError("DeepSeek is rate-limiting requests. Try again later.") from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise StudyError("Cannot reach DeepSeek. Check your network and try again.") from exc
    except Exception as exc:
        raise StudyError("The model request failed. Check the model name and try again.") from exc


def summarize(note: str, model: BaseChatModel) -> str:
    result = _invoke(SUMMARY_PROMPT, note, model)
    if not result:
        raise StudyError("The model returned an empty summary. Try again.")
    return result


def generate_quiz(note: str, model: BaseChatModel) -> Quiz:
    result = _invoke(QUIZ_PROMPT, note, model)
    try:
        return Quiz.model_validate(json.loads(result))
    except (ValueError, ValidationError) as exc:
        raise StudyError("The quiz format was invalid. Generate the quiz again.") from exc


def grade(quiz: Quiz, answers: list[str]) -> list[bool]:
    if len(answers) != 3 or any(answer not in {"A", "B", "C", "D"} for answer in answers):
        raise ValueError("Answer all three questions with A, B, C or D.")
    return [answer == question.answer for answer, question in zip(answers, quiz.questions)]
