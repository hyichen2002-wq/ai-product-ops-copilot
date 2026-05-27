from __future__ import annotations

from datetime import datetime

import pandas as pd

from .utils import format_percent, list_to_bullets, split_pipe_labels, top_items



def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No records available."
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = ["| " + " | ".join(str(value) for value in row) + " |" for row in df.itertuples(index=False, name=None)]
    return "\n".join([header, separator, *rows])



def _collect_bad_case_counts(df: pd.DataFrame) -> pd.Series:
    labels = df["bad_case_labels"].apply(split_pipe_labels).explode()
    labels = labels[labels.ne("no_bad_case")]
    if labels.empty:
        return pd.Series(dtype=int)
    return labels.value_counts()



def _build_suggestions(df: pd.DataFrame) -> tuple[list[str], list[str], list[str], list[str]]:
    process_missing_steps = len(df[(df["primary_issue_category"] == "Process Question") & (df["bad_case_labels"].str.contains("missing_steps", na=False))])
    system_entry_missing = len(df[(df["primary_issue_category"] == "System Entry") & (df["bad_case_labels"].str.contains("missing_system_entry", na=False))])
    failed_escalation = len(df[df["bad_case_labels"].str.contains("failed_human_escalation", na=False)])
    knowledge_gap = len(df[(df["primary_issue_category"] == "Knowledge Gap") | (df["bad_case_labels"].str.contains("knowledge_gap", na=False))])
    generic_answer = len(df[df["bad_case_labels"].str.contains("generic_answer", na=False)])

    knowledge_base = []
    prompt = []
    sop = []
    escalation = []

    if process_missing_steps > 0:
        knowledge_base.append("Add step-by-step SOP references for recurring process questions such as reimbursement, certificate requests, and approval flows.")
        sop.append("Standardize process answers into step, owner, materials, timeline, and escalation path.")
    if system_entry_missing > 0:
        knowledge_base.append("Add system entry links, menu paths, and screenshots to FAQ content for portal and login questions.")
    if failed_escalation > 0:
        prompt.append("Add a hard escalation rule when the query includes personal cases, manual approvals, HR exceptions, or support tickets.")
        sop.append("Route high-risk or exception cases to human support with a visible ticket handoff rule.")
        escalation.append("Add visible escalation instructions with contact owner, ticket path, and manual review boundary for exception-heavy cases.")
    if knowledge_gap > 0:
        knowledge_base.append("Expand FAQ and knowledge base coverage for uncovered topics and unsupported edge cases.")
    if generic_answer > 0:
        prompt.append("Use a stricter response template with conclusion, steps, owner, required materials, timeline, and escalation path.")
    if system_entry_missing > 0:
        escalation.append("Define a fallback escalation route when users cannot find the correct portal, menu path, or required system permission.")

    if not knowledge_base:
        knowledge_base.append("Current knowledge coverage is acceptable; continue monitoring uncovered questions in the next batch.")
    if not prompt:
        prompt.append("Current prompt structure is stable; keep tracking answer quality by scenario and role.")
    if not sop:
        sop.append("Document the current SOP baseline and compare future response quality after updates.")
    if not escalation:
        escalation.append("Current escalation coverage is stable; keep monitoring sensitive, personal, and manual-review cases.")

    return knowledge_base, prompt, sop, escalation



def generate_markdown_report(df: pd.DataFrame, cleaning_summary: dict[str, int]) -> str:
    total_cases = len(df)
    high_priority_cases = df[df["priority_level"] == "High"]
    bad_case_count = int(df["is_bad_case"].sum())
    average_rating = float(df["user_rating"].mean()) if total_cases else 0.0
    bad_case_counts = _collect_bad_case_counts(df)
    top_bad_cases = bad_case_counts.head(5)
    knowledge_base, prompt, sop, escalation = _build_suggestions(df)

    owner_actions = (
        df.groupby(["recommended_owner", "next_action"])["case_id"]
        .count()
        .sort_values(ascending=False)
        .rename("case_count")
        .reset_index()
    )

    high_priority_table = high_priority_cases[
        ["case_id", "source", "primary_issue_category", "bad_case_labels", "priority_score", "next_action"]
    ].head(10)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    top_category_lines = [f"{name}: {count}" for name, count in top_items(df["primary_issue_category"])]
    top_bad_case_lines = [f"{name}: {count}" for name, count in top_bad_cases.items()]
    if not top_bad_case_lines:
        top_bad_case_lines = ["No significant bad case pattern detected in this batch."]

    return f"""# AI Product & Ops Copilot Report

Generated at: {generated_at}

## 1. Executive Summary
This batch contains {total_cases} cleaned cases across product, operations, HR assistant evaluation, and customer support scenarios. {bad_case_count} cases ({format_percent(bad_case_count, total_cases)}) were flagged as bad cases, and {len(high_priority_cases)} cases ({format_percent(len(high_priority_cases), total_cases)}) were scored as high priority. The current average user rating is {average_rating:.2f}/5.0.

## 2. Key Numbers
- Original rows: {cleaning_summary.get("original_rows", total_cases)}
- Invalid rows removed: {cleaning_summary.get("invalid_rows", 0)}
- Duplicate rows removed: {cleaning_summary.get("duplicate_rows", 0)}
- Cleaned rows: {cleaning_summary.get("cleaned_rows", total_cases)}
- High priority cases: {len(high_priority_cases)}
- Average user rating: {average_rating:.2f}

## 3. Main Issue Categories
{list_to_bullets(top_category_lines)}

## 4. Main Bad Case Patterns
{list_to_bullets(top_bad_case_lines)}

## 5. Top High Priority Cases
{_markdown_table(high_priority_table)}

## 6. Recommended Knowledge Base Updates
{list_to_bullets(knowledge_base)}

## 7. Recommended Prompt Updates
{list_to_bullets(prompt)}

## 8. Recommended SOP Updates
{list_to_bullets(sop)}

## 9. Recommended Human Escalation Rules
{list_to_bullets(escalation)}

## 10. Team-level Action Items
{_markdown_table(owner_actions)}

## 11. Next Iteration Plan
- Review top high-priority cases with the recommended owners and confirm whether FAQ, SOP, prompt, or system changes are needed first.
- Convert repeated missing_steps and missing_system_entry cases into reusable answer templates.
- Add a manual escalation boundary for sensitive HR, legal, compensation, and exception-based requests.
- Re-run the pipeline after updates and compare priority distribution, bad case rate, and user rating improvement.
"""
