"""
clean.py
--------
Prepare job postings for the charts in analysis.py.

Those charts group on an exact role name and take the median of salary_usd.
They also keep only the experience labels Entry, Mid, Senior, and Lead, and
they split skills on commas. Scraped or hand-edited files rarely arrive that
way: titles pick up seniority ("Sr. Data Engineer"), pay is stored as
"$125k" or a range, and the same posting is scraped twice.

clean_jobs() normalizes those fields, drops rows that still have no role,
salary, or posting date, and removes duplicates. validation_issues() reports
the same problems without changing the frame.
"""

from __future__ import annotations

import math
import numbers
import re

import pandas as pd

# Annual USD. Hourly or monthly figures mis-filed as a salary sit below the
# floor and wreck the median. The cap keeps a bad scrape from stretching
# every box plot.
SALARY_MIN = 20_000
SALARY_MAX = 400_000

REQUIRED_COLUMNS = ("role", "salary_usd", "posting_date")

# Columns that describe one posting. job_id is handled on its own so a
# missing id does not collapse unrelated rows.
CONTENT_COLUMNS = (
    "role",
    "experience_level",
    "country",
    "salary_usd",
    "remote_type",
    "company_size",
    "industry",
    "skills",
    "posting_date",
)

_MISSING_TEXT = {
    "",
    "nan",
    "none",
    "n/a",
    "na",
    "null",
    "-",
    "--",
    "not specified",
    "negotiable",
}

# Longer phrases first. "analytics engineer" must win over "data engineer".
_ROLE_PATTERNS = (
    (
        re.compile(r"\b(?:machine learning engineer|ml engineer|ml eng|mle)\b"),
        "ML Engineer",
    ),
    (re.compile(r"\banalytics engineer\b"), "Analytics Engineer"),
    (
        re.compile(r"\b(?:business intelligence(?: analyst)?|bi analyst)\b"),
        "Business Intelligence Analyst",
    ),
    (re.compile(r"\bdata scient(?:ist|ce)\b"), "Data Scientist"),
    (
        re.compile(r"\b(?:data engineering|data engineers?|etl engineers?|data eng)\b"),
        "Data Engineer",
    ),
    (re.compile(r"\bdata analysts?\b"), "Data Analyst"),
)

_EXPERIENCE = {
    "entry": "Entry",
    "entry level": "Entry",
    "junior": "Entry",
    "jr": "Entry",
    "intern": "Entry",
    "mid": "Mid",
    "mid level": "Mid",
    "intermediate": "Mid",
    "senior": "Senior",
    "sr": "Senior",
    "lead": "Lead",
    "principal": "Lead",
    "staff": "Lead",
}

_REMOTE = {
    "remote": "Remote",
    "fully remote": "Remote",
    "full remote": "Remote",
    "wfh": "Remote",
    "work from home": "Remote",
    "hybrid": "Hybrid",
    "on site": "On-site",
    "onsite": "On-site",
    "in office": "On-site",
    "office": "On-site",
}

# Canonical names match the skill strings the generator and the skill chart use.
_SKILL_ALIASES = {
    "python": "Python",
    "py": "Python",
    "sql": "SQL",
    "excel": "Excel",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "pbi": "Power BI",
    "pandas": "pandas",
    "statistics": "Statistics",
    "apache spark": "Apache Spark",
    "spark": "Apache Spark",
    "airflow": "Airflow",
    "dbt": "dbt",
    "aws": "AWS",
    "amazon web services": "AWS",
    "kafka": "Kafka",
    "docker": "Docker",
    "snowflake": "Snowflake",
    "looker": "Looker",
    "git": "Git",
    "dax": "DAX",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "mlflow": "MLflow",
    "r": "R",
}

_AMOUNT = re.compile(r"\d[\d,]*(?:\.\d+)?\s*[kK]?")
_ANNUAL_WORDS = (
    "per annum",
    "per year",
    "a year",
    "annually",
    "annual",
    "/year",
    "/yr",
)


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, numbers.Number) and not isinstance(value, bool):
        try:
            return math.isnan(float(value))
        except (TypeError, ValueError):
            return False
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        return False
    return str(value).strip().lower() in _MISSING_TEXT


def _as_float(value):
    if isinstance(value, bool) or not isinstance(value, numbers.Number):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _whole_dollars(value: float) -> int:
    return int(math.floor(value + 0.5))


def _accept_annual(value: float):
    if math.isnan(value) or math.isinf(value):
        return None
    if value < SALARY_MIN or value > SALARY_MAX:
        return None
    return float(_whole_dollars(value))


def _parse_amount(token: str):
    match = _AMOUNT.search(token)
    if not match:
        return None
    raw = re.sub(r"\s+", "", match.group(0)).replace(",", "")
    multiplier = 1.0
    if raw.lower().endswith("k"):
        multiplier = 1000.0
        raw = raw[:-1]
    try:
        return float(raw) * multiplier
    except ValueError:
        return None


def _share_trailing_k(amounts: list[float], parts: list[str]) -> list[float]:
    """Read 100-140k as 100k-140k. The trailing k applies to earlier small numbers."""
    if len(amounts) < 2 or amounts[-1] < 1000:
        return amounts
    if not re.search(r"\d\s*k\b", parts[-1], flags=re.IGNORECASE):
        return amounts
    shared = []
    for amount in amounts[:-1]:
        shared.append(amount * 1000 if amount < 1000 else amount)
    shared.append(amounts[-1])
    return shared


def _text_key(value) -> str | None:
    if _is_missing(value):
        return None
    text = re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()
    if not text or text in _MISSING_TEXT:
        return None
    return text


def parse_salary(value) -> float | None:
    """Return annual USD as a whole number, or None when the cell is unusable.

    Accepts a number, '$125,000', '125k', and ranges. A range keeps the midpoint.
    Values outside $20,000–$400,000 are rejected.
    """
    number = _as_float(value)
    if number is not None:
        return _accept_annual(number)
    if _is_missing(value):
        return None

    text = str(value).strip().lower().replace(",", "")
    text = re.sub(r"[$£€]", "", text)
    text = re.sub(r"\b(?:usd|dollars|dollar)\b", "", text)
    for word in _ANNUAL_WORDS:
        text = text.replace(word, " ")
    text = text.strip()
    if not text or text in _MISSING_TEXT:
        return None

    parts = re.split(r"\s*(?:-|–|—|\bto\b)\s*", text)
    amounts = []
    parsed_parts = []
    for part in parts:
        amount = _parse_amount(part)
        if amount is None:
            continue
        amounts.append(amount)
        parsed_parts.append(part)
    if not amounts:
        return None
    amounts = _share_trailing_k(amounts, parsed_parts)
    return _accept_annual(sum(amounts) / len(amounts))


def normalize_role(value) -> str | None:
    """Map a messy title onto a role the salary charts group by."""
    if _is_missing(value):
        return None
    text = str(value).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text or text in _MISSING_TEXT:
        return None
    for pattern, canonical in _ROLE_PATTERNS:
        if pattern.search(text):
            return canonical
    return None


def normalize_skills(value) -> str | None:
    """Split a skill cell, map aliases, and drop repeats inside the cell."""
    if _is_missing(value):
        return None
    parts = re.split(r"[,;/|]+", str(value).replace("&", ","))
    chosen = []
    for part in parts:
        key = re.sub(r"\s+", " ", part.strip().lower())
        if not key or key in _MISSING_TEXT:
            continue
        skill = _SKILL_ALIASES.get(key)
        if skill is None:
            skill = re.sub(r"\s+", " ", part.strip())
        if skill not in chosen:
            chosen.append(skill)
    if not chosen:
        return None
    return ", ".join(chosen)


def normalize_experience(value) -> str | None:
    """Map a seniority label onto Entry, Mid, Senior, or Lead."""
    key = _text_key(value)
    if key is None:
        return None
    return _EXPERIENCE.get(key)


def normalize_remote(value) -> str | None:
    """Map a workplace label onto Remote, Hybrid, or On-site."""
    key = _text_key(value)
    if key is None:
        return None
    return _REMOTE.get(key)


def _is_clean_salary(value) -> bool:
    if isinstance(value, bool) or not isinstance(value, numbers.Number):
        return False
    number = _as_float(value)
    if number is None or not float(number).is_integer():
        return False
    return SALARY_MIN <= number <= SALARY_MAX


def _is_clean_date(value) -> bool:
    if isinstance(value, pd.Timestamp):
        return not pd.isna(value)
    return False


def _parse_dates(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if isinstance(parsed.dtype, pd.DatetimeTZDtype):
        parsed = parsed.dt.tz_convert("UTC").dt.tz_localize(None)
    return parsed


def _content_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in CONTENT_COLUMNS if column in df.columns]


def validation_issues(df: pd.DataFrame) -> list[str]:
    """Return reasons this frame would skew or crash the charts.

    An empty list means the frame is safe to plot: canonical roles, whole-dollar
    salaries, real posting dates, and no duplicate rows.
    """
    if not isinstance(df, pd.DataFrame):
        return ["expected a DataFrame"]

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        return ["missing columns: " + ", ".join(missing)]
    if df.empty:
        return ["no job postings"]

    issues = []
    roles_ok = df["role"].map(lambda value: normalize_role(value) == value)
    if not bool(roles_ok.all()):
        issues.append("role has blank or non-canonical titles")

    if not bool(df["salary_usd"].map(_is_clean_salary).all()):
        issues.append("salary_usd has missing, non-numeric, or out-of-range values")

    if not bool(df["posting_date"].map(_is_clean_date).all()):
        issues.append("posting_date has missing or unparseable values")

    if "job_id" in df.columns:
        duplicate_id = df["job_id"].notna() & df.duplicated(subset=["job_id"])
        if bool(duplicate_id.any()):
            issues.append("duplicate job_id")

    if bool(df.duplicated(subset=_content_columns(df)).any()):
        issues.append("duplicate postings")

    return issues


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy that is safe to pass into the chart functions.

    Rows with an unrecognized title, an unusable salary, or a bad date are
    dropped. Duplicate job ids and duplicate postings are dropped too.
    The input frame is not modified.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("clean_jobs expected a DataFrame")

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    out = df.copy()
    out["role"] = out["role"].map(normalize_role)
    out["salary_usd"] = out["salary_usd"].map(parse_salary)
    out["posting_date"] = _parse_dates(out["posting_date"])

    if "skills" in out.columns:
        out["skills"] = out["skills"].map(normalize_skills)
    if "experience_level" in out.columns:
        out["experience_level"] = out["experience_level"].map(normalize_experience)
    if "remote_type" in out.columns:
        out["remote_type"] = out["remote_type"].map(normalize_remote)

    out = out.dropna(subset=["role", "salary_usd", "posting_date"])
    out["salary_usd"] = out["salary_usd"].round().astype("int64")

    if "job_id" in out.columns:
        duplicate_id = out["job_id"].notna() & out.duplicated(subset=["job_id"], keep="first")
        out = out.loc[~duplicate_id]

    out = out.drop_duplicates(subset=_content_columns(out), keep="first")
    out = out.reset_index(drop=True)

    issues = validation_issues(out)
    if issues:
        raise ValueError("Job postings failed validation: " + "; ".join(issues))
    return out
