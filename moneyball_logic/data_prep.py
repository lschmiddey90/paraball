import numpy as np
import pandas as pd


def load_data(file_path):
    """Loads dataset from CSV using UTF-8 encoding and semicolon delimiter."""
    return pd.read_csv(file_path, encoding="utf-8", sep=",")


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


import numpy as np
import pandas as pd


def prepare_dataframe(df, id_columns=None):
    """Prepares and cleans the dataset by converting numeric columns,

    handling European percentage strings, preserving text ID columns,
    and calculating derived metrics.
    """
    if df.empty:
        return df

    cleaned_df = df.copy()

    # Known string/text columns to preserve
    default_text_cols = {
        "Player",
        "Best Pos",
        "Division",
        "Club",
        "Nation",
        "Inf",
        "Style",
        "Based In",
        "Preferred Foot",
        "Personality",
        "Transfer Value",
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

    # Clean numeric values across columns
    for col in cleaned_df.columns:
        if col in text_columns or col in [
            "Transfer_Value_Min",
            "Transfer_Value_Max",
        ]:
            continue

        sample = cleaned_df[col].dropna()
        if not sample.empty and isinstance(sample.iloc[0], str):
            first_val = sample.iloc[0].strip().replace("%", "")
            if any(
                c.isalpha() for c in first_val
            ) and first_val not in ["N/A", "nan", "None"]:
                text_columns.add(col)
                continue

        cleaned_df[col] = cleaned_df[col].apply(clean_numeric_value)

    # Helper function for safe numeric series retrieval
    def get_num(col_name):
        if col_name in cleaned_df.columns:
            return pd.to_numeric(cleaned_df[col_name], errors="coerce")
        return None

    # 1. xGP_perc metric
    xgp = get_num("xGP")
    gc = get_num("Goals Conceded")
    if xgp is not None and gc is not None:
        gc_safe = gc.replace(0, np.nan)
        cleaned_df["xGP_perc"] = ((xgp + gc) / gc_safe) - 1.0

    # 2. Key Passes % & Progressive Passes %
    passes_att = get_num("Passes Attempted")
    if passes_att is not None:
        passes_att_safe = passes_att.replace(0, np.nan)

        key_passes = get_num("Key Passes")
        if key_passes is not None:
            cleaned_df["Key_Passes_perc"] = (
                key_passes / passes_att_safe
            )

        psp = get_num("PsP")
        if psp is not None:
            cleaned_df["PsP_perc"] = (psp / passes_att_safe)

    # 3. xG/shot Fallback Calculation
    shot_p90 = get_num("Shot/90")
    xg_p90 = get_num("xG/90")
    if "xG/shot" not in cleaned_df.columns and xg_p90 is not None and shot_p90 is not None:
        shot_p90_safe = shot_p90.replace(0, np.nan)
        cleaned_df["xG/shot"] = xg_p90 / shot_p90_safe

    # 4. xG Overperformance/90
    goals_p90 = get_num("Goals per 90 minutes")
    if goals_p90 is not None and xg_p90 is not None:
        cleaned_df["xG_Overperformance_per_90"] = goals_p90 - xg_p90

    # 5. Goal Contributions & Goal Contributions/90
    goals = get_num("Goals")
    assists = get_num("Assists")
    if goals is not None and assists is not None:
        cleaned_df["Goal_Contributions"] = goals + assists

    asts_p90 = get_num("Asts/90")
    if goals_p90 is not None and asts_p90 is not None:
        cleaned_df["Goal_Contributions_per_90"] = goals_p90 + asts_p90

    # 6. Pressure Success %
    pres_a = get_num("Pres A")
    pres_c = get_num("Pres C")
    if pres_a is not None and pres_c is not None:
        pres_a_safe = pres_a.replace(0, np.nan)
        cleaned_df["Pressure_Success_perc"] = (pres_c / pres_a_safe)

    # 7. Poss+-/90 & Poss+- %
    poss_won_p90 = get_num("Possession Won per 90")
    poss_lost_p90 = get_num("Possession Lost per 90")
    if poss_won_p90 is not None and poss_lost_p90 is not None:
        cleaned_df["Poss_Net_per_90"] = poss_won_p90 - poss_lost_p90

        total_poss_actions = (poss_won_p90 + poss_lost_p90).replace(0, np.nan)
        cleaned_df["Poss_Win_perc"] = (
            poss_won_p90 / total_poss_actions
        )

    return cleaned_df