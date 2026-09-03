import json
from html import escape
from pathlib import Path

import streamlit as st

from src.pipeline import Pipeline, max_config


root_path = Path("data/stock_data")
pipeline = Pipeline(root_path, run_config=max_config)

st.set_page_config(page_title="RAGForge", page_icon="🔎", layout="wide")

st.markdown(
    """
<style>
    :root {
        --text: #20242e;
        --sidebar: #f0f2f6;
        --blue-bg: #e8f2fc;
        --blue-text: #07599a;
        --green-bg: #e8f8ee;
        --green-text: #16723c;
        --answer-bg: #f6f7f9;
    }

    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"], #MainMenu, footer { visibility: hidden; }
    [data-testid="stSidebar"] {
        background: var(--sidebar);
        min-width: 340px;
        max-width: 340px;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 5.8rem 1.25rem 2rem;
    }
    [data-testid="stSidebar"] h2 {
        color: var(--text);
        font-size: 1.45rem;
        margin-bottom: 1.35rem;
    }
    [data-testid="stSidebar"] label p {
        color: #313640;
        font-size: 1rem;
    }
    [data-testid="stTextArea"] textarea {
        min-height: 110px;
        border: 0;
        border-radius: 10px;
        background: white;
        color: #30343d;
        font-size: 1rem;
        line-height: 1.55;
        padding: .75rem .9rem;
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton button {
        height: 46px;
        border: 1px solid #c7cbd1;
        border-radius: 9px;
        background: #fbfbfc;
        color: #252a33;
        font-size: 1rem;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        border-color: #8d949e;
        color: #111827;
    }
    .block-container {
        max-width: 1500px;
        padding: 4.1rem 4.6rem 4rem;
    }
    .result-title {
        color: var(--text);
        font-size: 2rem;
        font-weight: 750;
        line-height: 1.2;
        margin: 0 0 1.5rem;
    }
    .link-icon {
        color: #8e949d;
        font-size: 1.05rem;
        margin-left: .35rem;
        vertical-align: middle;
    }
    .result-label {
        color: var(--text);
        font-size: 1.08rem;
        font-weight: 700;
        margin: 1.2rem 0 .75rem;
    }
    .result-card {
        border-radius: 10px;
        font-size: 1.05rem;
        line-height: 1.72;
        padding: 1.15rem 1.35rem;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .reasoning-card { background: var(--blue-bg); color: var(--blue-text); }
    .summary-card { background: var(--green-bg); color: var(--green-text); }
    .answer-card { background: var(--answer-bg); color: #242933; }
    .pages-card {
        color: #28313d;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 1rem;
        padding: .2rem 0 .4rem;
    }
    .empty-state { color: #68707c; font-size: 1rem; padding: .25rem 0; }

    @media (max-width: 900px) {
        .block-container { padding: 3.5rem 1.3rem 2rem; }
        [data-testid="stSidebar"] { min-width: 290px; max-width: 290px; }
    }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("查询设置")
    user_question = st.text_area(
        "输入问题",
        "中芯国际在晶圆制造行业中的地位如何？其服务范围和全球布局是怎样的？",
        height=110,
    )
    submit_btn = st.button("生成答案", use_container_width=True)

st.markdown(
    '<h1 class="result-title">检索结果<span class="link-icon">🔗</span></h1>',
    unsafe_allow_html=True,
)


def normalize_answer(answer):
    """兼容字典、JSON 字符串和 DashScope 的嵌套返回结构。"""
    if isinstance(answer, str):
        answer = json.loads(answer)
    if not isinstance(answer, dict):
        raise ValueError("返回内容不是有效的结构化答案")

    content = answer.get("content", answer)
    if isinstance(content, str):
        content = json.loads(content)

    if isinstance(content, dict):
        nested = content.get("final_answer")
        if isinstance(nested, str) and nested.lstrip().startswith("{"):
            try:
                parsed = json.loads(nested)
                if isinstance(parsed, dict):
                    content = parsed
            except json.JSONDecodeError:
                pass

    if not isinstance(content, dict):
        raise ValueError("无法解析模型返回的 content 字段")
    return content


def render_card(label, value, card_class):
    safe_value = escape(str(value if value not in (None, "") else "-"))
    st.markdown(f'<div class="result-label">{label}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="result-card {card_class}">{safe_value}</div>',
        unsafe_allow_html=True,
    )


if submit_btn and user_question.strip():
    with st.spinner("正在生成答案，请稍候..."):
        try:
            answer = pipeline.answer_single_question(user_question, kind="string")
            content = normalize_answer(answer)

            render_card(
                "分步推理：",
                content.get("step_by_step_analysis", "-"),
                "reasoning-card",
            )
            render_card(
                "推理摘要：",
                content.get("reasoning_summary", "-"),
                "summary-card",
            )
            relevant_pages = content.get("relevant_pages", [])
            st.markdown(
                '<div class="result-label">相关页面：</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="pages-card">{escape(json.dumps(relevant_pages, ensure_ascii=False))}</div>',
                unsafe_allow_html=True,
            )
            render_card(
                "最终答案：",
                content.get("final_answer", "-"),
                "answer-card",
            )
        except Exception as exc:
            st.error(f"生成答案时出错：{exc}")
else:
    st.markdown(
        '<div class="empty-state">请在左侧输入问题并点击“生成答案”。</div>',
        unsafe_allow_html=True,
    )
