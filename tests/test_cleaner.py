import pandas as pd

from src.cleaner import clean_feedback_dataframe, clean_text



def test_clean_text_normalizes_spaces_and_punctuation():
    assert clean_text("  请假流程  怎么走？  ") == "请假流程 怎么走?"



def test_clean_feedback_dataframe_removes_invalid_and_duplicate_rows():
    df = pd.DataFrame(
        [
            {"raw_feedback": "Need refund steps"},
            {"raw_feedback": "Need refund steps"},
            {"raw_feedback": "   "},
        ]
    )
    cleaned_df, summary = clean_feedback_dataframe(df)
    assert summary["invalid_rows"] == 1
    assert summary["duplicate_rows"] == 1
    assert summary["cleaned_rows"] == 1
    assert cleaned_df.iloc[0]["cleaned_feedback"] == "Need refund steps"
