"""Checks for the job-posting cleaner used by analysis.load_data."""

import pandas as pd
import pytest

from analysis import load_data
from clean import (
    clean_jobs,
    normalize_experience,
    normalize_remote,
    normalize_role,
    normalize_skills,
    parse_salary,
    validation_issues,
)


def test_parse_salary_reads_text_ranges_and_numbers():
    assert parse_salary(125_000) == 125_000
    assert parse_salary("125000") == 125_000
    assert parse_salary("$125,000") == 125_000
    assert parse_salary("125k") == 125_000
    assert parse_salary("125K") == 125_000
    assert parse_salary("USD 110,000 per year") == 110_000
    assert parse_salary("100k-140k") == 120_000
    assert parse_salary("100-140k") == 120_000
    assert parse_salary("100k to 140k") == 120_000
    assert parse_salary("$80,000 – $100,000") == 90_000
    assert parse_salary(20_000) == 20_000
    assert parse_salary(400_000) == 400_000


def test_parse_salary_rejects_blank_hourly_and_outliers():
    assert parse_salary(None) is None
    assert parse_salary(float("nan")) is None
    assert parse_salary("") is None
    assert parse_salary("n/a") is None
    assert parse_salary("negotiable") is None
    assert parse_salary(45) is None
    assert parse_salary("45/hr") is None
    assert parse_salary(15_000) is None
    assert parse_salary(-50_000) is None
    assert parse_salary(9_999_999) is None


def test_normalize_role_maps_seniority_and_aliases():
    assert normalize_role("Sr. Data Engineer") == "Data Engineer"
    assert normalize_role("DATA SCIENTIST III") == "Data Scientist"
    assert normalize_role("Machine Learning Engineer") == "ML Engineer"
    assert normalize_role("Jr. BI Analyst") == "Business Intelligence Analyst"
    assert normalize_role("analytics engineer") == "Analytics Engineer"
    assert normalize_role("  data   analyst ") == "Data Analyst"
    assert normalize_role(None) is None
    assert normalize_role("  ") is None
    assert normalize_role("Accountant") is None


def test_normalize_skills_dedupes_and_maps_aliases():
    assert normalize_skills("python, SQL, python, PowerBI") == "Python, SQL, Power BI"
    assert normalize_skills("excel; sql | python") == "Excel, SQL, Python"
    assert normalize_skills("Spark & AWS") == "Apache Spark, AWS"
    assert normalize_skills(None) is None
    assert normalize_skills("  ") is None


def test_normalize_experience_and_remote_match_chart_labels():
    assert normalize_experience("Sr.") == "Senior"
    assert normalize_experience("Jr") == "Entry"
    assert normalize_experience("Mid-level") == "Mid"
    assert normalize_experience("principal") == "Lead"
    assert normalize_experience("Director") is None

    assert normalize_remote("WFH") == "Remote"
    assert normalize_remote("Onsite") == "On-site"
    assert normalize_remote("On-site") == "On-site"
    assert normalize_remote("hybrid") == "Hybrid"
    assert normalize_remote("flexible") is None


def test_validation_issues_flags_fields_the_charts_cannot_use():
    raw = pd.DataFrame(
        {
            "job_id": [1, 1],
            "role": ["Sr. Data Engineer", "Data Engineer"],
            "salary_usd": ["$120,000", "$120,000"],
            "posting_date": ["2024-01-01", "2024-01-01"],
        }
    )
    issues = validation_issues(raw)
    assert "role has blank or non-canonical titles" in issues
    assert "salary_usd has missing, non-numeric, or out-of-range values" in issues
    assert "posting_date has missing or unparseable values" in issues
    assert "duplicate job_id" in issues


def test_validation_issues_reports_missing_columns():
    issues = validation_issues(pd.DataFrame({"role": ["Data Analyst"]}))
    assert issues == ["missing columns: salary_usd, posting_date"]


def test_clean_jobs_drops_bad_rows_and_duplicates():
    raw = pd.DataFrame(
        {
            "job_id": [1, 2, 3, 4, 5, None],
            "role": [
                "Sr. Data Engineer",
                "senior data engineer",
                "DATA ANALYST",
                "Data Analyst",
                "Accountant",
                "Data Analyst",
            ],
            "salary_usd": ["$140,000", "130k", "90k", "90k", 95_000, "80k"],
            "posting_date": [
                "2024-01-10",
                "2024-02-10",
                "2024-03-01",
                "2024-03-01",
                "2024-04-01",
                "2024-05-01",
            ],
            "experience_level": ["Sr.", "Senior", "Jr", "Junior", "Senior", "Mid"],
            "remote_type": ["WFH", "On-site", "hybrid", "Hybrid", "remote", "onsite"],
            "skills": [
                "python, python, SQL",
                "Spark, AWS",
                "excel; sql",
                "Excel, SQL",
                "Excel",
                "sql",
            ],
            "country": ["United States"] * 6,
        }
    )
    original = raw.copy()
    cleaned = clean_jobs(raw)

    pd.testing.assert_frame_equal(raw, original)
    assert cleaned["role"].tolist() == [
        "Data Engineer",
        "Data Engineer",
        "Data Analyst",
        "Data Analyst",
    ]
    assert cleaned["salary_usd"].tolist() == [140_000, 130_000, 90_000, 80_000]
    assert cleaned["skills"].tolist() == [
        "Python, SQL",
        "Apache Spark, AWS",
        "Excel, SQL",
        "SQL",
    ]
    assert cleaned["experience_level"].tolist() == ["Senior", "Senior", "Entry", "Mid"]
    assert cleaned["remote_type"].tolist() == ["Remote", "On-site", "Hybrid", "On-site"]
    assert validation_issues(cleaned) == []
    assert clean_jobs(cleaned).equals(cleaned)


def test_clean_jobs_requires_columns_and_at_least_one_row():
    with pytest.raises(ValueError, match="salary_usd"):
        clean_jobs(pd.DataFrame({"role": ["Data Analyst"], "posting_date": ["2024-01-01"]}))

    with pytest.raises(ValueError, match="no job postings"):
        clean_jobs(
            pd.DataFrame(
                {
                    "role": ["Accountant"],
                    "salary_usd": ["n/a"],
                    "posting_date": ["not a date"],
                }
            )
        )


def test_missing_job_id_does_not_collapse_different_postings():
    raw = pd.DataFrame(
        {
            "job_id": [None, None],
            "role": ["Data Engineer", "Data Analyst"],
            "salary_usd": [120_000, 80_000],
            "posting_date": ["2024-01-01", "2024-01-02"],
        }
    )
    cleaned = clean_jobs(raw)
    assert len(cleaned) == 2


def test_load_data_makes_groupbys_chart_ready(tmp_path):
    path = tmp_path / "jobs.csv"
    pd.DataFrame(
        {
            "job_id": [1, 2, 3, 3, 4],
            "role": [
                "Sr. Data Engineer",
                "senior data engineer",
                "DATA ANALYST",
                "Data Analyst",
                "Data Analyst",
            ],
            "salary_usd": ["$140,000", "130k", "90k", "90000", "90k"],
            "posting_date": [
                "2024-01-10",
                "2024-02-10",
                "2024-03-01",
                "2024-03-01",
                "2024-03-01",
            ],
            "experience_level": ["Sr.", "Senior", "Jr", "Junior", "Jr"],
            "remote_type": ["WFH", "On-site", "hybrid", "Hybrid", "hybrid"],
            "skills": [
                "python, python, SQL",
                "Spark, AWS",
                "excel; sql",
                "Excel, SQL",
                "excel; sql",
            ],
            "country": ["United States"] * 5,
        }
    ).to_csv(path, index=False)

    raw = pd.read_csv(path)
    assert raw["role"].nunique() == 4
    assert not pd.api.types.is_numeric_dtype(raw["salary_usd"])
    with pytest.raises(TypeError):
        raw.groupby("role")["salary_usd"].median()

    df = load_data(str(path))
    assert df["role"].nunique() == 2
    medians = df.groupby("role")["salary_usd"].median()
    assert medians["Data Engineer"] == 135_000
    assert medians["Data Analyst"] == 90_000

    # plot_salary_by_experience keeps only these labels. "Sr." would be dropped.
    assert set(df["experience_level"]) <= {"Entry", "Mid", "Senior", "Lead"}
    assert set(df["remote_type"]) <= {"Remote", "Hybrid", "On-site"}
    assert pd.api.types.is_datetime64_any_dtype(df["posting_date"])
    assert df["posting_date"].dt.to_period("M").astype(str).tolist() == [
        "2024-01",
        "2024-02",
        "2024-03",
    ]
    assert "Python, SQL" in set(df["skills"])
    assert len(df) == 3


def test_generated_rows_survive_cleaning(tmp_path):
    from data_generator import generate_dataset

    raw = generate_dataset(300)
    path = tmp_path / "jobs_data.csv"
    raw.to_csv(path, index=False)

    cleaned = load_data(str(path))
    assert len(cleaned) == len(raw)
    assert validation_issues(cleaned) == []
    assert cleaned["role"].tolist() == raw["role"].tolist()
    assert cleaned["salary_usd"].tolist() == raw["salary_usd"].tolist()
