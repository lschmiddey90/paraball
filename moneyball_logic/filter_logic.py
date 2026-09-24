import re
import numpy as np
import pandas as pd


def parse_player_positions(pos_string):
    """Parses complex FM position strings like 'DM, M/AM (C)' or 'M (L), AM (LC)'

    into structured tuples: [('DM', ['C']), ('M', ['C']), ('AM', ['C'])].
    """
    if not isinstance(pos_string, str) or not pos_string.strip():
        return []

    parsed_roles = []
    raw_blocks = [b.strip() for b in pos_string.split(",")]

    for block in raw_blocks:
        match = re.match(r"^([A-Z0-9/]+)(?:\s*\(([^)]+)\))?$", block)
        if match:
            roles_raw = match.group(1)
            sides_raw = match.group(2)

            roles = [r.strip() for r in roles_raw.split("/") if r.strip()]

            if sides_raw:
                sides = [
                    c for c in sides_raw.replace("/", "").strip() if c in "RLC"
                ]
            else:
                sides = ["C"]

            for role in roles:
                parsed_roles.append((role, sides))

    return parsed_roles


def matches_position_and_side(pos_string, selected_positions, selected_sides):
    """Returns True if at least one position role matches selected_positions

    AND that specific role satisfies selected_sides.
    """
    parsed_roles = parse_player_positions(pos_string)

    target_sides = set()
    for s in selected_sides:
        if s == "R/L":
            target_sides.update(["R", "L"])
        else:
            target_sides.add(s)

    target_positions = set(selected_positions)

    for role, sides in parsed_roles:
        if role in target_positions:
            if any(s in target_sides for s in sides):
                return True

    return False


def filter_players_by_position(
    df, selected_positions, selected_sides, pos_col="Position"
):
    """Filters DataFrame rows based on position and side matching."""
    if df.empty or pos_col not in df.columns:
        return df

    mask = df[pos_col].apply(
        lambda pos: matches_position_and_side(
            pos, selected_positions, selected_sides
        )
    )
    return df[mask].copy()


def parse_transfer_value_de(val):
    """Parses Football Manager transfer value strings using German locale rules:

    - '.' is treated as thousands separator (e.g., 20.000 -> 20000.0)
    - ',' is treated as decimal point (e.g., 20,5 -> 20.5)
    - Handles ranges ('€10M - €20M' takes lower/min or upper bound)
    - Unpriced / 'Not for sale' returns inf
    """
    if pd.isna(val) or val is None:
        return 0.0

    if isinstance(val, (int, float)):
        return float(val)

    val_str = str(val).strip()

    if not val_str or val_str.lower() in [
        "not for sale",
        "unverkäuflich",
        "uncertain",
        "unknown",
        "n/a",
        "-",
    ]:
        return float("inf")

    # If it's a range (e.g. "€10M - €20M"), take lower bound for min comparison
    if "-" in val_str:
        val_str = val_str.split("-")[0].strip()

    # Determine multiplier
    multiplier = 1.0
    val_upper = val_str.upper()
    if "M" in val_upper:
        multiplier = 1_000_000.0
    elif "K" in val_upper:
        multiplier = 1_000.0

    # Extract numeric parts and delimiters
    clean_str = re.sub(r"[^\d.,]", "", val_str)
    if not clean_str:
        return 0.0

    # German formatting: Remove thousand dots, replace decimal comma with dot
    clean_str = clean_str.replace(".", "").replace(",", ".")

    try:
        return float(clean_str) * multiplier
    except ValueError:
        return float("inf")


def apply_post_scoring_filters(
    scored_df, min_age=None, max_age=None, max_transfer_val=None
):
    """Applies age and transfer budget criteria after scoring."""
    df_out = scored_df.copy()

    # Filter Age
    if "Age" in df_out.columns:
        df_out["Age"] = pd.to_numeric(df_out["Age"], errors="coerce")
        if min_age is not None:
            df_out = df_out[df_out["Age"] >= min_age]
        if max_age is not None:
            df_out = df_out[df_out["Age"] <= max_age]

    # Filter Transfer Value
    if max_transfer_val is not None:
        # Check target columns
        target_col = None
        for col in ["Transfer_Value_Min", "Transfer Value", "Transfer_Value_Max"]:
            if col in df_out.columns:
                target_col = col
                break

        if target_col:
            num_vals = df_out[target_col].apply(parse_transfer_value_de)
            df_out = df_out[(num_vals <= max_transfer_val) | num_vals.isna()]

    return df_out