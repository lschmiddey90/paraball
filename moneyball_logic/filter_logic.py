import re
import numpy as np
import pandas as pd


SQUAD_POSITION_GROUPS = {
    "GK": (["GK"], ["C"]),
    "D(C)": (["D"], ["C"]),
    "[D, WB](R/L)": (["D", "WB"], ["R/L"]),
    "[DM/M](C)": (["DM", "M"], ["C"]),
    "[M/AM](C)": (["M", "AM"], ["C"]),
    "[M, AM](R/L)": (["M", "AM"], ["R/L"]),
    "ST(C)": (["ST"], ["C"]),
}


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


def calculate_personality_averages(df_squad, config):
    """Calculates average personality score across all players and per position group.

    Adds 'Personality_Value' directly to df_squad based on config mappings.
    If a player fits multiple position groups, they are included in each matching group.
    """
    personality_dict = config.get("general", {}).get("personalities", {})

    # Add Personality_Value column directly to df_squad
    df_squad["Personality_Value"] = df_squad["Personality"].map(
        personality_dict
    )

    # Filter out rows without a valid personality mapping for calculations
    valid_df = df_squad.dropna(subset=["Personality_Value"])

    # 1. Overall average
    all_avg = valid_df["Personality_Value"].mean()
    averages = {"All": float(all_avg) if not np.isnan(all_avg) else 0.0}

    # 2. Average per Squad Position Group
    for group_name, (roles, sides) in SQUAD_POSITION_GROUPS.items():
        mask = valid_df["Best Pos"].apply(
            lambda pos_str: matches_position_and_side(pos_str, roles, sides)
        )
        group_players = valid_df[mask]

        if len(group_players) > 0:
            averages[group_name] = float(
                group_players["Personality_Value"].mean()
            )
        else:
            averages[group_name] = np.nan

    return averages


def filter_players_by_position(
    df, selected_positions, selected_sides, pos_col="Best Pos"
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


def filter_by_min_minutes(df, min_minutes, minutes_col="Minutes", label="players"):
    """Keeps only players with at least `min_minutes` played.

    Players without a minutes value are dropped. If the column is missing,
    the DataFrame is returned unchanged and a warning is printed.
    """
    if min_minutes is None or df.empty:
        return df
    if minutes_col not in df.columns:
        print(
            f"[Warning] '{minutes_col}' column not found - minimum minutes filter "
            f"NOT applied to {label}. Add '{minutes_col}' to the export."
        )
        return df

    minutes = pd.to_numeric(df[minutes_col], errors="coerce")
    df_out = df[minutes >= min_minutes].copy()
    print(
        f"Minimum minutes filter (>= {min_minutes}) on {label}: "
        f"{len(df_out)} of {len(df)} kept"
    )
    return df_out


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

            # Include players whose minimum transfer value is within budget.
            # Unpriced players ("Unknown" / "Not for Sale" -> -99) are kept on purpose.
            df_out = df_out[
                (transfer_vals <= max_transfer_val)
            ]

    return df_out