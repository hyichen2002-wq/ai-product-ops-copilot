from __future__ import annotations

import pandas as pd

from .cleaner import clean_text
from .utils import split_pipe_labels

GENERIC_ANSWER_PHRASES = [
    "please follow company policy",
    "please contact the relevant team",
    "please check the system",
    "please check backend",
    "请联系相关部门",
    "请查看后台",
    "请查看系统",
    "请按公司政策执行",
]
CONTACT_TERMS = [
    "contact",
    "human",
    "hr",
    "support",
    "ticket",
    "manager",
    "人工",
    "联系",
    "工单",
    "客服",
    "helpdesk",
]
ENTRY_TERMS = [
    "link",
    "portal",
    "url",
    "path",
    "menu",
    "step",
    "login",
    "入口",
    "链接",
    "菜单",
    "路径",
    "登录",
]
PROCESS_TERMS = [
    "流程",
    "how",
    "怎么",
    "申请",
    "报销",
    "证明",
    "submit",
    "apply",
]
SENSITIVE_TERMS = [
    "salary",
    "performance",
    "legal",
    "compliance",
    "privacy",
    "special case",
    "personal case",
    "薪资",
    "绩效",
    "合规",
    "隐私",
    "特殊情况",
    "个人情况",
]
CONFIDENT_TERMS = [
    "can",
    "will",
    "should",
    "eligible",
    "approved",
    "可以",
    "应当",
    "会",
    "能够",
]
OVER_REFUSAL_TERMS = [
    "cannot help",
    "unable to help",
    "contact support",
    "无法帮助",
    "不支持",
    "请联系人工",
]
KNOWLEDGE_GAP_TERMS = [
    "not found",
    "not available",
    "not in knowledge base",
    "暂无信息",
    "未收录",
    "无法确认",
]



def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)



def analyze_bad_case(row: pd.Series) -> list[str]:
    raw_feedback = clean_text(row.get("raw_feedback", "")).lower()
    ai_answer = clean_text(row.get("ai_answer", "")).lower()
    expected_behavior = clean_text(row.get("expected_behavior", "")).lower()
    user_rating = float(row.get("user_rating", 0) or 0)

    labels: list[str] = []
    generic_answer = contains_any(ai_answer, GENERIC_ANSWER_PHRASES)
    missing_contact = not contains_any(ai_answer, CONTACT_TERMS)
    missing_entry = not contains_any(ai_answer, ENTRY_TERMS)
    too_short = len(ai_answer) < 60

    if user_rating <= 2 and too_short:
        labels.append("incomplete_answer")

    if contains_any(expected_behavior, ["escalate", "human", "manual", "人工", "hr", "support", "ticket"]) and missing_contact:
        labels.append("failed_human_escalation")

    if contains_any(raw_feedback, ["where", "入口", "在哪里", "system", "portal", "link", "链接"]) and missing_entry:
        labels.append("missing_system_entry")

    if contains_any(raw_feedback, PROCESS_TERMS) and (too_short or generic_answer):
        labels.append("missing_steps")

    if generic_answer:
        labels.append("generic_answer")

    if contains_any(ai_answer, KNOWLEDGE_GAP_TERMS):
        labels.append("knowledge_gap")

    if contains_any(raw_feedback, SENSITIVE_TERMS) and contains_any(ai_answer, CONFIDENT_TERMS) and missing_contact:
        labels.extend(["hallucination_risk", "failed_human_escalation"])

    if contains_any(ai_answer, OVER_REFUSAL_TERMS) and not contains_any(raw_feedback, SENSITIVE_TERMS):
        labels.append("over_refusal")

    if user_rating <= 2 and not labels:
        labels.append("intent_mismatch")

    if not labels and user_rating >= 4:
        labels.append("no_bad_case")

    deduplicated_labels: list[str] = []
    for label in labels:
        if label not in deduplicated_labels:
            deduplicated_labels.append(label)
    return deduplicated_labels



def add_bad_case_columns(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["bad_case_labels_list"] = working.apply(analyze_bad_case, axis=1)
    working["bad_case_labels"] = working["bad_case_labels_list"].apply(
        lambda labels: "|".join(labels) if labels else "no_bad_case"
    )
    working["bad_case_count"] = working["bad_case_labels_list"].apply(
        lambda labels: 0 if labels == ["no_bad_case"] else len(labels)
    )
    working["is_bad_case"] = working["bad_case_count"] > 0
    return working
