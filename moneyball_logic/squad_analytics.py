import unicodedata
import pandas as pd
import numpy as np
from .filter_logic import filter_players_by_position

def normalize_metrics_0_to_1(
    df_base, df_own_base=None, target_metrics=None, exclude_columns=None
):
    """Normalizes numerical metric columns strictly between 0.0 and 1.0 using Min-Max scaling.

    Fits min/max bounds on df_base and applies them safely to df_own_base.
    """
    df_base_norm = df_base.copy()
    df_own_norm = df_own_base.copy() if df_own_base is not None else None

    # Default metadata/ID columns to NEVER scale
    default_excludes = {
        "Player",
        "Position",
        "Division",
        "Club",
        "Nation",
        "Inf",
        "Style",
        "Age",
        "Transfer Value",
        "Transfer_Value_Min",
        "Transfer_Value_Max",
        "Based In",
        "Minutes Played",
        "Mins",
        "Min",
        "_rank_score",
    }

    if exclude_columns is not None:
        if isinstance(exclude_columns, (list, tuple, set)):
            default_excludes.update(exclude_columns)
        else:
            default_excludes.add(exclude_columns)

    # Determine which columns to normalize
    if target_metrics is not None:
        # Normalize ONLY the specified target metrics
        cols_to_scale = [
            c
            for c in target_metrics
            if c in df_base_norm.columns and c not in default_excludes
        ]
    else:
        # Fallback: Normalize all numeric columns that aren't excluded
        cols_to_scale = [
            c
            for c in df_base_norm.select_dtypes(
                include=[np.number]
            ).columns
            if c not in default_excludes
        ]

    for col in cols_to_scale:
        min_val = df_base_norm[col].min()
        max_val = df_base_norm[col].max()

        # Safely handle min/max scaling
        if pd.notna(min_val) and pd.notna(max_val) and max_val > min_val:
            # 1. Transform df_base
            df_base_norm[col] = (df_base_norm[col] - min_val) / (
                max_val - min_val
            )

            # 2. Transform df_own_base using exact df_base bounds
            if df_own_norm is not None and col in df_own_norm.columns:
                df_own_norm[col] = (df_own_norm[col] - min_val) / (
                    max_val - min_val
                )
                # Clip values to [0.0, 1.0] in case own-team stats exceed market max/min
                df_own_norm[col] = df_own_norm[col].clip(0.0, 1.0)
        else:
            # Avoid divide-by-zero or NaN issues if min == max
            df_base_norm[col] = 1.0
            if df_own_norm is not None and col in df_own_norm.columns:
                df_own_norm[col] = 1.0

    return df_base_norm, df_own_norm

def _clean_str(val):
    if not isinstance(val, (str, bytes)) or pd.isna(val):
        return ""
    val = unicodedata.normalize("NFKD", str(val))
    val = val.replace("\xa0", " ")
    return " ".join(val.split()).lower()


def _get_league_multiplier(
    division_name, country_name, top_leagues_config, default_multiplier
):
    div_clean = _clean_str(division_name)
    country_clean = _clean_str(country_name)

    if not div_clean or not country_clean:
        return default_multiplier

    if isinstance(top_leagues_config, dict):
        top_leagues_config = top_leagues_config.get("top_leagues", [])

    if not isinstance(top_leagues_config, list):
        return default_multiplier

    for item in top_leagues_config:
        if not isinstance(item, dict):
            continue

        cfg_league = _clean_str(str(item.get("league", "")))
        cfg_country = _clean_str(str(item.get("country", "")))

        if cfg_league == div_clean and cfg_country == country_clean:
            return 1.0

    return default_multiplier


def apply_league_normalization(
    df, metrics, top_leagues_config, default_multiplier=0.75
):
    """Multipliziert metrische Spalten mit dem jeweiligen Liga-Multiplikator."""
    if df.empty:
        return df.copy()

    df_norm = df.copy()
    multipliers = df_norm.apply(
        lambda r: _get_league_multiplier(
            r.get("Division", ""),
            r.get("Based In", ""),
            top_leagues_config,
            default_multiplier,
        ),
        axis=1,
    )

    for m in metrics:
        if m in df_norm.columns:
            df_norm[m] = pd.to_numeric(df_norm[m], errors="coerce").fillna(0) * multipliers

    return df_norm

def calculate_position_benchmarks(
    df_comparison,
    pos_config,
    top_leagues_config,
    default_multiplier=0.75,
    top_n=20,
    inverse_metrics=None,
):
    if inverse_metrics is None:
        inverse_metrics = ["Possession Lost per 90"]

    benchmarks = {}

    for role_key, role_cfg in pos_config.items():
        positions = role_cfg.get("positions", [])
        sides = role_cfg.get("sides", [])
        metrics = role_cfg.get("metrics", [])

        pos_df = filter_players_by_position(df_comparison, positions, sides)
        if pos_df.empty or not metrics:
            continue

        valid_metrics = [m for m in metrics if m in pos_df.columns]
        if not valid_metrics:
            continue

        pos_df_norm = apply_league_normalization(
            pos_df, valid_metrics, top_leagues_config, default_multiplier
        )

        role_benchmarks = {}

        for metric in valid_metrics:
            is_inverse = metric in inverse_metrics
            
            if is_inverse:
                # Lowest 20 players have the best score for inverse metrics
                top_metric_df = pos_df_norm.nsmallest(top_n, metric)
                raw_mean = top_metric_df[metric].mean()
                # Invert so 1.0 = best possible score
                role_benchmarks[metric] = 1.0 - raw_mean
            else:
                top_metric_df = pos_df_norm.nlargest(top_n, metric)
                role_benchmarks[metric] = top_metric_df[metric].mean()

        benchmarks[role_key] = role_benchmarks

    return benchmarks