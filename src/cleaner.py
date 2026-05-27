from __future__ import annotations

import re

import pandas as pd

from .utils import safe_text

PUNCTUATION_MAP = str.maketrans(
    {
        "，": ",",
        "。": ".",
        "；": ";",
        "：": ":",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "？": "?",
        "！": "!",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "、": ",",
        "　": " ",
    }
)



def clean_text(text: object) -> str:
    cleaned = safe_text(text).translate(PUNCTUATION_MAP)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned



def add_cleaned_text_column(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["cleaned_feedback"] = working["raw_feedback"].apply(clean_text)
    return working



def remove_invalid_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    valid_mask = df["cleaned_feedback"].ne("")
    return df.loc[valid_mask].copy(), int((~valid_mask).sum())



def deduplicate_feedback(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    duplicate_mask = df["cleaned_feedback"].duplicated(keep="first")
    return df.loc[~duplicate_mask].copy(), int(duplicate_mask.sum())



def clean_feedback_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    working = add_cleaned_text_column(df)
    original_rows = len(working)
    valid_df, invalid_rows = remove_invalid_rows(working)
    deduplicated_df, duplicate_rows = deduplicate_feedback(valid_df)
    summary = {
        "original_rows": int(original_rows),
        "invalid_rows": int(invalid_rows),
        "duplicate_rows": int(duplicate_rows),
        "cleaned_rows": int(len(deduplicated_df)),
    }
    return deduplicated_df.reset_index(drop=True), summary
