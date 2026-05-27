from __future__ import annotations

from collections import Counter
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from src.bad_case_analyzer import add_bad_case_columns
from src.classifier import add_classification_columns
from src.cleaner import clean_feedback_dataframe, clean_text
from src.priority_scorer import add_priority_columns
from src.report_generator import generate_markdown_report
from src.utils import (
    REQUIRED_COLUMNS,
    dataframe_to_csv_bytes,
    has_openai_api_key,
    load_input_file,
    prepare_input_dataframe,
    split_pipe_labels,
    top_items,
)

NAV_OPTIONS = ["Overview", "Cleaning", "Classification", "Bad Cases", "Priority", "Report"]

OWNER_ACTION_SUGGESTIONS = {
    "HR Team": "Update FAQ, improve SOP, and clarify policy boundaries.",
    "IT Team": "Add system entry instructions and clarify portal, path, or link guidance.",
    "Product Team": "Improve prompt structure, answer templates, and AI behavior rules.",
    "Operations Team": "Improve SOP, confirm process ownership, and tighten execution steps.",
    "Data Team": "Check the data pipeline, investigate mismatches, and fix dashboard data issues.",
    "Human Support": "Add escalation rules and define the manual review boundary more clearly.",
}


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #f4f7fb;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .top-nav-marker {
            display: none;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }
        .brand-card,
        .status-card,
        .metric-card,
        .info-panel,
        .highlight-panel,
        .owner-card,
        .report-shell,
        .section-card {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
            overflow-wrap: anywhere;
            word-break: break-word;
            white-space: normal;
            max-width: 100%;
        }
        .brand-card {
            background: linear-gradient(180deg, #eaf1ff 0%, #f8fbff 100%);
            padding: 18px 18px 16px 18px;
            margin-bottom: 12px;
        }
        .brand-title {
            color: #0f172a;
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 6px;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }
        .brand-subtitle {
            color: #475569;
            font-size: 0.86rem;
            line-height: 1.55;
            margin-bottom: 12px;
            overflow-wrap: anywhere;
        }
        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .badge-chip,
        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.76rem;
            font-weight: 700;
            line-height: 1.2;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .badge-chip {
            background: rgba(37, 99, 235, 0.1);
            color: #1d4ed8;
            border: 1px solid rgba(37, 99, 235, 0.12);
        }
        .status-chip {
            background: #f8fafc;
            color: #0f172a;
            border: 1px solid rgba(148, 163, 184, 0.2);
            width: fit-content;
            max-width: 100%;
        }
        .status-card {
            padding: 14px 16px;
            min-height: 84px;
        }
        .status-label {
            color: #64748b;
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }
        .status-value {
            color: #0f172a;
            font-size: 0.94rem;
            line-height: 1.45;
            font-weight: 700;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .page-title {
            color: #0f172a;
            font-size: 1.42rem;
            font-weight: 800;
            margin-bottom: 4px;
            margin-top: 0;
            line-height: 1.24;
            letter-spacing: -0.01em;
            overflow-wrap: anywhere;
        }
        .page-caption {
            color: #475569;
            font-size: 0.95rem;
            line-height: 1.58;
            margin-bottom: 2px;
            overflow-wrap: anywhere;
        }
        .page-question {
            color: #1d4ed8;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 16px;
            overflow-wrap: anywhere;
        }
        .metric-card {
            padding: 17px 16px;
            min-height: 146px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.055);
        }
        .metric-topline {
            color: #2563eb;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .metric-value {
            color: #0f172a;
            font-size: 1.9rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 8px;
        }
        .metric-caption {
            color: #64748b;
            font-size: 0.84rem;
            line-height: 1.48;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .info-panel {
            padding: 16px;
            margin: 10px 0 18px 0;
        }
        .info-title {
            color: #0f172a;
            font-size: 0.9rem;
            font-weight: 800;
            margin-bottom: 5px;
        }
        .info-body {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.58;
            overflow-wrap: anywhere;
        }
        .highlight-panel {
            padding: 18px;
            min-height: 378px;
            background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
        }
        .highlight-kicker {
            color: #2563eb;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
        }
        .highlight-panel p {
            margin-bottom: 12px;
            color: #0f172a;
            line-height: 1.55;
            overflow-wrap: anywhere;
        }
        .owner-card {
            padding: 14px 16px;
            min-height: 120px;
        }
        .action-board-card {
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
            padding: 16px;
            min-height: 210px;
            overflow-wrap: anywhere;
        }
        .action-board-owner {
            color: #0f172a;
            font-size: 0.98rem;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .action-board-count {
            color: #2563eb;
            font-size: 1.7rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 10px;
        }
        .action-board-meta {
            color: #475569;
            font-size: 0.84rem;
            line-height: 1.55;
            margin-bottom: 10px;
        }
        .action-board-meta strong {
            color: #0f172a;
        }
        .action-board-note {
            color: #334155;
            font-size: 0.84rem;
            line-height: 1.58;
        }
        .owner-title {
            color: #0f172a;
            font-size: 0.92rem;
            font-weight: 800;
            margin-bottom: 6px;
        }
        .owner-body {
            color: #64748b;
            font-size: 0.84rem;
            line-height: 1.52;
            overflow-wrap: anywhere;
        }
        .report-shell {
            padding: 18px 20px;
            line-height: 1.72;
            margin-top: 8px;
        }
        div[data-testid="stVerticalBlock"]:has(.top-nav-marker) {
            position: sticky;
            top: 0.35rem;
            z-index: 40;
            margin-top: -0.15rem;
            margin-bottom: 18px;
        }
        div[data-testid="stVerticalBlock"]:has(.top-nav-marker) > div[data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent;
        }
        .top-nav-shell {
            background: rgba(248, 250, 252, 0.92);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
            padding: 0.75rem 0.85rem 0.9rem 0.85rem;
        }
        .top-nav-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 0.7rem;
        }
        .top-nav-button-row {
            display: flex;
            gap: 12px;
            width: 100%;
        }
        .top-nav-title {
            color: #0f172a;
            font-size: 1.02rem;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.01em;
        }
        .top-nav-subtitle {
            color: #64748b;
            font-size: 0.82rem;
            line-height: 1.45;
            margin-top: 2px;
        }
        .top-nav-context {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: flex-end;
        }
        .context-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 11px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.18);
            color: #334155;
            font-size: 0.78rem;
            font-weight: 700;
            line-height: 1.2;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        .top-action-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 0.15rem 0 0.35rem 0;
        }
        .top-action-copy {
            color: #475569;
            font-size: 0.82rem;
            line-height: 1.45;
            margin: 0;
            overflow-wrap: anywhere;
        }
        div[data-testid="stVerticalBlock"]:has(.top-nav-marker) div[data-testid="stButton"] {
            width: 100%;
        }
        div[data-testid="stVerticalBlock"]:has(.top-nav-marker) div[data-testid="stButton"] > button {
            min-height: 48px;
            width: 100%;
            border-radius: 999px;
            font-size: 0.98rem;
            font-weight: 700;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(255, 255, 255, 0.96);
            color: #475569;
            box-shadow: none;
            transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease, background 160ms ease, color 160ms ease;
        }
        div[data-testid="stVerticalBlock"]:has(.top-nav-marker) div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            border-color: rgba(59, 130, 246, 0.2);
            background: rgba(241, 245, 249, 0.98);
            color: #1e293b;
        }
        div[data-testid="stVerticalBlock"]:has(.top-nav-marker) div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(180deg, #dbeafe 0%, #c7d2fe 100%);
            color: #0f172a;
            border: 1px solid rgba(59, 130, 246, 0.34);
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.5);
        }
        div[data-testid="stVerticalBlock"]:has(.top-nav-marker) div[data-testid="stButton"] > button[kind="primary"] p {
            color: #0f172a;
        }
        .chart-note {
            color: #64748b;
            font-size: 0.84rem;
            line-height: 1.48;
            margin-top: -4px;
            margin-bottom: 12px;
            overflow-wrap: anywhere;
        }
        .section-card {
            padding: 18px;
        }
        .pipeline-text {
            color: #0f172a;
            font-size: 0.84rem;
            line-height: 1.6;
            font-weight: 600;
            overflow-wrap: anywhere;
        }
        .compact-toolbar .stDownloadButton button,
        .compact-toolbar button[kind="secondary"] {
            border-radius: 12px;
            min-height: 2.3rem;
            font-size: 0.85rem;
            white-space: normal;
            overflow-wrap: anywhere;
            transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }
        .compact-toolbar .stDownloadButton button:hover,
        .compact-toolbar button[kind="secondary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
        }
        .compact-toolbar .stButton button {
            border-radius: 12px;
        }
        .stPlotlyChart,
        div[data-testid="stDataFrame"] {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 18px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
            padding: 0.35rem;
        }
        .stPlotlyChart {
            margin-bottom: 0.45rem;
        }
        .stDataFrame, .stMarkdown, .stAlert, .stCodeBlock {
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        @media (max-width: 1100px) {
            .top-nav-header,
            .top-action-row {
                flex-direction: column;
                align-items: flex-start;
            }
            .top-nav-context {
                justify-content: flex-start;
            }
            .top-nav-button-row {
                flex-wrap: wrap;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand_card() -> None:
    st.markdown(
        """
        <div class="brand-card">
            <div class="brand-title">AI Product &amp; Ops Copilot</div>
            <div class="brand-subtitle">Offline evaluation dashboard for existing AI Assistant Q&amp;A and product/operations feedback.</div>
            <div class="badge-row">
                <span class="badge-chip">Local-first</span>
                <span class="badge-chip">Offline</span>
                <span class="badge-chip">Rule-based</span>
                <span class="badge-chip">No API required</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_chip(text: str) -> None:
    st.markdown(f'<div class="status-chip">{text}</div>', unsafe_allow_html=True)


def render_metric_card(icon: str, label: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-topline">{icon} {label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, caption: str, question: str) -> None:
    st.markdown(
        f"""
        <div class="page-title">{title}</div>
        <div class="page-caption">{caption}</div>
        <div class="page-question">Question answered: {question}</div>
        """,
        unsafe_allow_html=True,
    )


def build_standard_template_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "case_id": "EX001",
                "user_role": "employee",
                "source": "HR AI Assistant",
                "raw_feedback": "我想开在职证明，在哪里申请？",
                "ai_answer": "请联系 HR 处理。",
                "user_rating": 2,
                "expected_behavior": "Provide system entry, application steps, required materials, timeline, and support contact.",
                "business_impact": "medium",
                "frequency": 8,
                "created_at": "2026-01-10",
            },
            {
                "case_id": "EX002",
                "user_role": "supplier",
                "source": "B2B Operations",
                "raw_feedback": "物流节点一直没有更新，承运商说已经送达。",
                "ai_answer": "请等待系统同步。",
                "user_rating": 2,
                "expected_behavior": "Check logistics node, carrier feedback, system status, and assign operations or data owner.",
                "business_impact": "high",
                "frequency": 7,
                "created_at": "2026-01-11",
            },
            {
                "case_id": "EX003",
                "user_role": "employee",
                "source": "HR AI Assistant",
                "raw_feedback": "我这种特殊情况能不能特殊审批年假？",
                "ai_answer": "可以申请。",
                "user_rating": 1,
                "expected_behavior": "Escalate to human HR because this is a personal special case.",
                "business_impact": "high",
                "frequency": 4,
                "created_at": "2026-01-12",
            },
        ],
        columns=REQUIRED_COLUMNS,
    )


def build_standard_template_excel_bytes() -> bytes:
    template_df = build_standard_template_dataframe()
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="input_template")
    output.seek(0)
    return output.getvalue()


def initialize_navigation_state() -> None:
    if "active_page" not in st.session_state or st.session_state.active_page not in NAV_OPTIONS:
        st.session_state.active_page = NAV_OPTIONS[0]


def render_top_navigation(source_name: str, uploaded_file) -> str:
    source_label = "Mock data" if uploaded_file is None else source_name
    mode_label = "Offline rule-based" if not has_openai_api_key() else "LLM optional"
    initialize_navigation_state()
    current_page = st.session_state.active_page
    nav_container = st.container()
    with nav_container:
        st.markdown('<div class="top-nav-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="top-nav-shell">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="top-nav-header">
                <div>
                    <div class="top-nav-title">Workspace Navigation</div>
                    <div class="top-nav-subtitle">Keep the analysis flow visible while scrolling and move directly between the six working modules.</div>
                </div>
                <div class="top-nav-context">
                    <span class="context-pill">Source: {source_label}</span>
                    <span class="context-pill">Mode: {mode_label}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        nav_columns = st.columns(len(NAV_OPTIONS))
        for column, page_name in zip(nav_columns, NAV_OPTIONS):
            with column:
                button_type = "primary" if current_page == page_name else "secondary"
                if st.button(page_name, key=f"nav_{page_name}", use_container_width=True, type=button_type):
                    if st.session_state.active_page != page_name:
                        st.session_state.active_page = page_name
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.active_page


def render_info_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="info-panel">
            <div class="info-title">{title}</div>
            <div class="info-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_template_download_card() -> None:
    with st.container(border=True):
        st.markdown(
            """
            <div class="info-title">Input Template</div>
            <div class="info-body">Download the standard Excel template, fill in your Q&amp;A / feedback records, and upload it back to run the analysis.</div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download Excel template",
            data=build_standard_template_excel_bytes(),
            file_name="ai_product_ops_input_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.caption("Keep the column names unchanged. Each row should represent one Q&A or feedback case.")


def render_status_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-label">{label}</div>
            <div class="status-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart_note(text: str) -> None:
    st.markdown(f'<div class="chart-note">{text}</div>', unsafe_allow_html=True)


def render_dataframe_preview(df: pd.DataFrame, height: int = 360) -> None:
    st.dataframe(df, use_container_width=True, height=height)


def render_bar_chart(df: pd.DataFrame, column: str, title: str, color: str, height: int = 320) -> None:
    counts = df[column].fillna("Unknown").value_counts().reset_index()
    counts.columns = [column, "count"]
    figure = px.bar(counts, x=column, y="count", title=title, text_auto=True)
    figure.update_traces(marker_color=color)
    figure.update_layout(
        xaxis_title=None,
        yaxis_title="Cases",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=52, b=8),
        height=height,
    )
    st.plotly_chart(figure, use_container_width=True)


def render_bad_case_chart(chart_df: pd.DataFrame, title: str, color: str) -> None:
    figure = px.bar(chart_df, x="bad_case_type", y="count", title=title, text_auto=True)
    figure.update_traces(marker_color=color)
    figure.update_layout(
        xaxis_title=None,
        yaxis_title="Cases",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=52, b=8),
        height=320,
    )
    st.plotly_chart(figure, use_container_width=True)


def render_owner_guide() -> None:
    owner_cards = [
        ("HR Team", "HR policy, SOP, FAQ, process content."),
        ("IT Team", "System entry, access, internal tool path, permissions."),
        ("Product Team", "Prompt, answer structure, AI behavior rules."),
        ("Operations Team", "B2B workflow, logistics, merchant operations, process execution."),
        ("Data Team", "Data mismatch, pipeline issue, dashboard issue."),
        ("Human Support", "Sensitive, personal, exception, escalation-required cases."),
    ]
    cols = st.columns(3)
    for index, (title, body) in enumerate(owner_cards):
        with cols[index % 3]:
            st.markdown(
                f"""
                <div class="owner-card">
                    <div class="owner-title">{title}</div>
                    <div class="owner-body">{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_report_preview(report: str) -> None:
    with st.container(border=True):
        st.markdown(report)


def build_duplicate_examples(prepared_df: pd.DataFrame) -> pd.DataFrame:
    working = prepared_df.copy()
    working["cleaned_feedback_candidate"] = working["raw_feedback"].apply(clean_text)
    working = working[working["cleaned_feedback_candidate"].ne("")]
    working = working[
        working["cleaned_feedback_candidate"].duplicated(keep=False)
    ][["case_id", "source", "raw_feedback", "cleaned_feedback_candidate"]]
    return working.head(12)


def build_invalid_examples(prepared_df: pd.DataFrame) -> pd.DataFrame:
    working = prepared_df.copy()
    working["cleaned_feedback_candidate"] = working["raw_feedback"].apply(clean_text)
    working = working[working["cleaned_feedback_candidate"].eq("")][
        ["case_id", "source", "raw_feedback", "ai_answer", "user_role"]
    ]
    return working.head(12)


def build_bad_case_chart_df(analyzed_df: pd.DataFrame) -> pd.DataFrame:
    labels = analyzed_df["bad_case_labels"].apply(split_pipe_labels).explode()
    labels = labels[labels.notna()]
    labels = labels[labels.ne("no_bad_case")]
    if labels.empty:
        return pd.DataFrame({"bad_case_type": ["no_bad_case"], "count": [0]})
    counts = labels.value_counts().reset_index()
    counts.columns = ["bad_case_type", "count"]
    return counts


def extract_top_bad_case_types(analyzed_df: pd.DataFrame, limit: int = 3) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for labels in analyzed_df["bad_case_labels"].apply(split_pipe_labels):
        for label in labels:
            if label != "no_bad_case":
                counter[label] += 1
    return counter.most_common(limit)


def build_first_action_summary(analyzed_df: pd.DataFrame, top_bad_case_types: list[tuple[str, int]]) -> str:
    label_names = {name for name, _ in top_bad_case_types}
    if "missing_steps" in label_names and "missing_system_entry" in label_names:
        return "If missing_steps and missing_system_entry dominate, prioritize SOP and system entry updates."
    if "failed_human_escalation" in label_names:
        return "Add a stronger escalation rule first so sensitive cases stop ending inside the assistant."
    if not analyzed_df.empty:
        return f"Start with {analyzed_df['next_action'].value_counts().idxmax()} for the highest-volume high-impact issues."
    return "Review the current batch and identify the dominant issue pattern first."


def _most_common_value(series: pd.Series, fallback: str = "Unknown") -> str:
    cleaned = series.fillna(fallback).astype(str)
    if cleaned.empty:
        return fallback
    counts = cleaned.value_counts()
    return str(counts.index[0]) if not counts.empty else fallback


def build_owner_action_board(high_priority_df: pd.DataFrame) -> pd.DataFrame:
    if high_priority_df.empty:
        return pd.DataFrame(
            columns=[
                "recommended_owner",
                "high_priority_cases",
                "top_issue_category",
                "top_next_action",
                "team_action",
            ]
        )

    records: list[dict[str, str | int]] = []
    grouped = high_priority_df.groupby("recommended_owner", dropna=False)
    for owner, owner_df in grouped:
        owner_name = owner if pd.notna(owner) and str(owner).strip() else "Unassigned"
        records.append(
            {
                "recommended_owner": owner_name,
                "high_priority_cases": int(len(owner_df)),
                "top_issue_category": _most_common_value(owner_df["primary_issue_category"]),
                "top_next_action": _most_common_value(owner_df["next_action"]),
                "team_action": OWNER_ACTION_SUGGESTIONS.get(owner_name, "Review the high-priority cases and confirm the next operational owner."),
            }
        )

    board_df = pd.DataFrame(records)
    return board_df.sort_values(by=["high_priority_cases", "recommended_owner"], ascending=[False, True]).reset_index(drop=True)


def render_owner_action_board(board_df: pd.DataFrame) -> None:
    if board_df.empty:
        render_info_panel(
            "Owner Action Board",
            "No high-priority cases were identified in the current batch, so there is no immediate owner action summary to review.",
        )
        return

    st.markdown("Owner Action Board")
    card_columns = st.columns(3)
    for index, record in board_df.iterrows():
        with card_columns[index % 3]:
            st.markdown(
                f"""
                <div class="action-board-card">
                    <div class="action-board-owner">{record['recommended_owner']}</div>
                    <div class="action-board-count">{record['high_priority_cases']}</div>
                    <div class="action-board-meta"><strong>Top issue:</strong> {record['top_issue_category']}</div>
                    <div class="action-board-meta"><strong>Top next action:</strong> {record['top_next_action']}</div>
                    <div class="action-board-note">{record['team_action']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def run_pipeline(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int], pd.DataFrame, str]:
    prepared_df = prepare_input_dataframe(df)
    cleaned_df, cleaning_summary = clean_feedback_dataframe(prepared_df)
    classified_df = add_classification_columns(cleaned_df)
    bad_case_df = add_bad_case_columns(classified_df)
    analyzed_df = add_priority_columns(bad_case_df)
    report = generate_markdown_report(analyzed_df, cleaning_summary)
    return prepared_df, cleaning_summary, analyzed_df, report


def render_sidebar(
    uploaded_file,
    source_name: str,
    prepared_df: pd.DataFrame,
    cleaning_summary: dict[str, int],
) -> None:
    data_source_text = "Using bundled mock data" if uploaded_file is None else f"Using uploaded file: {source_name}"

    with st.sidebar:
        render_info_panel("Current data source", data_source_text)
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            render_status_card("Loaded rows", str(len(prepared_df)))
        with stats_col2:
            render_status_card("Valid rows", str(cleaning_summary["cleaned_rows"]))
        stats_col3, stats_col4 = st.columns(2)
        with stats_col3:
            render_status_card("Duplicates", str(cleaning_summary["duplicate_rows"]))
        with stats_col4:
            render_status_card("Current mode", "Offline" if not has_openai_api_key() else "LLM optional")
        render_template_download_card()
        with st.expander("How to use", expanded=False):
            st.write("Upload existing Q&A or feedback records, review issue categories and bad cases, then prioritize the next fixes and owners.")


def render_download_bar(
    cleaned_export: pd.DataFrame,
    report: str,
    source_name: str,
    uploaded_file,
) -> None:
    st.markdown(
        f"""
        <div class="top-action-row">
            <p class="top-action-copy">Export the cleaned dataset, full analyzed results, or the generated markdown report without leaving the current module.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        st.markdown('<div class="compact-toolbar">', unsafe_allow_html=True)
        st.download_button(
            "Cleaned CSV",
            data=dataframe_to_csv_bytes(cleaned_export[[*REQUIRED_COLUMNS, "cleaned_feedback"]]),
            file_name="cleaned_feedback.csv",
            mime="text/csv",
            use_container_width=True,
            help="UTF-8-SIG encoded for direct opening in Windows Excel.",
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with btn_col2:
        st.markdown('<div class="compact-toolbar">', unsafe_allow_html=True)
        st.download_button(
            "Analyzed CSV",
            data=dataframe_to_csv_bytes(cleaned_export),
            file_name="analyzed_feedback.csv",
            mime="text/csv",
            use_container_width=True,
            help="UTF-8-SIG encoded for direct opening in Windows Excel.",
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with btn_col3:
        st.markdown('<div class="compact-toolbar">', unsafe_allow_html=True)
        st.download_button(
            "Report MD",
            data=report.encode("utf-8"),
            file_name="generated_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)



def render_overview_page(analyzed_df: pd.DataFrame, cleaning_summary: dict[str, int]) -> None:
    render_page_header(
        "Overview Dashboard",
        "Executive snapshot of quality, risk, and operational handling urgency for the current feedback batch.",
        "What is the overall quality of this feedback batch?",
    )
    top_issue_categories = top_items(analyzed_df["primary_issue_category"], limit=3)
    top_bad_case_types = extract_top_bad_case_types(analyzed_df, limit=3)
    high_priority_count = int((analyzed_df["priority_level"] == "High").sum())
    first_action_summary = build_first_action_summary(analyzed_df, top_bad_case_types)
    bad_case_chart_df = build_bad_case_chart_df(analyzed_df)

    metric_columns = st.columns(6)
    cards = [
        ("📦", "Total cases", str(cleaning_summary["original_rows"]), "All rows loaded from the selected input file."),
        ("✅", "Valid cases", str(cleaning_summary["cleaned_rows"]), "Rows retained after cleaning and exact deduplication."),
        ("🧩", "Duplicate cases", str(cleaning_summary["duplicate_rows"]), "Repeated feedback entries detected by exact cleaned text."),
        ("⚠️", "Bad case count", str(int(analyzed_df["is_bad_case"].sum())), "Cases where the current AI answer may be incomplete, vague, or risky."),
        ("🔥", "High priority cases", str(high_priority_count), "Issues that should be handled first based on impact, frequency, rating, and risk."),
        ("⭐", "Average user rating", f"{analyzed_df['user_rating'].mean():.2f}", "Observed answer satisfaction signal from the uploaded evaluation data."),
    ]
    for column, card in zip(metric_columns, cards):
        with column:
            render_metric_card(*card)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        render_bar_chart(analyzed_df, "primary_issue_category", "Issue Category Distribution", color="#2563eb")
        render_chart_note("If policy and process questions dominate, your team likely needs stronger SOP, FAQ, and answer templates before model-level optimization.")
    with chart_col2:
        render_bad_case_chart(bad_case_chart_df, "Bad Case Type Distribution", color="#ef4444")
        render_chart_note("This shows how the existing AI Assistant is failing after testing, for example by missing steps, missing system paths, or staying too generic.")

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        render_bar_chart(analyzed_df, "priority_level", "Priority Distribution", color="#f59e0b")
        render_chart_note("Priority is operational handling urgency, not model confidence. High counts indicate immediate iteration workload.")
    with chart_col4:
        render_bar_chart(analyzed_df, "source", "Source Distribution", color="#0ea5e9")
        render_chart_note("Compare which business scenario is currently generating the most friction: HR, B2B operations, e-commerce operations, or customer support.")

    lower_left, lower_right = st.columns([1.2, 1])
    with lower_left:
        render_bar_chart(analyzed_df, "user_role", "User Role Distribution", color="#8b5cf6")
        render_chart_note("This shows whether the most urgent pain points come mainly from employees, merchants, customers, managers, or operations specialists.")
    with lower_right:
        top_issue = top_issue_categories[0] if top_issue_categories else ("No data", 0)
        top_bad_case = top_bad_case_types[0] if top_bad_case_types else ("No major bad case pattern", 0)
        st.markdown(
            f"""
            <div class="highlight-panel">
                <div class="highlight-kicker">What To Look At First</div>
                <p><strong>Top issue category</strong><br>{top_issue[0]} ({top_issue[1]})</p>
                <p><strong>Top bad case type</strong><br>{top_bad_case[0]} ({top_bad_case[1]})</p>
                <p><strong>High-priority cases</strong><br>{high_priority_count}</p>
                <p><strong>Suggested first action</strong><br>{first_action_summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )



def render_cleaning_page(prepared_df: pd.DataFrame, analyzed_df: pd.DataFrame, cleaning_summary: dict[str, int]) -> None:
    render_page_header(
        "Data Cleaning",
        "Data quality inspection for rows removed or normalized before downstream analysis.",
        "Which records were removed or normalized before analysis?",
    )
    metrics = [
        ("Original rows", cleaning_summary["original_rows"]),
        ("Invalid rows removed", cleaning_summary["invalid_rows"]),
        ("Duplicate rows removed", cleaning_summary["duplicate_rows"]),
        ("Cleaned rows", cleaning_summary["cleaned_rows"]),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        with col:
            render_status_card(label, str(value))

    duplicate_examples = build_duplicate_examples(prepared_df)
    invalid_examples = build_invalid_examples(prepared_df)

    if not duplicate_examples.empty:
        st.markdown("Duplicate examples")
        render_dataframe_preview(duplicate_examples, height=260)
    if not invalid_examples.empty:
        st.markdown("Invalid row examples")
        render_dataframe_preview(invalid_examples, height=240)

    st.markdown("Cleaned data preview")
    render_dataframe_preview(
        analyzed_df[["case_id", "source", "raw_feedback", "cleaned_feedback", "user_role"]].head(30),
        height=420,
    )
    render_info_panel(
        "Limitation note",
        "Current deduplication is exact-match based. Future versions can use semantic deduplication with embeddings or LLM.",
    )



def render_classification_page(analyzed_df: pd.DataFrame) -> None:
    render_page_header(
        "Issue Classification",
        "Product analytics view of the dominant question and issue types in the uploaded evaluation batch.",
        "What types of problems are users asking about?",
    )
    left, right = st.columns(2)
    with left:
        render_bar_chart(analyzed_df, "primary_issue_category", "Primary Issue Category Distribution", color="#2563eb")
        render_chart_note("Many Process Questions usually means the team needs clearer SOP. Many System Entry issues usually means the FAQ should include paths, links, or screenshots.")
    with right:
        render_bar_chart(analyzed_df, "secondary_tag", "Secondary Tag Distribution", color="#10b981")
        render_chart_note("Secondary tags reveal narrower business patterns such as reimbursement, system access, merchant onboarding, approval delay, or logistics exception.")

    render_dataframe_preview(
        analyzed_df[["case_id", "source", "raw_feedback", "primary_issue_category", "secondary_tag"]].head(30),
        height=430,
    )
    with st.expander("Category Guide"):
        st.markdown(
            """
- Policy / Rule Question: asks about formal rules, policy boundaries, benefits, or eligibility.
- Process Question: asks how to complete a task, submit a request, or move through a workflow.
- System Entry: asks where the user should click, enter, log in, or find the correct path.
- Product Usage Issue: asks how to use a feature or complete a product or e-commerce operation task.
- Data / Operation Exception: reports a field error, abnormal submission, duplicate modification, or data mismatch.
- Knowledge Gap: suggests the FAQ or knowledge base is incomplete or outdated.
- Human Escalation Needed: should be routed to support, HR, manager, or manual review.
- High-risk / Sensitive: involves sensitive HR, compliance, legal, privacy, or unsafe prompt behavior.
- Other: does not strongly match the current deterministic rules.
            """
        )
    render_info_panel(
        "Business interpretation",
        "Many Process Questions -> improve SOP. Many System Entry issues -> add portal, path, link, or screenshot guidance. Many Knowledge Gap cases -> update FAQ and knowledge base coverage. Many Human Escalation cases -> add clearer handoff rules.",
    )



def render_bad_cases_page(analyzed_df: pd.DataFrame) -> None:
    render_page_header(
        "Bad Case Analysis",
        "Evaluation report for existing AI answers after testing, focused on answer quality failures rather than real-time generation.",
        "Where did the existing AI Assistant fail?",
    )
    render_info_panel(
        "Module explanation",
        "This module analyzes existing AI answers after testing. It does not generate real-time answers. It identifies answer quality failures such as missing steps, generic responses, missing system entry, failed escalation, or hallucination risk.",
    )

    bad_case_count = int(analyzed_df["is_bad_case"].sum())
    severe_cases = analyzed_df[
        analyzed_df["bad_case_labels"].str.contains(
            "hallucination_risk|failed_human_escalation|missing_system_entry|missing_steps|generic_answer",
            na=False,
        )
    ]
    severe_count = int(len(severe_cases))
    stat_col1, stat_col2 = st.columns(2)
    with stat_col1:
        render_metric_card("⚠️", "Bad case count", str(bad_case_count), "Rows where the current AI answer may need prompt, SOP, FAQ, or escalation improvement.")
    with stat_col2:
        render_metric_card("🚨", "Severe bad case count", str(severe_count), "Rows with higher-risk answer failures such as weak escalation or hallucination risk.")

    render_bad_case_chart(build_bad_case_chart_df(analyzed_df), "Bad Case Type Distribution", color="#ef4444")
    render_chart_note("This is the strongest interview page because it turns model output review into concrete failure labels and business actions.")

    st.markdown("Severe bad case examples")
    render_dataframe_preview(
        severe_cases[["case_id", "source", "raw_feedback", "ai_answer", "expected_behavior", "bad_case_labels", "user_rating"]].head(24),
        height=420,
    )

    with st.expander("Bad Case Label Guide"):
        st.markdown(
            """
- incomplete_answer: answer misses key information.
- missing_steps: process question lacks step-by-step instructions.
- missing_system_entry: system entry, path, or link is missing.
- knowledge_gap: likely missing FAQ or knowledge base coverage.
- hallucination_risk: AI gives a confident answer in a risky or uncertain case.
- generic_answer: answer is too vague to execute.
- over_refusal: AI refuses when it could answer safely.
- failed_human_escalation: should have routed to human but did not.
- intent_mismatch: answer does not match user intent.
            """
        )

    render_info_panel(
        "Optimization Mapping",
        "missing_steps -> improve SOP / force step-by-step answer format; missing_system_entry -> add portal, path, and link instructions; knowledge_gap -> update FAQ / knowledge base; generic_answer -> improve prompt structure; failed_human_escalation -> add escalation rule; hallucination_risk -> add risk guardrail and manual review.",
    )



def render_priority_page(analyzed_df: pd.DataFrame) -> None:
    render_page_header(
        "Priority Scoring",
        "Operational triage board for deciding which issues should be handled first, by which team, and with what next action.",
        "Which issues should be handled first, by which team, and what should they do next?",
    )
    render_info_panel(
        "Priority logic",
        "Priority is not model confidence. It is operational handling priority based on business impact, frequency, user rating, bad case type, and risk.",
    )
    render_bar_chart(analyzed_df, "priority_level", "Priority Distribution", color="#f97316")
    render_chart_note("High priority means the issue should be handled earlier in the operating queue because it is costly, frequent, risky, or badly rated.")

    high_priority_df = analyzed_df[analyzed_df["priority_level"] == "High"].copy()
    owner_action_board = build_owner_action_board(high_priority_df)

    render_owner_action_board(owner_action_board)
    if not high_priority_df.empty:
        render_bar_chart(high_priority_df, "recommended_owner", "High Priority Cases by Recommended Owner", color="#2563eb", height=300)
        render_chart_note("This owner view shows which department should pick up the most urgent cases first and what kind of operational action is clustering there.")

    priority_columns = [
        "case_id",
        "source",
        "recommended_owner",
        "next_action",
        "primary_issue_category",
        "bad_case_labels",
        "business_impact",
        "frequency",
        "user_rating",
        "priority_score",
        "priority_level",
    ]

    st.markdown("High priority cases")
    render_dataframe_preview(
        high_priority_df[priority_columns].sort_values(by="priority_score", ascending=False),
        height=340,
    )
    with st.expander("Full priority table"):
        render_dataframe_preview(
            analyzed_df[priority_columns].sort_values(by="priority_score", ascending=False),
            height=420,
        )

    st.markdown("Owner guide")
    render_owner_guide()



def render_report_page(analyzed_df: pd.DataFrame, cleaning_summary: dict[str, int], report: str) -> str:
    render_page_header(
        "Report Generator",
        "Final business output page for weekly AI Assistant MVP review, iteration meetings, and product operations retrospectives.",
        "What should the product or ops team discuss in the next iteration meeting?",
    )
    toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([1, 1, 4])
    current_report = report
    with toolbar_col1:
        if st.button("Regenerate report", use_container_width=True):
            current_report = generate_markdown_report(analyzed_df, cleaning_summary)
    with toolbar_col2:
        st.download_button(
            "Download report",
            data=current_report.encode("utf-8"),
            file_name="generated_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with toolbar_col3:
        st.caption("Use this report for weekly AI Assistant MVP review, HR/IT/Product iteration meeting, B2B operations issue review, or product operations retrospective.")

    render_report_preview(current_report)
    return current_report



def main() -> None:
    st.set_page_config(page_title="AI Product & Ops Copilot", page_icon="🤖", layout="wide")
    apply_global_styles()
    initialize_navigation_state()

    with st.sidebar:
        render_sidebar_brand_card()
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

    try:
        raw_df, source_name = load_input_file(uploaded_file, validate_schema=True)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Failed to load input data: {exc}")
        st.stop()

    try:
        prepared_df, cleaning_summary, analyzed_df, report = run_pipeline(raw_df)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Pipeline execution failed: {exc}")
        st.stop()

    st.session_state.generated_report = report

    cleaned_export = analyzed_df.drop(columns=["bad_case_labels_list"], errors="ignore")
    render_sidebar(uploaded_file, source_name, prepared_df, cleaning_summary)

    nav_choice = render_top_navigation(source_name, uploaded_file)

    render_download_bar(cleaned_export, st.session_state.generated_report, source_name, uploaded_file)

    if nav_choice == "Overview":
        render_overview_page(analyzed_df, cleaning_summary)
    elif nav_choice == "Cleaning":
        render_cleaning_page(prepared_df, analyzed_df, cleaning_summary)
    elif nav_choice == "Classification":
        render_classification_page(analyzed_df)
    elif nav_choice == "Bad Cases":
        render_bad_cases_page(analyzed_df)
    elif nav_choice == "Priority":
        render_priority_page(analyzed_df)
    elif nav_choice == "Report":
        st.session_state.generated_report = render_report_page(analyzed_df, cleaning_summary, st.session_state.generated_report)


if __name__ == "__main__":
    main()
