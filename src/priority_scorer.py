from __future__ import annotations

import pandas as pd

from .utils import split_pipe_labels

IMPACT_POINTS = {"high": 30, "medium": 18, "low": 8}



def score_priority(row: pd.Series) -> tuple[int, str, str, str]:
    labels = split_pipe_labels(row.get("bad_case_labels", ""))
    business_impact = str(row.get("business_impact", "medium")).lower()
    frequency = int(row.get("frequency", 0) or 0)
    user_rating = float(row.get("user_rating", 0) or 0)
    primary_issue_category = str(row.get("primary_issue_category", "Other"))
    secondary_tag = str(row.get("secondary_tag", "other"))
    raw_feedback = str(row.get("raw_feedback", "")).lower()

    score = IMPACT_POINTS.get(business_impact, 18)
    score += min(20, frequency * 2)

    if user_rating <= 2:
        score += 20
    elif user_rating <= 3:
        score += 10

    if primary_issue_category == "High-risk / Sensitive":
        score += 20

    if "failed_human_escalation" in labels:
        score += 18
    if "hallucination_risk" in labels:
        score += 18
    if "missing_steps" in labels or "missing_system_entry" in labels:
        score += 10
    if "generic_answer" in labels or "knowledge_gap" in labels:
        score += 8
    if labels == ["no_bad_case"]:
        score -= 15

    score = max(0, min(100, score))

    if score >= 70:
        priority_level = "High"
    elif score >= 40:
        priority_level = "Medium"
    else:
        priority_level = "Low"

    recommended_owner = "Operations Team"
    if primary_issue_category in {"Policy / Rule Question", "High-risk / Sensitive"} or secondary_tag in {"leave_request", "reimbursement", "certificate_request", "personal_case"}:
        recommended_owner = "HR Team"
    elif primary_issue_category == "System Entry" or secondary_tag == "system_access":
        recommended_owner = "IT Team"
    elif primary_issue_category == "Product Usage Issue" or secondary_tag in {"campaign_setup", "product_listing", "refund_after_sales"}:
        recommended_owner = "Product Team"
    elif primary_issue_category == "Data / Operation Exception" and any(keyword in raw_feedback for keyword in ["data", "字段", "duplicate", "重复"]):
        recommended_owner = "Data Team"
    elif primary_issue_category == "Human Escalation Needed" or "failed_human_escalation" in labels:
        recommended_owner = "Human Support"

    next_action = "update FAQ"
    if "failed_human_escalation" in labels:
        next_action = "add human escalation rule"
    elif primary_issue_category == "High-risk / Sensitive":
        next_action = "clarify policy boundary"
    elif "missing_system_entry" in labels:
        next_action = "add system entry instruction"
    elif "missing_steps" in labels or primary_issue_category == "Process Question":
        next_action = "improve SOP"
    elif "generic_answer" in labels or "incomplete_answer" in labels:
        next_action = "improve prompt"
    elif primary_issue_category == "Data / Operation Exception":
        next_action = "check data pipeline"
    elif priority_level == "High":
        next_action = "follow up with user"

    return score, priority_level, recommended_owner, next_action



def add_priority_columns(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    scored = working.apply(score_priority, axis=1)
    working["priority_score"] = scored.apply(lambda item: item[0])
    working["priority_level"] = scored.apply(lambda item: item[1])
    working["recommended_owner"] = scored.apply(lambda item: item[2])
    working["next_action"] = scored.apply(lambda item: item[3])
    return working
