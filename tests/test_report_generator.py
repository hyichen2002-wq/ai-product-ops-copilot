import pandas as pd

from src.report_generator import generate_markdown_report



def test_report_generator_outputs_required_sections():
    df = pd.DataFrame(
        [
            {
                "case_id": "CASE-1",
                "source": "customer_support",
                "primary_issue_category": "Process Question",
                "bad_case_labels": "missing_steps|generic_answer",
                "priority_level": "High",
                "priority_score": 82,
                "next_action": "improve SOP",
                "recommended_owner": "Operations Team",
                "is_bad_case": True,
                "user_rating": 2,
            }
        ]
    )
    cleaning_summary = {"original_rows": 1, "invalid_rows": 0, "duplicate_rows": 0, "cleaned_rows": 1}
    report = generate_markdown_report(df, cleaning_summary)
    assert "## 1. Executive Summary" in report
    assert "## 7. Recommended Prompt Updates" in report
    assert "## 9. Recommended Human Escalation Rules" in report
    assert "CASE-1" in report
