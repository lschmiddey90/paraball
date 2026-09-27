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


def parse_transfer_amount(amount_str):
    """Helper to convert individual transfer amounts like '€8K', '€1.8M', or '€500'

    into numeric floats. Returns -99.0 for non-numeric/unknown values.
    """
    if pd.isna(amount_str) or amount_str is None:
        return -99.0

    val_str = str(amount_str).strip()
    if val_str in ["Not for Sale", "Unknown", "-", "N/A", "nan", "None", ""]:
        return -99.0

    # Strip currency symbols and whitespace
    clean_str = (
        val_str.replace("€", "")
        .replace("£", "")
        .replace("$", "")
        .replace(" ", "")
        .strip()
    )

    # Determine multiplier (K, M, B)
    multiplier = 1.0
    if clean_str.upper().endswith("K"):
        multiplier = 1_000.0
        clean_str = clean_str[:-1]
    elif clean_str.upper().endswith("M"):
        multiplier = 1_000_000.0
        clean_str = clean_str[:-1]
    elif clean_str.upper().endswith("B"):
        multiplier = 1_000_000_000.0
        clean_str = clean_str[:-1]

    # Handle European vs Standard decimals
    if "," in clean_str and "." in clean_str:
        clean_str = clean_str.replace(".", "").replace(",", ".")
    elif "," in clean_str:
        clean_str = clean_str.replace(",", ".")

    try:
        return float(clean_str) * multiplier
    except ValueError:
        return -99.0


def parse_transfer_value_range(val):
    """Splits range strings like '€8K - €75K' into (Min, Max) numeric values.

    Returns (-99.0, -99.0) for 'Not for Sale', 'Unknown', or invalid values.
    """
    if pd.isna(val) or val is None:
        return -99.0, -99.0

    val_str = str(val).strip()

    if val_str in ["Not for Sale", "Unknown", "-", "N/A", "nan", "None", ""]:
        return -99.0, -99.0

    # Handle range separated by '-' or ' - '
    if " - " in val_str:
        parts = val_str.split(" - ")
        return parse_transfer_amount(parts[0]), parse_transfer_amount(
            parts[1]
        )
    elif "-" in val_str and not val_str.startswith("-"):
        parts = val_str.split("-")
        if len(parts) == 2:
            return parse_transfer_amount(parts[0]), parse_transfer_amount(
                parts[1]
            )

    # Single value case (e.g., '€1.2M')
    parsed_single = parse_transfer_amount(val_str)
    return parsed_single, parsed_single


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
        "Transfer Value",  # Keep raw text column unparsed in text list
    }

    if id_columns is not None:
        if isinstance(id_columns, (list, tuple, set)):
            text_columns = set(id_columns).union(default_text_cols)
        else:
            text_columns = {id_columns}.union(default_text_cols)
    else:
        text_columns = default_text_cols

    # Parse Transfer Values into numerical Min and Max columns
    if "Transfer Value" in cleaned_df.columns:
        parsed_ranges = cleaned_df["Transfer Value"].apply(
            parse_transfer_value_range
        )
        cleaned_df["Transfer_Value_Min"] = [r[0] for r in parsed_ranges]
        cleaned_df["Transfer_Value_Max"] = [r[1] for r in parsed_ranges]

    for col in cleaned_df.columns:
        if col in text_columns or col in [
            "Transfer_Value_Min",
            "Transfer_Value_Max",
        ]:
            continue

        # If column contains text/words rather than numbers, keep it as text
        sample = cleaned_df[col].dropna()
        if not sample.empty and isinstance(sample.iloc[0], str):
            first_val = sample.iloc[0].strip().replace("%", "")
            if any(
                c.isalpha() for c in first_val
            ) and first_val not in ["N/A", "nan", "None"]:
                text_columns.add(col)
                continue

        cleaned_df[col] = cleaned_df[col].apply(clean_numeric_value)

    # Calculate xGP_perc metric if both source columns exist
    if "xGP" in cleaned_df.columns and "Goals Conceded" in cleaned_df.columns:
        xgp = pd.to_numeric(cleaned_df["xGP"], errors="coerce")
        gc = pd.to_numeric(cleaned_df["Goals Conceded"], errors="coerce")

        gc_safe = gc.replace(0, np.nan)
        cleaned_df["xGP_perc"] = ((xgp + gc) / gc_safe) - 1.0

    return cleaned_df