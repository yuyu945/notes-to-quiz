# 课程笔记学习助手

一个基于 **LangChain + DeepSeek API + Streamlit** 的小型学习应用。上传课程笔记后，
可以提炼知识点、生成三道单选练习题，并在本地提交答案、查看成绩和解析。

## 功能

- 上传一份 UTF-8 编码的 `.txt` 或 `.md` 笔记，最多 256 KiB、20,000 字符。
- 按需生成知识点列表和三道单选题；不会在上传时自动发起 API 请求。
- 答题结果在本地计算。更换笔记时清除旧的知识点、题目和成绩。
- 文件只在当前会话内处理，不写入数据库或磁盘。

## 前置条件

- Python 3.10 或更新版本，推荐使用 [uv](https://docs.astral.sh/uv/) 管理环境。
- 可访问 DeepSeek API 的网络，以及你自己的 DeepSeek API Key。
- 使用在线 API 可能产生费用；请以服务商账户和计费页面为准。

## 在 Windows PowerShell 中运行

首次获取代码时克隆仓库；已有代码目录可跳过 `git clone`：

```powershell
git clone https://github.com/yuyu945/notes-to-quiz.git "D:\langchainApp"
cd "D:\langchainApp"
uv sync --python 3.10
Copy-Item .env.example .env
```

在本机打开 `.env`，把 `DEEPSEEK_API_KEY` 的示例值替换成你自己的 Key。
`DEEPSEEK_MODEL` 默认为 `deepseek-chat`，如果服务商更新型号，可在 `.env` 修改。
**不要将真实 Key 复制到 README、提交记录、截图或聊天消息。** `.env` 已被 Git 忽略。

```powershell
uv run streamlit run app.py
```

在终端显示的本地地址打开页面，通常是 `http://localhost:8501`。
可先上传 [`examples/formal-methods.md`](examples/formal-methods.md)，
点击“提炼知识点”和“生成练习题”，选完三题后点击“提交答案”。

不使用 uv 时，可创建 Python 虚拟环境并安装 `pyproject.toml` 中的依赖。

## 验证

```powershell
uv run pytest -q
uv run ruff check .
```

自动化测试使用假模型，不发送网络请求、也不需要真实 Key。
完整的在线调用需要你在本机设置 Key，按上述演示流程实际运行一次。
API 鉴权失败、限流、网络故障或模型输出格式错误时，页面会显示简短提示。

## 隐私和限制

点击提炼或出题时，当前笔记内容会发送给 DeepSeek API；不要上传含个人隐私、
商业机密或其他敏感信息的笔记。应用不持久化上传文件，但浏览器会话中暂存
当前生成结果。生成结果可能不准确，应自行核对课程资料。
当前只支持单文件 `.txt`/`.md`，不支持 PDF、长文检索或账号系统。

## 开源仓库

[GitHub: yuyu945/notes-to-quiz](https://github.com/yuyu945/notes-to-quiz)
