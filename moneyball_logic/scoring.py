import numpy as np
import pandas as pd
import unicodedata


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
            # Return custom factor if defined, defaulting to 1.0 if factor key is missing
            return float(item.get("factor", 1.0))

    return default_multiplier


def calculate_moneyball_scores(
    filtered_df,
    filtered_df_own_team,
    profile_cfg,
    inverse_metrics,
    config,  # Pass full config or general_config here
):
    df_market = filtered_df.copy()
    df_own = filtered_df_own_team.copy()

    df_market["_is_own_team"] = False
    df_own["_is_own_team"] = True

    # Safely extract league multiplier parameters directly from config
    general_cfg = config.get("general", config)  # Handles both full config dict or general section
    league_cfg = general_cfg.get("league_multipliers", {})
    top_leagues_config = league_cfg.get("top_leagues", [])
    default_league_multiplier = league_cfg.get("default", 0.75)

    # 1. Detect dynamic column casing ('Division' vs 'division', 'Based In' vs 'Based in')
    division_col = next(
        (col for col in df_market.columns if col.lower() == "division"),
        "Division",
    )
    based_in_col = next(
        (col for col in df_market.columns if col.lower() == "based in"),
        "Based In",
    )

    # Combine datasets for uniform percentile ranking
    df_combined = pd.concat([df_market, df_own], ignore_index=False)

    yaml_metrics = profile_cfg.get("metrics", [])
    metric_groups = profile_cfg.get("metric_groups", {})

    individual_metrics = [
        m for m in yaml_metrics if m in df_combined.columns
    ]

    # Percentile Scoring
    individual_score_cols = []
    for metric in individual_metrics:
        df_combined[metric] = pd.to_numeric(
            df_combined[metric], errors="coerce"
        )

        ascending = metric not in inverse_metrics
        pct_rank = df_combined[metric].rank(
            pct=True, ascending=ascending, method="min"
        )

        score_col_name = f"{metric}_score"
        df_combined[score_col_name] = np.ceil(pct_rank * 10) / 10.0
        individual_score_cols.append(score_col_name)

    # Group Scoring
    group_score_cols = []
    group_weights = []

    for group_name, group_data in metric_groups.items():
        if isinstance(group_data, dict):
            group_metrics = group_data.get("metrics", [])
            weight = float(group_data.get("weight", 1.0))
        else:
            group_metrics = group_data
            weight = 1.0

        member_scores = [
            f"{m}_score"
            for m in group_metrics
            if f"{m}_score" in df_combined.columns
        ]

        if member_scores:
            group_col_name = f"Group_{group_name}_Score"
            df_combined[group_col_name] = (
                df_combined[member_scores].mean(axis=1, skipna=True).round(2)
            )
            group_score_cols.append(group_col_name)
            group_weights.append(weight)

    # 3. Apply Multiplier (Strict Exact Match)
    if division_col in df_combined.columns and based_in_col in df_combined.columns:
        df_combined["League_Multiplier"] = df_combined.apply(
            lambda row: _get_league_multiplier(
                row[division_col],
                row[based_in_col],
                top_leagues_config,
                default_league_multiplier,
            ),
            axis=1,
        )
    else:
        df_combined["League_Multiplier"] = default_league_multiplier

    # 4. Final Weighted Score
    if group_score_cols:
        weights_array = np.array(group_weights)
        total_weight = weights_array.sum()
        raw_score = (
            df_combined[group_score_cols].fillna(0).values @ weights_array
        ) / total_weight
    else:
        raw_score = df_combined[individual_score_cols].mean(
            axis=1, skipna=True
        ).fillna(0)

    df_combined["Moneyball_Score"] = (
        raw_score * df_combined["League_Multiplier"]
    ).round(3)

    # 5. Split datasets back
    df_market_out = df_combined[~df_combined["_is_own_team"]].drop(
        columns=["_is_own_team"]
    )
    df_own_out = df_combined[df_combined["_is_own_team"]].drop(
        columns=["_is_own_team"]
    )

    df_market_out = df_market_out.sort_values(
        by="Moneyball_Score", ascending=False
    )
    df_own_out = df_own_out.sort_values(by="Moneyball_Score", ascending=False)

    return df_market_out, df_own_out