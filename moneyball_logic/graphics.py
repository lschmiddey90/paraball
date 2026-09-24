import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def plot_top_players(
    scored_df, top_n=15, name_col="Player", score_col="Moneyball_Score"
):
    """Plots a horizontal bar chart of top players by Moneyball Score."""
    if scored_df.empty:
        print("No data available to plot.")
        return

    if name_col not in scored_df.columns:
        raise KeyError(
            f"Column '{name_col}' not found in DataFrame. Available columns: {scored_df.columns.tolist()}"
        )

    plot_data = scored_df.head(top_n).sort_values(by=score_col, ascending=True)

    plt.figure(figsize=(10, 6))
    plt.barh(plot_data[name_col], plot_data[score_col], color="#1f77b4")
    plt.xlabel("Moneyball Score")
    plt.title(f"Top {top_n} Players by Moneyball Score")
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_group_breakdown(scored_df, player_name, name_col="Player"):
    """Plots group scores breakdown for a specific player."""
    if name_col not in scored_df.columns:
        raise KeyError(
            f"Column '{name_col}' not found in DataFrame. Available columns: {scored_df.columns.tolist()}"
        )

    player_data = scored_df[scored_df[name_col] == player_name]
    if player_data.empty:
        print(f"Player '{player_name}' not found.")
        return

    group_cols = [c for c in scored_df.columns if c.startswith("Group_")]
    if not group_cols:
        print("No group scores found in DataFrame.")
        return

    scores = player_data[group_cols].iloc[0].values
    labels = [
        c.replace("Group_", "").replace("_Score", "") for c in group_cols
    ]

    plt.figure(figsize=(8, 4))
    sns.barplot(x=labels, y=scores, palette="viridis")
    plt.ylim(0, 1.0)
    plt.ylabel("Group Score")
    plt.title(f"Performance Profile: {player_name}")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


def plot_top_20_spider_grid(
    scored_df, profile_name="FB_WB", save_filename="top_20_players_spider_grid.png"
):
    """Generates a 5x4 grid of spider charts for individual metrics (Top 20 players)."""
    top_20_df = scored_df.head(20).copy()
    if top_20_df.empty:
        print("No players available for spider grid plot.")
        return

    score_columns = [
        col
        for col in top_20_df.columns
        if col.endswith("_score") and not col.startswith("Group_")
    ]
    x_labels = [col[:-6] for col in score_columns]
    num_metrics = len(x_labels)

    if num_metrics == 0:
        print("No individual score columns found for spider grid plot.")
        return

    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    fig, axes = plt.subplots(
        5, 4, figsize=(24, 28), subplot_kw=dict(polar=True)
    )
    axes = axes.flatten()

    for i, (_, row) in enumerate(top_20_df.iterrows()):
        ax = axes[i]
        player_name = str(row.get("Player", f"Player {i+1}"))
        moneyball_score = float(row.get("Moneyball_Score", 0.0))
        division = str(row.get("Division", "Unknown"))

        y_scores = [float(row[sc]) if pd.notna(row[sc]) else 0.0 for sc in score_columns]
        y_scores_closed = y_scores + [y_scores[0]]

        ax.plot(
            angles_closed,
            y_scores_closed,
            color="#1f77b4",
            linewidth=2,
            linestyle="solid",
        )
        ax.fill(angles_closed, y_scores_closed, color="#1f77b4", alpha=0.25)

        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=7)

        ax.set_xticks(angles)
        ax.set_xticklabels(x_labels, fontsize=8, fontweight="bold")

        ax.set_title(
            f"{i+1}. {player_name}\nScore: {moneyball_score:.3f} | {division}",
            fontsize=10,
            fontweight="bold",
            pad=15,
        )

    # Hide unused axes if dataframe has < 20 rows
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    plt.tight_layout()
    plt.suptitle(
        f"Top 20 Player Radar Profiles — Profile: {profile_name}",
        fontsize=18,
        fontweight="bold",
        y=1.02,
    )

    plt.show()


def plot_scouting_cards(
    scored_df,
    profile_name="FB_WB",
    save_filename="top_20_moneyball_scouting_cards.png",
):
    """Generates 5x4 player scouting cards with group-score radar charts for market targets."""
    top_20_df = scored_df.head(20).copy()
    if top_20_df.empty:
        print("No players available for scouting cards plot.")
        return

    group_score_columns = [
        col
        for col in top_20_df.columns
        if col.startswith("Group_") and col.endswith("_Score")
    ]
    group_labels = [
        col.replace("Group_", "").replace("_Score", "")
        for col in group_score_columns
    ]
    num_groups = len(group_labels)

    if num_groups == 0:
        print("No group score columns found for scouting cards.")
        return

    angles = np.linspace(0, 2 * np.pi, num_groups, endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    fig = plt.figure(figsize=(24, 32), facecolor="#f8f9fa")
    fig.suptitle(
        f"Top 20 Moneyball Player Cards — Profile: {profile_name}",
        fontsize=22,
        fontweight="bold",
        y=0.99,
        color="#111827",
    )

    outer_grid = fig.add_gridspec(5, 4, hspace=0.35, wspace=0.25)

    for i, (_, row) in enumerate(top_20_df.iterrows()):
        if i >= 20:
            break

        player_name = str(row.get("Player", f"Player {i+1}"))
        moneyball_score = float(row.get("Moneyball_Score", 0.0))
        val_min = str(row.get("Transfer_Value_Min", "-"))
        val_max = str(row.get("Transfer_Value_Max", "-"))
        division = str(row.get("Division", "Unknown"))
        age = str(row.get("Age", "-"))

        # Extract Minutes
        mins_raw = row.get("Minutes", None)
        if pd.notna(mins_raw) and str(mins_raw).strip() != "":
            try:
                mins_str = f"Mins: {int(float(mins_raw)):,}"
            except ValueError:
                mins_str = f"Mins: {mins_raw}"
        else:
            mins_str = "Mins: N/A"

        if val_min == val_max:
            val_str = f"Val: {val_min}"
        else:
            val_str = f"Val: {val_min} - {val_max}"

        # Increased header height ratio slightly to fit 4 text lines cleanly
        card_gs = outer_grid[i].subgridspec(
            2, 1, height_ratios=[1.2, 3], hspace=0.15
        )

        # Header section
        header_gs = card_gs[0].subgridspec(
            1, 2, width_ratios=[2.5, 1], wspace=0.05
        )

        ax_text = fig.add_subplot(header_gs[0])
        ax_text.axis("off")
        ax_text.text(
            0.02,
            0.92,
            f"{i+1}. {player_name}",
            fontsize=12,
            fontweight="bold",
            color="#1f2937",
            va="top",
            ha="left",
        )
        ax_text.text(
            0.02,
            0.66,
            f"Age: {age} | {division}",
            fontsize=8.5,
            color="#4b5563",
            va="top",
            ha="left",
        )
        ax_text.text(
            0.02,
            0.42,
            val_str,
            fontsize=9,
            fontweight="semibold",
            color="#059669",
            va="top",
            ha="left",
        )
        ax_text.text(
            0.02,
            0.18,
            mins_str,
            fontsize=8.5,
            fontweight="medium",
            color="#4b5563",
            va="top",
            ha="left",
        )

        ax_circle = fig.add_subplot(header_gs[1])
        ax_circle.axis("off")
        ax_circle.set_aspect("equal")

        score_clamped = min(max(moneyball_score, 0.0), 1.0)
        sizes = [score_clamped, 1.0 - score_clamped]
        colors = ["#2563eb", "#e5e7eb"]

        ax_circle.pie(
            sizes,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.25, edgecolor="white", linewidth=1),
        )

        ax_circle.text(
            0,
            0,
            f"{moneyball_score:.3f}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#1e3a8a",
        )

        # Bottom section: Radar
        ax_radar = fig.add_subplot(card_gs[1], polar=True)

        y_scores = [
            float(row[sc]) if pd.notna(row[sc]) else 0.0
            for sc in group_score_columns
        ]
        y_scores_closed = y_scores + [y_scores[0]]

        ax_radar.plot(
            angles_closed,
            y_scores_closed,
            color="#2563eb",
            linewidth=2,
            linestyle="solid",
        )
        ax_radar.fill(
            angles_closed, y_scores_closed, color="#3b82f6", alpha=0.25
        )

        ax_radar.set_ylim(0, 1.0)
        ax_radar.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax_radar.set_yticklabels([])
        ax_radar.grid(True, color="#d1d5db", linestyle="--", linewidth=0.7)

        ax_radar.set_xticks(angles)
        ax_radar.set_xticklabels(
            group_labels, fontsize=8, fontweight="bold", color="#374151"
        )

    plt.tight_layout()
    plt.show()


def plot_own_team_scouting_cards(
    own_team_df, profile_name="FB_WB", save_filename=None
):
    """Generates player scouting cards for own team members."""
    own_team_top_df = own_team_df.head(20).copy()
    num_players = len(own_team_top_df)

    if num_players == 0:
        print("No players found in 'own_team_df' matching criteria.")
        return

    group_score_columns = [
        col
        for col in own_team_top_df.columns
        if col.startswith("Group_") and col.endswith("_Score")
    ]
    group_labels = [
        col.replace("Group_", "").replace("_Score", "")
        for col in group_score_columns
    ]
    num_groups = len(group_labels)

    if num_groups == 0:
        print("No group score columns found for own team scouting cards.")
        return

    angles = np.linspace(0, 2 * np.pi, num_groups, endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    n_cols = 4 if num_players >= 4 else num_players
    n_rows = math.ceil(num_players / n_cols)

    fig = plt.figure(figsize=(6 * n_cols, 6.5 * n_rows), facecolor="#f8f9fa")
    fig.suptitle(
        f"Own Team Moneyball Cards — Profile: {profile_name} ({num_players} Players)",
        fontsize=22,
        fontweight="bold",
        y=0.99 if n_rows > 1 else 1.02,
        color="#111827",
    )

    outer_grid = fig.add_gridspec(n_rows, n_cols, hspace=0.35, wspace=0.25)

    for i, (_, row) in enumerate(own_team_top_df.iterrows()):
        player_name = str(row.get("Player", f"Player {i+1}"))
        moneyball_score = float(row.get("Moneyball_Score", 0.0))
        division = str(row.get("Division", "Own Team"))
        age = str(row.get("Age", "-"))

        val_min = str(
            row.get("Transfer_Value_Min", row.get("Transfer Value", "-"))
        )
        val_max = str(row.get("Transfer_Value_Max", ""))

        # Extract Minutes
        mins_raw = row.get("Minutes", None)
        if pd.notna(mins_raw) and str(mins_raw).strip() != "":
            try:
                mins_str = f"Mins: {int(float(mins_raw)):,}"
            except ValueError:
                mins_str = f"Mins: {mins_raw}"
        else:
            mins_str = "Mins: N/A"

        if val_max and val_min != val_max:
            val_str = f"Val: {val_min} - {val_max}"
        elif val_min != "-":
            val_str = f"Val: {val_min}"
        else:
            val_str = "Status: Squad Member"

        card_gs = outer_grid[i].subgridspec(
            2, 1, height_ratios=[1.2, 3], hspace=0.15
        )

        header_gs = card_gs[0].subgridspec(
            1, 2, width_ratios=[2.5, 1], wspace=0.05
        )

        ax_text = fig.add_subplot(header_gs[0])
        ax_text.axis("off")
        ax_text.text(
            0.02,
            0.92,
            f"{i+1}. {player_name}",
            fontsize=12,
            fontweight="bold",
            color="#064e3b",
            va="top",
            ha="left",
        )
        ax_text.text(
            0.02,
            0.66,
            f"Age: {age} | {division}",
            fontsize=8.5,
            color="#374151",
            va="top",
            ha="left",
        )
        ax_text.text(
            0.02,
            0.42,
            val_str,
            fontsize=9,
            fontweight="semibold",
            color="#059669",
            va="top",
            ha="left",
        )
        ax_text.text(
            0.02,
            0.18,
            mins_str,
            fontsize=8.5,
            fontweight="medium",
            color="#374151",
            va="top",
            ha="left",
        )

        ax_circle = fig.add_subplot(header_gs[1])
        ax_circle.axis("off")
        ax_circle.set_aspect("equal")

        score_clamped = min(max(moneyball_score, 0.0), 1.0)
        sizes = [score_clamped, 1.0 - score_clamped]
        colors = ["#059669", "#e5e7eb"]

        ax_circle.pie(
            sizes,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.25, edgecolor="white", linewidth=1),
        )

        ax_circle.text(
            0,
            0,
            f"{moneyball_score:.3f}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#064e3b",
        )

        ax_radar = fig.add_subplot(card_gs[1], polar=True)

        y_scores = [
            float(row[sc]) if pd.notna(row[sc]) else 0.0
            for sc in group_score_columns
        ]
        y_scores_closed = y_scores + [y_scores[0]]

        ax_radar.plot(
            angles_closed,
            y_scores_closed,
            color="#059669",
            linewidth=2,
            linestyle="solid",
        )
        ax_radar.fill(
            angles_closed, y_scores_closed, color="#10b981", alpha=0.30
        )

        ax_radar.set_ylim(0, 1.0)
        ax_radar.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax_radar.set_yticklabels([])
        ax_radar.grid(True, color="#d1d5db", linestyle="--", linewidth=0.7)

        ax_radar.set_xticks(angles)
        ax_radar.set_xticklabels(
            group_labels, fontsize=8, fontweight="bold", color="#1f2937"
        )

    plt.tight_layout()

    output_filename = (
        save_filename
        if save_filename
        else f"own_team_{profile_name.lower()}_scouting_cards.png"
    )
    plt.show()
    print(f"Cards successfully generated and saved to '{output_filename}'")