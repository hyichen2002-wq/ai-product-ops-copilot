from io import BytesIO

import pandas as pd
import pytest

from src.utils import dataframe_to_csv_bytes, load_input_file, prepare_input_dataframe, validate_required_columns


def test_validate_required_columns_returns_missing_fields():
    df = pd.DataFrame({"case_id": ["1"], "raw_feedback": ["hello"]})
    missing = validate_required_columns(df)
    assert "user_role" in missing
    assert "created_at" in missing


def test_prepare_input_dataframe_normalizes_types():
    df = pd.DataFrame(
        [
            {
                "case_id": "A1",
                "user_role": "agent",
                "source": "customer_support",
                "raw_feedback": " test ",
                "ai_answer": None,
                "user_rating": "2",
                "expected_behavior": None,
                "business_impact": "HIGH",
                "frequency": "3",
                "created_at": None,
            }
        ]
    )
    prepared = prepare_input_dataframe(df)
    assert prepared.loc[0, "business_impact"] == "high"
    assert prepared.loc[0, "frequency"] == 3
    assert prepared.loc[0, "created_at"] == "unknown"


def test_prepare_input_dataframe_raises_for_missing_required_column():
    df = pd.DataFrame({"case_id": ["A1"]})
    with pytest.raises(ValueError):
        prepare_input_dataframe(df)


def test_dataframe_to_csv_bytes_uses_utf8_bom_for_excel():
    csv_bytes = dataframe_to_csv_bytes(pd.DataFrame({"raw_feedback": ["中文测试"]}))
    assert csv_bytes.startswith(b"\xef\xbb\xbf")


def test_load_input_file_reads_csv_upload():
    class UploadedFile:
        def __init__(self, name: str, content: bytes):
            self.name = name
            self._content = content

        def getvalue(self):
            return self._content

    csv_content = (
        "case_id,user_role,source,raw_feedback,ai_answer,user_rating,expected_behavior,business_impact,frequency,created_at\n"
        "A1,employee,hr_ai_mvp,测试反馈,请查看系统,2,Provide path,medium,3,2026-05-01\n"
    ).encode("utf-8-sig")
    df, source_name = load_input_file(UploadedFile("sample.csv", csv_content))
    assert source_name == "sample.csv"
    assert df.loc[0, "raw_feedback"] == "测试反馈"


def test_load_input_file_reads_excel_upload():
    class UploadedFile:
        def __init__(self, name: str, content: bytes):
            self.name = name
            self._content = content

        def getvalue(self):
            return self._content

    df = pd.DataFrame(
        [
            {
                "case_id": "A1",
                "user_role": "employee",
                "source": "hr_ai_mvp",
                "raw_feedback": "测试反馈",
                "ai_answer": "请查看系统",
                "user_rating": 2,
                "expected_behavior": "Provide path",
                "business_impact": "medium",
                "frequency": 3,
                "created_at": "2026-05-01",
            }
        ]
    )
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    loaded_df, source_name = load_input_file(UploadedFile("sample.xlsx", buffer.getvalue()))
    assert source_name == "sample.xlsx"
    assert loaded_df.loc[0, "source"] == "hr_ai_mvp"


def test_load_input_file_rejects_missing_columns():
    class UploadedFile:
        def __init__(self, name: str, content: bytes):
            self.name = name
            self._content = content

        def getvalue(self):
            return self._content

    csv_content = "case_id,raw_feedback\nA1,test\n".encode("utf-8")
    with pytest.raises(ValueError, match="Missing required columns"):
        load_input_file(UploadedFile("broken.csv", csv_content))
