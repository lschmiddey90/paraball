import numpy as np
import pandas as pd

from .filter_logic import filter_players_by_position


def _get_group_metrics_and_weights(role_cfg):
    """Extracts unique metrics and group weightings from metric_groups configuration."""
    metric_groups = role_cfg.get("metric_groups", {})
    if not metric_groups:
        return {}, []

    all_metrics = set()
    parsed_groups = {}

    for group_name, group_info in metric_groups.items():
        weight = float(group_info.get("weight", 1.0))
        metrics = group_info.get("metrics", [])
        parsed_groups[group_name] = {"weight": weight, "metrics": metrics}
        all_metrics.update(metrics)

    return parsed_groups, list(all_metrics)


def calculate_player_profile_scores(
    df_base,
    df_own_base,
    config,
    inverse_metrics=None,
):
    """Calculates weighted Moneyball Scores (0.0 to 1.0) for every player across
    applicable positional profiles based on metric percentiles from df_base
    without applying league multipliers.
    """
    if inverse_metrics is None:
        inverse_metrics = ["Possession Lost per 90"]

    general_config = config.get("general", {})
    pos_config = config.get("positions", {})

    id_cols = general_config.get(
        "id_columns",
        ["Player", "Position", "Age", "Transfer Value", "Division", "Based In"],
    )

    all_profile_results = []

    for role_key, role_cfg in pos_config.items():
        parsed_groups, required_metrics = _get_group_metrics_and_weights(role_cfg)
        if not parsed_groups or not required_metrics:
            continue

        positions = role_cfg.get("positions", [])
        sides = role_cfg.get("sides", [])

        # Filter market (df_base) and squad (df_own_base) for current position
        base_pos_df = filter_players_by_position(df_base, positions, sides).copy()
        own_pos_df = filter_players_by_position(df_own_base, positions, sides).copy()

        if base_pos_df.empty:
            continue

        # Keep only metrics present in df_base
        valid_metrics = [m for m in required_metrics if m in base_pos_df.columns]
        if not valid_metrics:
            continue

        # Tag source provenance
        base_pos_df["_Source"] = "Market"
        own_pos_df["_Source"] = "Own Squad"

        # Combine datasets directly without league normalization
        combined_df = pd.concat([base_pos_df, own_pos_df], ignore_index=True)

        if combined_df.empty:
            continue

        # 1. Invert inverse metrics on COMBINED dataset
        for inv_m in inverse_metrics:
            if inv_m in valid_metrics:
                max_val = combined_df[inv_m].max()
                combined_df[inv_m] = max_val - combined_df[inv_m]

        # 2. Calculate Percentiles against 'Market' Baseline inside combined_df
        market_mask = combined_df["_Source"] == "Market"
        percentile_df = pd.DataFrame(index=combined_df.index)

        for m in valid_metrics:
            # Baseline market distribution
            market_distribution = combined_df.loc[market_mask, m].dropna().to_numpy(dtype=float)

            if len(market_distribution) == 0:
                percentile_df[m] = 0.5
                continue

            # Compute relative percentile for EVERY player against market distribution
            player_vals = combined_df[m].to_numpy(dtype=float)

            # Vectorized percentile rank (Percentage of market values <= player value)
            ranks = np.array([
                np.sum(market_distribution <= val) / len(market_distribution)
                if not np.isnan(val) else 0.0
                for val in player_vals
            ])
            percentile_df[m] = ranks

        # 3. Calculate Weighted Metric Group Scores
        total_role_weight = sum(g["weight"] for g in parsed_groups.values())
        final_role_score = np.zeros(len(combined_df))

        for group_name, group_data in parsed_groups.items():
            g_weight = group_data["weight"]
            g_metrics = [m for m in group_data["metrics"] if m in valid_metrics]

            if not g_metrics:
                continue

            # Average percentiles within group
            group_avg = percentile_df[g_metrics].mean(axis=1)

            # Store individual group score on combined DataFrame
            combined_df[f"Group_{group_name}"] = group_avg

            # Add weighted contribution to final score
            final_role_score += group_avg * (g_weight / total_role_weight)

        # 4. Format output records for this profile
        combined_df["Profile"] = role_key
        combined_df["Moneyball_Score"] = np.round(final_role_score, 4)

        display_cols = [
            c for c in id_cols if c in combined_df.columns
        ] + [
            "Profile",
            "Moneyball_Score",
            "_Source",
        ]
        group_cols = [
            c for c in combined_df.columns if c.startswith("Group_")
        ]

        result_sub_df = combined_df[display_cols + group_cols].copy()
        all_profile_results.append(result_sub_df)

    if not all_profile_results:
        return pd.DataFrame()

    # Consolidate into single final shortlist table
    final_df = pd.concat(all_profile_results, ignore_index=True)
    return final_df.sort_values(
        by=["Profile", "Moneyball_Score"], ascending=[True, False]
    ).reset_index(drop=True)