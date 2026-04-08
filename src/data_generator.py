"""
data_generator.py
-----------------
Generates a realistic synthetic dataset of data job postings.
Run this script first to create data/jobs_data.csv.

Usage:
    python src/data_generator.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

# ── Configuration ──────────────────────────────────────────────────────────────

N_RECORDS = 5_000

ROLES = {
    "Data Engineer":            {"base_salary": 125_000, "std": 22_000, "weight": 0.30},
    "Data Analyst":             {"base_salary":  90_000, "std": 18_000, "weight": 0.28},
    "Analytics Engineer":       {"base_salary": 115_000, "std": 20_000, "weight": 0.12},
    "Business Intelligence Analyst": {"base_salary": 95_000, "std": 17_000, "weight": 0.15},
    "Data Scientist":           {"base_salary": 130_000, "std": 25_000, "weight": 0.10},
    "ML Engineer":              {"base_salary": 145_000, "std": 28_000, "weight": 0.05},
}

EXPERIENCE_LEVELS = {
    "Entry":  {"multiplier": 0.70, "weight": 0.25},
    "Mid":    {"multiplier": 1.00, "weight": 0.45},
    "Senior": {"multiplier": 1.35, "weight": 0.25},
    "Lead":   {"multiplier": 1.60, "weight": 0.05},
}

COUNTRIES = {
    "United States":    {"salary_mult": 1.20, "weight": 0.40},
    "United Kingdom":   {"salary_mult": 0.90, "weight": 0.10},
    "Germany":          {"salary_mult": 0.85, "weight": 0.08},
    "Canada":           {"salary_mult": 0.92, "weight": 0.08},
    "India":            {"salary_mult": 0.30, "weight": 0.12},
    "Australia":        {"salary_mult": 0.95, "weight": 0.05},
    "Netherlands":      {"salary_mult": 0.88, "weight": 0.04},
    "Singapore":        {"salary_mult": 1.05, "weight": 0.04},
    "Brazil":           {"salary_mult": 0.35, "weight": 0.05},
    "France":           {"salary_mult": 0.80, "weight": 0.04},
}

SKILLS_BY_ROLE = {
    "Data Engineer":      ["Python", "SQL", "Apache Spark", "Airflow", "dbt", "AWS", "Kafka", "Docker"],
    "Data Analyst":       ["SQL", "Python", "Excel", "Tableau", "Power BI", "pandas", "Statistics"],
    "Analytics Engineer": ["dbt", "SQL", "Python", "Snowflake", "Looker", "Airflow", "Git"],
    "Business Intelligence Analyst": ["Power BI", "Tableau", "SQL", "Excel", "DAX", "Python", "Looker"],
    "Data Scientist":     ["Python", "Machine Learning", "SQL", "Statistics", "TensorFlow", "AWS", "R"],
    "ML Engineer":        ["Python", "TensorFlow", "PyTorch", "AWS", "Docker", "Kubernetes", "MLflow"],
}

REMOTE_TYPES = ["Remote", "Hybrid", "On-site"]

COMPANY_SIZES = ["Startup (<50)", "Mid-size (50-500)", "Large (500-5000)", "Enterprise (5000+)"]

INDUSTRIES = [
    "Technology", "Finance", "Healthcare", "E-Commerce",
    "Consulting", "Manufacturing", "Media", "Education"
]


def generate_skills(role: str, n: int = 3) -> str:
    """Randomly select skills for a given role."""
    pool = SKILLS_BY_ROLE.get(role, ["SQL", "Python"])
    chosen = np.random.choice(pool, size=min(n, len(pool)), replace=False)
    return ", ".join(chosen)


def generate_dataset(n: int = N_RECORDS) -> pd.DataFrame:
    """Generate a realistic jobs dataset."""
    role_names  = list(ROLES.keys())
    role_weights = [ROLES[r]["weight"] for r in role_names]

    exp_names   = list(EXPERIENCE_LEVELS.keys())
    exp_weights = [EXPERIENCE_LEVELS[e]["weight"] for e in exp_names]

    country_names   = list(COUNTRIES.keys())
    country_weights = [COUNTRIES[c]["weight"] for c in country_names]

    roles      = np.random.choice(role_names, n, p=role_weights)
    experience = np.random.choice(exp_names, n, p=exp_weights)
    countries  = np.random.choice(country_names, n, p=country_weights)

    salaries = []
    for role, exp, country in zip(roles, experience, countries):
        base  = ROLES[role]["base_salary"]
        std   = ROLES[role]["std"]
        exp_m = EXPERIENCE_LEVELS[exp]["multiplier"]
        cnt_m = COUNTRIES[country]["salary_mult"]
        salary = int(np.random.normal(base * exp_m * cnt_m, std * exp_m))
        salary = max(30_000, min(salary, 350_000))
        salaries.append(salary)

    remote = np.random.choice(
        REMOTE_TYPES,
        n,
        p=[0.35, 0.40, 0.25]
    )

    post_dates = pd.date_range("2023-01-01", "2024-12-31", periods=n)
    post_dates = post_dates[np.random.permutation(n)]

    df = pd.DataFrame({
        "job_id":        range(1, n + 1),
        "role":          roles,
        "experience_level": experience,
        "country":       countries,
        "salary_usd":    salaries,
        "remote_type":   remote,
        "company_size":  np.random.choice(COMPANY_SIZES, n, p=[0.20, 0.30, 0.30, 0.20]),
        "industry":      np.random.choice(INDUSTRIES, n),
        "skills":        [generate_skills(r, np.random.randint(2, 5)) for r in roles],
        "posting_date":  post_dates,
        "year":          [d.year for d in post_dates],
        "month":         [d.month for d in post_dates],
    })

    return df.sort_values("posting_date").reset_index(drop=True)


if __name__ == "__main__":
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating {N_RECORDS:,} job records...")
    df = generate_dataset(N_RECORDS)
    output_path = output_dir / "jobs_data.csv"
    df.to_csv(output_path, index=False)
    print(f"Dataset saved to: {output_path}")
    print(f"Shape: {df.shape}")
    print(df.head())
