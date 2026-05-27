import pandas as pd

from src.bad_case_analyzer import analyze_bad_case
from src.priority_scorer import score_priority



def test_bad_case_analysis_detects_missing_escalation_and_steps():
    row = pd.Series(
        {
            "raw_feedback": "报销流程怎么走？个人特殊情况要人工处理吗？",
            "ai_answer": "请按公司政策执行。",
            "expected_behavior": "Provide steps and escalate to HR manual review.",
            "user_rating": 1,
        }
    )
    labels = analyze_bad_case(row)
    assert "missing_steps" in labels
    assert "failed_human_escalation" in labels



def test_priority_score_marks_high_risk_case_as_high_priority():
    row = pd.Series(
        {
            "bad_case_labels": "hallucination_risk|failed_human_escalation",
            "business_impact": "high",
            "frequency": 5,
            "user_rating": 1,
            "primary_issue_category": "High-risk / Sensitive",
            "secondary_tag": "personal_case",
            "raw_feedback": "salary special case",
        }
    )
    score, level, owner, action = score_priority(row)
    assert score >= 70
    assert level == "High"
    assert owner in {"HR Team", "Human Support"}
    assert action in {"add human escalation rule", "clarify policy boundary"}
