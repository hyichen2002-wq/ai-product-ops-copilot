from __future__ import annotations

from io import BytesIO, StringIO
import os
from pathlib import Path
from typing import Iterable

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "mock_feedback.csv"
REQUIRED_COLUMNS = [
    "case_id",
    "user_role",
    "source",
    "raw_feedback",
    "ai_answer",
    "user_rating",
    "expected_behavior",
    "business_impact",
    "frequency",
    "created_at",
]

IMPACT_ORDER = {"high": 3, "medium": 2, "low": 1}


def safe_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def validate_required_columns(df: pd.DataFrame) -> list[str]:
    normalized = {str(column).strip() for column in df.columns}
    return [column for column in REQUIRED_COLUMNS if column not in normalized]


def _read_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    decode_errors: list[str] = []
    for encoding in ["utf-8-sig", "utf-8"]:
        try:
            text = file_bytes.decode(encoding)
            return pd.read_csv(StringIO(text))
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")
        except Exception as exc:
            raise ValueError(f"Failed to parse CSV content: {exc}") from exc
    raise ValueError(
        "Unable to decode CSV file with UTF-8 or UTF-8-SIG. Please save the file as UTF-8/UTF-8-SIG and try again."
    )


def load_input_file(uploaded_file, validate_schema: bool = True) -> tuple[pd.DataFrame, str]:
    if uploaded_file is None:
        df = pd.read_csv(DEFAULT_DATA_PATH)
        return df, DEFAULT_DATA_PATH.name

    file_name = uploaded_file.name
    suffix = Path(file_name).suffix.lower()
    file_bytes = uploaded_file.getvalue()

    try:
        if suffix == ".csv":
            df = _read_csv_bytes(file_bytes)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported file format. Please upload a .csv, .xlsx, or .xls file.")
    except ValueError:
        raise
    except ImportError as exc:
        raise ValueError(
            "Excel support is unavailable in the current environment. Please install the required Excel engine and try again."
        ) from exc
    except Exception as exc:
        raise ValueError(f"Failed to read uploaded file: {exc}") from exc

    if validate_schema:
        missing_columns = validate_required_columns(df)
        if missing_columns:
            raise ValueError(
                "Missing required columns: " + ", ".join(missing_columns) + "."
            )

    return df, file_name



def prepare_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working.columns = [str(column).strip() for column in working.columns]

    for column in REQUIRED_COLUMNS:
        if column not in working.columns:
            raise ValueError(f"Missing required column: {column}")

    string_columns = [
        "case_id",
        "user_role",
        "source",
        "raw_feedback",
        "ai_answer",
        "expected_behavior",
        "business_impact",
        "created_at",
    ]
    for column in string_columns:
        working[column] = working[column].apply(safe_text)

    working["user_rating"] = pd.to_numeric(working["user_rating"], errors="coerce").fillna(0).clip(0, 5)
    working["frequency"] = pd.to_numeric(working["frequency"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    working["business_impact"] = (
        working["business_impact"]
        .str.lower()
        .map(lambda value: value if value in IMPACT_ORDER else "medium")
    )
    working["created_at"] = working["created_at"].replace("", pd.NA).fillna("unknown")
    return working



def load_input_dataframe(uploaded_file) -> tuple[pd.DataFrame, str]:
    return load_input_file(uploaded_file, validate_schema=False)


def has_openai_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))



def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")



def split_pipe_labels(value: object) -> list[str]:
    text = safe_text(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]



def top_items(series: pd.Series, limit: int = 5) -> list[tuple[str, int]]:
    counts = series.value_counts().head(limit)
    return [(str(index), int(value)) for index, value in counts.items()]



def format_percent(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.0%"
    return f"{(numerator / denominator) * 100:.1f}%"



def list_to_bullets(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return "- None"
    return "\n".join(f"- {item}" for item in values)
