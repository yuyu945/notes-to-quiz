import hashlib

import streamlit as st
from dotenv import load_dotenv

import study
from notes import NoteError, parse_note

load_dotenv()
st.set_page_config(
    page_title="课程笔记学习助手", page_icon=":material/menu_book:", layout="centered"
)


def reset_for_file(file_id: tuple[str, str] | None) -> None:
    if st.session_state.get("file_id") == file_id:
        return
    st.session_state["file_id"] = file_id
    for key in ("summary", "quiz", "result"):
        st.session_state.pop(key, None)
    for index in range(3):
        st.session_state.pop(f"answer_{index}", None)


st.title("课程笔记学习助手")
uploaded = st.file_uploader(
    "上传课程笔记",
    type=["txt", "md"],
    key="note_upload",
    help="笔记最多 256 KiB、20,000 字符，使用 UTF-8 编码。",
)

if uploaded is None:
    reset_for_file(None)
    st.stop()

data = uploaded.getvalue()
file_id = (uploaded.name, hashlib.sha256(data).hexdigest())
reset_for_file(file_id)

try:
    note = parse_note(uploaded.name, data)
except NoteError as exc:
    st.error(str(exc))
    st.stop()

st.caption(f"{uploaded.name}  |  {len(note):,} 字")
st.text_area("笔记预览", note[:800], height=150, disabled=True)

summary_column, quiz_column = st.columns(2)
with summary_column:
    summarize_clicked = st.button(
        "提炼知识点", key="summarize", icon=":material/notes:", use_container_width=True
    )
with quiz_column:
    quiz_clicked = st.button(
        "生成练习题", key="generate_quiz", icon=":material/quiz:", use_container_width=True
    )

if summarize_clicked:
    try:
        model = study.create_model()
        with st.spinner("正在提炼知识点"):
            st.session_state["summary"] = study.summarize(note, model)
    except study.StudyError as exc:
        st.error(str(exc))

if quiz_clicked:
    try:
        model = study.create_model()
        with st.spinner("正在生成练习题"):
            quiz = study.generate_quiz(note, model)
        st.session_state["quiz"] = quiz
        st.session_state.pop("result", None)
        for index in range(3):
            st.session_state.pop(f"answer_{index}", None)
    except study.StudyError as exc:
        st.error(str(exc))

if summary := st.session_state.get("summary"):
    st.subheader("知识点")
    st.markdown(summary)

if quiz := st.session_state.get("quiz"):
    st.subheader("练习题")
    with st.form("quiz_form"):
        answers = []
        for index, question in enumerate(quiz.questions):
            st.markdown(f"**{index + 1}. {question.stem}**")
            answer = st.radio(
                "选择答案",
                ["A", "B", "C", "D"],
                index=None,
                format_func=lambda choice, options=question.options: f"{choice}. {options[choice]}",
                key=f"answer_{index}",
            )
            answers.append(answer)
        submitted = st.form_submit_button("提交答案", icon=":material/check_circle:")

    if submitted:
        if any(answer is None for answer in answers):
            st.warning("请先完成全部三道题。")
        else:
            st.session_state["result"] = study.grade(quiz, answers)

    if result := st.session_state.get("result"):
        st.markdown(f"### 得分：{sum(result)} / 3")
        for index, (question, correct) in enumerate(zip(quiz.questions, result), start=1):
            verdict = "正确" if correct else "错误"
            st.markdown(
                f"**第 {index} 题：{verdict}**  "
                f"正确答案：{question.answer}. {question.options[question.answer]}\n\n"
                f"{question.explanation}"
            )
