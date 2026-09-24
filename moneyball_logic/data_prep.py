import numpy as np
import pandas as pd


def load_data(file_path):
    """Loads dataset from CSV using UTF-8 encoding and semicolon delimiter."""
    return pd.read_csv(file_path, encoding="utf-8", sep=";")


def clean_numeric_value(val):
    """Strips % symbols, removes thousand-separator periods, replaces European decimal

    commas with dots, and converts to float.
    """
    if pd.isna(val) or val is None:
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)

    val_str = str(val).strip().replace("%", "").strip()

    if not val_str or val_str in ["-", "N/A", "nan", "None"]:
        return np.nan

    # Handle European decimal formatting (e.g. "65,0" -> "65.0" or "1.200,5" -> "1200.5")
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")

    try:
        return float(val_str)
    except ValueError:
        return np.nan


def prepare_dataframe(df, id_columns=None):
    """Prepares and cleans the dataset by converting numeric columns,

    handling European percentage strings, preserving text ID columns,
    and calculating derived metrics (e.g., xGP_perc).
    """
    if df.empty:
        return df

    cleaned_df = df.copy()

    # Known string/text columns to preserve
    default_text_cols = {
        "Player",
        "Position",
        "Division",
        "Club",
        "Nation",
        "Inf",
        "Style",
    }

    if id_columns is not None:
        if isinstance(id_columns, (list, tuple, set)):
            text_columns = set(id_columns).union(default_text_cols)
        else:
            text_columns = {id_columns}.union(default_text_cols)
    else:
        text_columns = default_text_cols

    for col in cleaned_df.columns:
        if col in text_columns:
            continue

        # If column contains text/words rather than numbers, keep it as text
        sample = cleaned_df[col].dropna()
        if not sample.empty and isinstance(sample.iloc[0], str):
            # If the value contains alphabetic characters (and isn't just "N/A" or "-")
            first_val = sample.iloc[0].strip().replace("%", "")
            if any(c.isalpha() for c in first_val) and first_val not in ["N/A", "nan", "None"]:
                text_columns.add(col)
                continue

        cleaned_df[col] = cleaned_df[col].apply(clean_numeric_value)

    # Clean Transfer Values if present
    if "Transfer Value" in cleaned_df.columns:
        if (
            "Transfer_Value_Min" not in cleaned_df.columns
            and "Transfer_Value_Max" not in cleaned_df.columns
        ):
            cleaned_df["Transfer_Value_Min"] = cleaned_df["Transfer Value"]
            cleaned_df["Transfer_Value_Max"] = cleaned_df["Transfer Value"]

    # Calculate xGP_perc metric if both source columns exist
    if "xGP" in cleaned_df.columns and "Goals Conceded" in cleaned_df.columns:
        xgp = pd.to_numeric(cleaned_df["xGP"], errors="coerce")
        gc = pd.to_numeric(cleaned_df["Goals Conceded"], errors="coerce")

        # Replace 0 with NaN for Goals Conceded to avoid division by zero
        gc_safe = gc.replace(0, np.nan)
        cleaned_df["xGP_perc"] = ((xgp + gc) / gc_safe) - 1.0

    return cleaned_df