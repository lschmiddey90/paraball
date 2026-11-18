import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker
import matplotlib.patches as patches
from matplotlib.patches import Patch
import seaborn as sns

from .filter_logic import (
    SQUAD_POSITION_GROUPS,
    filter_players_by_position,
    matches_position_and_side,
)

def plot_age_distribution_squad(df, figsize=(15, 12)):
    """Erstellt ein Alters-Histogramm über alle Spieler im Kader

    sowie Subplots für die einzelnen Positionsgruppen.
    y-Achsen zeigen ausschließlich ganze Zahlen.
    """
    if df.empty or "Age" not in df.columns:
        raise ValueError("DataFrame ist leer oder enthält keine 'Age'-Spalte.")

    sns.set_theme(style="whitegrid")

    num_positions = len(SQUAD_POSITION_GROUPS)
    num_rows = math.ceil(num_positions / 2) + 1

    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(num_rows, 2)

    # 1. Haupt-Histogramm (Gesamter Kader)
    ax_total = fig.add_subplot(gs[0, :])
    sns.histplot(
        data=df,
        x="Age",
        kde=True,
        discrete=True,
        ax=ax_total,
        color="#2b5c8f",
        alpha=0.6,
    )

    mean_age_total = df["Age"].mean()
    ax_total.axvline(
        mean_age_total,
        color="#d9534f",
        linestyle="--",
        linewidth=2,
        label=f"Ø-Alter: {mean_age_total:.1f} Jahre",
    )

    ax_total.set_title(
        f"Gesamter Kader (n = {len(df)})", fontsize=14, fontweight="bold", pad=10
    )
    ax_total.set_xlabel("Alter", fontsize=11)
    ax_total.set_ylabel("Anzahl Spieler", fontsize=11)
    ax_total.legend(loc="upper right", frameon=True)
    
    # y-Achse auf ganze Zahlen erzwingen
    ax_total.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # 2. Subplots je Positionsgruppe
    for idx, (group_name, (roles, sides)) in enumerate(
        SQUAD_POSITION_GROUPS.items()
    ):
        row = (idx // 2) + 1
        col = idx % 2
        ax = fig.add_subplot(gs[row, col])

        pos_df = filter_players_by_position(df, roles, sides)

        if not pos_df.empty:
            sns.histplot(
                data=pos_df,
                x="Age",
                kde=True,
                discrete=True,
                ax=ax,
                color="#36b55c",
                alpha=0.6,
            )

            mean_age_pos = pos_df["Age"].mean()
            ax.axvline(
                mean_age_pos,
                color="#d9534f",
                linestyle="--",
                linewidth=1.5,
                label=f"Ø {mean_age_pos:.1f}",
            )
            ax.legend(loc="upper right", frameon=True)
        else:
            ax.text(
                0.5,
                0.5,
                "Keine Spieler",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color="gray",
            )

        ax.set_title(
            f"{group_name} (n = {len(pos_df)})", fontsize=12, fontweight="bold"
        )
        ax.set_xlabel("Alter", fontsize=10)
        ax.set_ylabel("Anzahl", fontsize=10)
        
        # y-Achse auf ganze Zahlen erzwingen
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.suptitle(
        "Squad Age Profiling — FM26", fontsize=16, fontweight="bold", y=1.02
    )

    return fig

def plot_style_distribution_squad(df, figsize=(15, 14)):
    """Erstellt ein Bar-Chart über die Verteilung der Spielstile (Style) im Kader

    sowie Subplots für jede Positionsgruppe.
    """
    if df.empty or "Style" not in df.columns:
        raise ValueError("DataFrame ist leer oder enthält keine 'Style'-Spalte.")

    sns.set_theme(style="whitegrid")

    # Einheitliche Sortierung & Farbpalette für Styles definieren
    style_counts = df["Style"].value_counts()
    style_order = style_counts.index.tolist()
    palette = sns.color_palette("tab10", n_colors=len(style_order))
    color_map = dict(zip(style_order, palette))

    num_positions = len(SQUAD_POSITION_GROUPS)
    num_rows = math.ceil(num_positions / 2) + 1

    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(num_rows, 2)

    # 1. Haupt-Barchart (Gesamter Kader)
    ax_total = fig.add_subplot(gs[0, :])
    sns.countplot(
        data=df,
        y="Style",
        hue="Style",
        order=style_order,
        palette=color_map,
        legend=False,
        ax=ax_total,
        alpha=0.85,
    )

    ax_total.set_title(
        f"Gesamter Kader — Style-Verteilung (n = {len(df)})",
        fontsize=14,
        fontweight="bold",
        pad=10,
    )
    ax_total.set_xlabel("Anzahl Spieler", fontsize=11)
    ax_total.set_ylabel("Style", fontsize=11)
    ax_total.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Werte-Labels auf den Balken des Haupt-Charts anzeigen
    for p in ax_total.patches:
        width = p.get_width()
        if width > 0:
            ax_total.annotate(
                f"{int(width)}",
                (width, p.get_y() + p.get_height() / 2.0),
                ha="left",
                va="center",
                xytext=(5, 0),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
            )

    # 2. Subplots je Positionsgruppe
    for idx, (group_name, (roles, sides)) in enumerate(
        SQUAD_POSITION_GROUPS.items()
    ):
        row = (idx // 2) + 1
        col = idx % 2
        ax = fig.add_subplot(gs[row, col])

        pos_df = filter_players_by_position(df, roles, sides)

        if not pos_df.empty and pos_df["Style"].notna().any():
            sns.countplot(
                data=pos_df,
                y="Style",
                hue="Style",
                order=style_order,
                palette=color_map,
                legend=False,
                ax=ax,
                alpha=0.85,
            )

            # Werte-Labels auf den Balken im Subplot
            for p in ax.patches:
                width = p.get_width()
                if width > 0:
                    ax.annotate(
                        f"{int(width)}",
                        (width, p.get_y() + p.get_height() / 2.0),
                        ha="left",
                        va="center",
                        xytext=(4, 0),
                        textcoords="offset points",
                        fontsize=9,
                    )
        else:
            ax.text(
                0.5,
                0.5,
                "Keine Spieler",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color="gray",
            )

        ax.set_title(
            f"{group_name} (n = {len(pos_df)})", fontsize=12, fontweight="bold"
        )
        ax.set_xlabel("Anzahl", fontsize=10)
        ax.set_ylabel("Style", fontsize=10)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.suptitle(
        "Squad Style Profiling — FM26", fontsize=16, fontweight="bold", y=1.02
    )

    return fig

def _ratio_to_benchmark(player_val, bench_val, is_inverse):
    """Player value relative to the benchmark (1.0 = Top 20 average), higher = better.

    Player values are 0..1 normalized. For inverse metrics the player value is
    flipped (1 - x); the benchmark is already pre-inverted in
    calculate_position_benchmarks, so it is used as is.
    """
    p_score = (1.0 - player_val) if is_inverse else player_val
    return p_score / max(bench_val, 0.01)


def plot_player_vs_benchmark_spider(
    player_row,
    role_name,
    role_metrics,
    role_benchmark,
    inverse_metrics=None,
    figsize=(8, 8),
):
    """Renders a radar chart comparing a single player against the precalculated benchmark."""
    if inverse_metrics is None:
        inverse_metrics = ["Possession Lost per 90", "MLG"]

    valid_metrics = [
        m for m in role_metrics if m in player_row.index and m in role_benchmark
    ]
    num_metrics = len(valid_metrics)

    if num_metrics < 3:
        return None

    raw_player_vals = [float(player_row.get(m, 0)) for m in valid_metrics]
    raw_bench_vals = [float(role_benchmark[m]) for m in valid_metrics]

    norm_player_vals = []
    norm_bench_vals = []
    display_labels = []

    # Prepare values so that larger area = better performance
    for m, p_val, b_val in zip(valid_metrics, raw_player_vals, raw_bench_vals):
        is_inverse = m in inverse_metrics
        display_labels.append(f"{m}\n(Inv)" if is_inverse else m)

        norm_player_vals.append(_ratio_to_benchmark(p_val, b_val, is_inverse))
        norm_bench_vals.append(1.0)

    # Close the polar plot loop
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    norm_player_vals += norm_player_vals[:1]
    norm_bench_vals += norm_bench_vals[:1]
    angles += angles[:1]

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # Plot Benchmark baseline (1.0 = Top 20 Average)
    ax.plot(
        angles,
        norm_bench_vals,
        color="#888888",
        linewidth=2,
        linestyle="--",
        label="Top 20 Avg (Base 1.0)",
    )
    ax.fill(angles, norm_bench_vals, color="#888888", alpha=0.15)

    # Plot Player performance
    player_name = player_row.get("Player", "Unknown")
    minutes = player_row.get("Minutes", 0)

    ax.plot(
        angles,
        norm_player_vals,
        color="#2b5c8f",
        linewidth=2.5,
        label=f"{player_name}",
    )
    ax.fill(angles, norm_player_vals, color="#2b5c8f", alpha=0.35)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(display_labels, fontsize=8)

    ax.set_title(
        f"{player_name} — Profile: {role_name}\nMinutes Played: {int(minutes)}",
        fontsize=13,
        fontweight="bold",
        pad=25,
    )
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), frameon=True)

    return fig


def plot_top_players_per_profile_seaborn(
    shortlist_df,
    config,
    top_n=15,
    own_squad_color="#2b5c8f",  # Highlight color for your squad
    market_color="#b0bec5",  # Muted color for market targets
    badge_bg_color="#eef3f8",  # Background for percentile badges
    save_path_prefix=None,
):
    """Generates horizontal Seaborn bar charts per Profile:

    Top N candidates on top, followed by a separate bar chart of all Own Squad
    players for that profile below, annotated with their overall profile
    percentile.
    """
    if shortlist_df.empty or "Profile" not in shortlist_df.columns:
        print(
            "Provided shortlist DataFrame is empty or missing 'Profile'"
            " column."
        )
        return {}

    configured_profiles = list(config.get("positions", {}).keys())
    existing_profiles = shortlist_df["Profile"].unique()

    profile_order = [p for p in configured_profiles if p in existing_profiles]
    for p in existing_profiles:
        if p not in profile_order:
            profile_order.append(p)

    sns.set_theme(style="whitegrid")
    figures = {}

    for profile_name in profile_order:
        group = shortlist_df[shortlist_df["Profile"] == profile_name].copy()

        # "Top X%" within this profile cohort: best player -> smallest X
        group["Percentile"] = (
            group["Moneyball_Score"].rank(pct=True, ascending=False, method="min")
            * 100
        )

        top_players = (
            group.sort_values(by="Moneyball_Score", ascending=False)
            .head(top_n)
            .copy()
        )
        own_squad_players = (
            group[group["_Source"] == "Own Squad"]
            .sort_values(by="Moneyball_Score", ascending=False)
            .copy()
        )

        n_top = len(top_players)
        n_own = len(own_squad_players)

        if n_top == 0 and n_own == 0:
            continue

        total_rows = n_top + (n_own if n_own > 0 else 0)
        fig_height = max(5.0, total_rows * 0.48 + 1.5)

        if n_own > 0:
            fig, (ax_top, ax_own) = plt.subplots(
                nrows=2,
                ncols=1,
                figsize=(10, fig_height),
                gridspec_kw={"height_ratios": [n_top, max(1, n_own)]},
            )
        else:
            fig, ax_top = plt.subplots(figsize=(10, max(3.5, n_top * 0.45)))
            ax_own = None

        # --- Top Subplot: Top Candidates ---
        palette_top = {
            row["Player"]: (
                own_squad_color if row["_Source"] == "Own Squad" else market_color
            )
            for _, row in top_players.iterrows()
        }

        barplot_top = sns.barplot(
            data=top_players,
            x="Moneyball_Score",
            y="Player",
            hue="Player",  # Expressly assign hue to clear warning
            palette=palette_top,
            legend=False,
            ax=ax_top,
        )

        for p in barplot_top.patches:
            width = p.get_width()
            if width > 0:
                ax_top.annotate(
                    f"{width:.4f}",
                    (width, p.get_y() + p.get_height() / 2.0),
                    ha="left",
                    va="center",
                    xytext=(6, 0),
                    textcoords="offset points",
                    fontsize=9,
                    fontweight="bold",
                    color="#333333",
                )

        ax_top.set_title(
            f"Top {n_top} Candidates — Profile: {profile_name}",
            fontsize=13,
            pad=12,
            fontweight="bold",
        )
        ax_top.set_xlabel("" if ax_own else "Moneyball Score", fontsize=10)
        ax_top.set_ylabel("Player", fontsize=10)
        ax_top.set_xlim(0, 1.25)
        sns.despine(ax=ax_top, left=True, bottom=True)

        legend_elements = [
            Patch(facecolor=own_squad_color, label="Own Squad"),
            Patch(facecolor=market_color, label="Market"),
        ]
        ax_top.legend(
            handles=legend_elements,
            title="Source",
            loc="lower right",
            frameon=True,
        )

        # --- Bottom Subplot: Own Squad Players ---
        if ax_own is not None and n_own > 0:
            palette_own = {
                row["Player"]: own_squad_color
                for _, row in own_squad_players.iterrows()
            }

            barplot_own = sns.barplot(
                data=own_squad_players,
                x="Moneyball_Score",
                y="Player",
                hue="Player",  # Expressly assign hue to clear warning
                palette=palette_own,
                legend=False,
                ax=ax_own,
            )

            # Annotate score AND percentile rank badge
            for idx, p in enumerate(barplot_own.patches):
                width = p.get_width()
                if width > 0 and idx < len(own_squad_players):
                    row = own_squad_players.iloc[idx]
                    pct_val = row["Percentile"]

                    # Display score + Percentile badge
                    text_label = f"{width:.4f}   "
                    badge_label = f" Top {pct_val:.0f}% "

                    y_pos = p.get_y() + p.get_height() / 2.0

                    # 1. Score Text
                    ax_own.annotate(
                        text_label,
                        (width, y_pos),
                        ha="left",
                        va="center",
                        xytext=(6, 0),
                        textcoords="offset points",
                        fontsize=9,
                        fontweight="bold",
                        color="#333333",
                    )

                    # 2. Percentile Badge Box
                    ax_own.annotate(
                        badge_label,
                        (width, y_pos),
                        ha="left",
                        va="center",
                        xytext=(62, 0),
                        textcoords="offset points",
                        fontsize=8.5,
                        fontweight="bold",
                        color=own_squad_color,
                        bbox=dict(
                            boxstyle="round,pad=0.3",
                            fc=badge_bg_color,
                            ec=own_squad_color,
                            lw=1,
                        ),
                    )

            ax_own.set_title(
                f"Own Squad Players — Profile: {profile_name}",
                fontsize=11,
                pad=10,
                fontweight="bold",
            )
            ax_own.set_xlabel("Moneyball Score", fontsize=10, labelpad=8)
            ax_own.set_ylabel("Player", fontsize=10)
            ax_own.set_xlim(0, 1.25)
            sns.despine(ax=ax_own, left=True, bottom=True)

        plt.tight_layout()

        if save_path_prefix:
            plt.savefig(
                f"{save_path_prefix}_{profile_name}.png",
                dpi=300,
                bbox_inches="tight",
            )

        figures[profile_name] = fig
        plt.show()

    return figures

def plot_two_players_vs_benchmark_spider(
    df_squad,
    player_name_1,
    player_name_2,
    profile_key,
    config,
    benchmarks,
    inverse_metrics=None,
    figsize=(8, 8),
    player1_color="#2b5c8f",  # Primary Blue
    player2_color="#e65100",  # Vivid Orange
):
    """Renders a radar chart comparing TWO squad players side-by-side against

    the precalculated benchmark baseline (1.0) using only the profile key.
    """
    if inverse_metrics is None:
        inverse_metrics = ["Possession Lost per 90", "MLG"]

    # 1. Fetch Profile Config & Benchmarks directly using profile_key
    pos_config = config.get("positions", {}).get(profile_key)
    if not pos_config:
        print(f"Profile key '{profile_key}' not found in config['positions'].")
        return None

    role_metrics = pos_config.get("metrics", [])
    role_benchmark = benchmarks.get(profile_key)

    if not role_benchmark:
        print(f"No benchmark data found for profile '{profile_key}'.")
        return None

    # 2. Extract player rows safely
    p1_data = df_squad[df_squad["Player"] == player_name_1]
    p2_data = df_squad[df_squad["Player"] == player_name_2]

    if p1_data.empty or p2_data.empty:
        missing = []
        if p1_data.empty:
            missing.append(player_name_1)
        if p2_data.empty:
            missing.append(player_name_2)
        print(f"Skipping plot: Player(s) not found in DataFrame: {', '.join(missing)}")
        return None

    p1_row = p1_data.iloc[0]
    p2_row = p2_data.iloc[0]

    # 3. Validate metrics
    valid_metrics = [
        m
        for m in role_metrics
        if m in p1_row.index and m in p2_row.index and m in role_benchmark
    ]
    num_metrics = len(valid_metrics)

    if num_metrics < 3:
        print(
            f"Insufficient valid metrics ({num_metrics}) for radar chart. Need at least 3."
        )
        return None

    raw_p1_vals = [float(p1_row.get(m, 0)) for m in valid_metrics]
    raw_p2_vals = [float(p2_row.get(m, 0)) for m in valid_metrics]
    raw_bench_vals = [float(role_benchmark[m]) for m in valid_metrics]

    norm_p1_vals = []
    norm_p2_vals = []
    norm_bench_vals = []
    display_labels = []

    # 4. Normalize values relative to benchmark base = 1.0
    for m, p1_v, p2_v, b_v in zip(
        valid_metrics, raw_p1_vals, raw_p2_vals, raw_bench_vals
    ):
        is_inverse = m in inverse_metrics
        display_labels.append(f"{m}\n(Inv)" if is_inverse else m)

        norm_p1_vals.append(_ratio_to_benchmark(p1_v, b_v, is_inverse))
        norm_p2_vals.append(_ratio_to_benchmark(p2_v, b_v, is_inverse))
        norm_bench_vals.append(1.0)

    # 5. Close polar plot loops
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    norm_p1_vals += norm_p1_vals[:1]
    norm_p2_vals += norm_p2_vals[:1]
    norm_bench_vals += norm_bench_vals[:1]
    angles += angles[:1]

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # Benchmark Baseline (Top 20 Average)
    ax.plot(
        angles,
        norm_bench_vals,
        color="#888888",
        linewidth=2,
        linestyle="--",
        label="Top 20 Avg (Base 1.0)",
    )
    ax.fill(angles, norm_bench_vals, color="#888888", alpha=0.10)

    # Player 1
    p1_mins = int(p1_row.get("Minutes", p1_row.get("Mins", 0)))
    ax.plot(
        angles,
        norm_p1_vals,
        color=player1_color,
        linewidth=2.5,
        label=f"{player_name_1} ({p1_mins} mins)",
    )
    ax.fill(angles, norm_p1_vals, color=player1_color, alpha=0.25)

    # Player 2
    p2_mins = int(p2_row.get("Minutes", p2_row.get("Mins", 0)))
    ax.plot(
        angles,
        norm_p2_vals,
        color=player2_color,
        linewidth=2.5,
        label=f"{player_name_2} ({p2_mins} mins)",
    )
    ax.fill(angles, norm_p2_vals, color=player2_color, alpha=0.25)

    # Formatting
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(display_labels, fontsize=8)

    ax.set_title(
        f"Head-to-Head Comparison — Profile: {profile_key}\n{player_name_1} vs {player_name_2}",
        fontsize=13,
        fontweight="bold",
        pad=25,
    )
    ax.legend(loc="upper right", bbox_to_anchor=(1.30, 1.1), frameon=True)

    return fig


def plot_personality_boxplot_by_position(
    df_squad, config, title="Personality Value Distribution by Position"
):
    """Generates a boxplot chart showing the distribution of personality values 
    across squad position groups and the overall squad ("All").
    """
    personality_dict = config.get("general", {}).get("personalities", {})

    # Ensure Personality_Value exists in df_squad
    if "Personality_Value" not in df_squad.columns:
        df_squad["Personality_Value"] = df_squad["Personality"].map(personality_dict)

    # Filter out rows with missing personality scores or positions
    valid_df = df_squad.dropna(subset=["Personality_Value", "Best Pos"]).copy()

    records = []

    # 1. Add "All" group entries
    for _, row in valid_df.iterrows():
        records.append({
            "Group": "All",
            "Personality_Value": row["Personality_Value"]
        })

    # 2. Add entries per Squad Position Group (players fit into every group they qualify for)
    for group_name, (roles, sides) in SQUAD_POSITION_GROUPS.items():
        mask = valid_df["Best Pos"].apply(
            lambda pos_str: matches_position_and_side(pos_str, roles, sides)
        )
        for val in valid_df.loc[mask, "Personality_Value"]:
            records.append({
                "Group": group_name,
                "Personality_Value": val
            })

    # Convert records into a long-format DataFrame for Seaborn
    plot_df = pd.DataFrame(records)

    if plot_df.empty:
        print("No valid player personality data found to plot.")
        return

    # Set up figure styling
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")

    # Plot Boxplot
    ax = sns.boxplot(
        data=plot_df,
        x="Group",
        y="Personality_Value",
        palette="viridis",
        width=0.5,
        fliersize=0  # Hide default outliers to prevent duplicate dots from stripplot
    )

    # Overlay Individual Player Data Points
    sns.stripplot(
        data=plot_df,
        x="Group",
        y="Personality_Value",
        color="black",
        alpha=0.6,
        jitter=0.2,
        size=5
    )

    # Chart Formatting
    plt.title(title, fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Position Group", fontsize=11, fontweight="bold", labelpad=10)
    plt.ylabel("Personality Value (0 = Worst, 1 = Best)", fontsize=11, fontweight="bold")
    plt.ylim(-0.05, 1.05)
    plt.xticks(rotation=20, ha="right", fontsize=10, fontweight="bold")

    # Annotate group means above each box
    means = plot_df.groupby("Group", sort=False)["Personality_Value"].mean()
    groups = plot_df["Group"].unique()
    
    for i, group in enumerate(groups):
        mean_val = means.get(group, np.nan)
        if not np.isnan(mean_val):
            ax.text(
                i, 1.02, f"μ={mean_val:.2f}",
                ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#333333"
            )

    plt.tight_layout()
    plt.show()