import pandas as pd

from src.bad_case_analyzer import add_bad_case_columns
from src.classifier import add_classification_columns
from src.cleaner import clean_feedback_dataframe
from src.priority_scorer import add_priority_columns
from src.report_generator import generate_markdown_report
from src.utils import REQUIRED_COLUMNS, prepare_input_dataframe


def test_end_to_end_pipeline_generates_expected_columns():
    df = pd.DataFrame(
        [
            {
                "case_id": "CASE-1",
                "user_role": "employee",
                "source": "hr_ai_mvp",
                "raw_feedback": "报销流程怎么走，需要哪些材料？",
                "ai_answer": "请按公司政策执行。",
                "user_rating": 1,
                "expected_behavior": "Provide steps, owner, materials, and timeline.",
                "business_impact": "high",
                "frequency": 5,
                "created_at": "2026-05-01",
            }
        ]
    )
    prepared = prepare_input_dataframe(df)
    cleaned_df, cleaning_summary = clean_feedback_dataframe(prepared)
    classified_df = add_classification_columns(cleaned_df)
    bad_case_df = add_bad_case_columns(classified_df)
    prioritized_df = add_priority_columns(bad_case_df)
    report = generate_markdown_report(prioritized_df, cleaning_summary)

    for column in REQUIRED_COLUMNS:
        assert column in prioritized_df.columns

    assert "primary_issue_category" in prioritized_df.columns
    assert "bad_case_labels" in prioritized_df.columns
    assert "priority_score" in prioritized_df.columns
    assert "Executive Summary" in report
