"""
analysis.py
-----------
Core analysis functions for the Data Jobs Market dataset.
Postings are cleaned in load_data before the charts run.
Runs a full analysis and saves all charts to outputs/charts/.

Usage:
    python src/analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib

# Charts are written to disk. Agg avoids a display requirement in CI.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
from collections import Counter

from clean import clean_jobs

# ── Styling ───────────────────────────────────────────────────────────────────
PALETTE      = ["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2", "#B7E4C7"]
ACCENT_COLOR = "#2D6A4F"
BACKGROUND   = "#F8F9FA"

sns.set_theme(style="whitegrid", palette=PALETTE)
plt.rcParams.update({
    "figure.facecolor": BACKGROUND,
    "axes.facecolor":   BACKGROUND,
    "font.family":      "DejaVu Sans",
})

CHARTS_DIR = Path(__file__).parent.parent / "outputs" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def load_data(path: str = None) -> pd.DataFrame:
    """Load job postings and clean them for the charts."""
    if path is None:
        path = Path(__file__).parent.parent / "data" / "jobs_data.csv"
    raw = pd.read_csv(path)
    df = clean_jobs(raw)
    dropped = len(raw) - len(df)
    print(f"Loaded {len(df):,} records | Columns: {list(df.columns)}")
    if dropped:
        print(f"Dropped {dropped:,} rows (blank salary or role, bad dates, duplicates)")
    return df


# ── Analysis 1: Salary by Role ─────────────────────────────────────────────

def plot_salary_by_role(df: pd.DataFrame) -> None:
    """Box plot of salary distribution per role."""
    role_order = df.groupby("role")["salary_usd"].median().sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=df, x="role", y="salary_usd",
        order=role_order, palette=PALETTE, ax=ax,
        flierprops=dict(marker="o", markerfacecolor="#ccc", markersize=3)
    )
    ax.set_title("Salary Distribution by Role (USD)", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Annual Salary (USD)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.tick_params(axis="x", rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "01_salary_by_role.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: 01_salary_by_role.png")


# ── Analysis 2: Salary by Experience Level ────────────────────────────────

def plot_salary_by_experience(df: pd.DataFrame) -> None:
    """Bar chart of median salary by experience level across roles."""
    exp_order = ["Entry", "Mid", "Senior", "Lead"]
    pivot = df.groupby(["experience_level", "role"])["salary_usd"].median().reset_index()
    pivot = pivot[pivot["experience_level"].isin(exp_order)]

    fig, ax = plt.subplots(figsize=(13, 6))
    sns.barplot(
        data=pivot, x="experience_level", y="salary_usd",
        hue="role", order=exp_order,
        palette=PALETTE, ax=ax
    )
    ax.set_title("Median Salary by Experience Level & Role", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Experience Level", fontsize=11)
    ax.set_ylabel("Median Salary (USD)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(title="Role", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "02_salary_by_experience.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: 02_salary_by_experience.png")


# ── Analysis 3: Top Skills ─────────────────────────────────────────────────

def plot_top_skills(df: pd.DataFrame, top_n: int = 15) -> None:
    """Horizontal bar chart of most in-demand skills."""
    all_skills = []
    for skills_str in df["skills"].dropna():
        all_skills.extend([s.strip() for s in skills_str.split(",")])

    skill_counts = Counter(all_skills).most_common(top_n)
    skills_df = pd.DataFrame(skill_counts, columns=["skill", "count"])
    skills_df["pct"] = (skills_df["count"] / len(df) * 100).round(1)

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(skills_df["skill"][::-1], skills_df["pct"][::-1], color=ACCENT_COLOR, alpha=0.85)
    ax.bar_label(bars, labels=[f"{v:.0f}%" for v in skills_df["pct"][::-1]], padding=4, fontsize=9)
    ax.set_title(f"Top {top_n} In-Demand Skills (% of Job Postings)", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("% of Job Postings", fontsize=11)
    ax.set_xlim(0, skills_df["pct"].max() * 1.15)
    ax.tick_params(axis="y", labelsize=10)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "03_top_skills.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: 03_top_skills.png")


# ── Analysis 4: Remote Work Distribution ──────────────────────────────────

def plot_remote_distribution(df: pd.DataFrame) -> None:
    """Stacked bar chart of remote type by role."""
    pivot = (
        df.groupby(["role", "remote_type"])
        .size()
        .reset_index(name="count")
    )
    pivot_pct = pivot.copy()
    totals = pivot_pct.groupby("role")["count"].transform("sum")
    pivot_pct["pct"] = pivot_pct["count"] / totals * 100

    wide = pivot_pct.pivot(index="role", columns="remote_type", values="pct").fillna(0)
    role_order = df.groupby("role")["salary_usd"].median().sort_values(ascending=False).index
    wide = wide.reindex(role_order)

    fig, ax = plt.subplots(figsize=(12, 6))
    wide.plot(kind="barh", stacked=True, ax=ax, color=PALETTE[:3], edgecolor="white")
    ax.set_title("Remote Work Distribution by Role", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("% of Job Postings", fontsize=11)
    ax.set_ylabel("")
    ax.legend(title="Work Type", loc="lower right", fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "04_remote_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: 04_remote_distribution.png")


# ── Analysis 5: Salary by Country ─────────────────────────────────────────

def plot_salary_by_country(df: pd.DataFrame, top_n: int = 10) -> None:
    """Bar chart of median salary by top countries."""
    top_countries = df.groupby("country")["salary_usd"].median().nlargest(top_n).index
    country_df = df[df["country"].isin(top_countries)]

    median_salaries = (
        country_df.groupby("country")["salary_usd"]
        .median()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(median_salaries.index, median_salaries.values, color=ACCENT_COLOR, alpha=0.85)
    ax.bar_label(bars, labels=[f"${v:,.0f}" for v in median_salaries.values], padding=5, fontsize=9)
    ax.set_title(f"Median Salary by Country (Top {top_n})", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Median Annual Salary (USD)", fontsize=11)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "05_salary_by_country.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: 05_salary_by_country.png")


# ── Analysis 6: Job Posting Trends ────────────────────────────────────────

def plot_posting_trends(df: pd.DataFrame) -> None:
    """Line chart of monthly job postings by role."""
    df["month_year"] = df["posting_date"].dt.to_period("M").astype(str)
    trend = df.groupby(["month_year", "role"]).size().reset_index(name="count")

    fig, ax = plt.subplots(figsize=(13, 6))
    for i, role in enumerate(df["role"].unique()):
        role_data = trend[trend["role"] == role].sort_values("month_year")
        ax.plot(
            role_data["month_year"],
            role_data["count"],
            label=role,
            color=PALETTE[i % len(PALETTE)],
            linewidth=2, marker="o", markersize=3
        )

    ax.set_title("Monthly Job Postings by Role (2023–2024)", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Number of Postings", fontsize=11)
    ax.legend(fontsize=9, loc="upper left")
    tick_positions = list(range(0, len(trend["month_year"].unique()), 3))
    ax.set_xticks([trend["month_year"].unique()[i] for i in tick_positions])
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "06_posting_trends.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: 06_posting_trends.png")


# ── Summary stats ──────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame) -> None:
    """Print key statistics to console."""
    print("\n" + "="*60)
    print("DATA JOBS MARKET — KEY STATISTICS")
    print("="*60)
    print(f"Total job postings analyzed:  {len(df):,}")
    print(f"Date range:                   {df['posting_date'].min().date()} to {df['posting_date'].max().date()}")
    print(f"\nMedian salary (all roles):    ${df['salary_usd'].median():,.0f}")
    print(f"Highest paying role:          {df.groupby('role')['salary_usd'].median().idxmax()}")
    print(f"\nMost common role:             {df['role'].mode()[0]}")
    print(f"Remote/Hybrid %:              {(df['remote_type'].isin(['Remote','Hybrid']).sum()/len(df)*100):.1f}%")
    print("="*60 + "\n")


if __name__ == "__main__":
    from data_generator import generate_dataset

    print("Running full analysis...")

    # Try loading existing data, generate if not found
    data_path = Path(__file__).parent.parent / "data" / "jobs_data.csv"
    if not data_path.exists():
        print("Dataset not found — generating now...")
        generated = generate_dataset()
        data_path.parent.mkdir(exist_ok=True)
        generated.to_csv(data_path, index=False)

    df = load_data(str(data_path))

    print_summary(df)

    print("Generating charts...")
    plot_salary_by_role(df)
    plot_salary_by_experience(df)
    plot_top_skills(df)
    plot_remote_distribution(df)
    plot_salary_by_country(df)
    plot_posting_trends(df)

    print(f"\nAll charts saved to: {CHARTS_DIR}")
