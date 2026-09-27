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

    # Filter Transfer Value using pre-cleaned numeric columns
    if max_transfer_val is not None:
        target_col = None
        for col in ["Transfer_Value_Min", "Transfer_Value_Max", "Transfer Value"]:
            if col in df_out.columns:
                target_col = col
                break

        if target_col:
            # Ensure target column is numeric
            transfer_vals = pd.to_numeric(df_out[target_col], errors="coerce")

            # Include players whose minimum transfer value is within budget
            # Exclude unpriced / unknown players (-99 or NaN)
            df_out = df_out[
                (transfer_vals <= max_transfer_val)
            ]

    return df_out