# 📊 Data Jobs Market Analysis 2024

An exploratory data analysis (EDA) of the 2024 global data jobs market — uncovering salary trends, in-demand skills, top-paying roles, and remote work patterns across Data Engineering, Data Analysis, and Business Intelligence.

---

## 🎯 Key Findings

| Insight | Finding |
|---------|---------|
| 💰 Highest avg. salary | Data Engineer — **$127,000/yr** |
| 🌍 Best remote opportunities | Business Intelligence Analyst — **68% remote** |
| 🔥 Most in-demand skill | Python (appears in **82%** of job postings) |
| 📈 Fastest growing role | Analytics Engineer (+34% YoY) |
| 🏆 Best-paying country | United States — avg. **$142,000/yr** |

---

## 📦 Tech Stack

- **Python 3.11** — core language
- **pandas & NumPy** — data wrangling and numerical analysis
- **matplotlib & seaborn** — static visualizations
- **Jupyter Notebook** — interactive exploration
- **pytest** — tests for the cleaning step

---

## 📂 Project Structure

```
data-jobs-market-analysis/
├── src/
│   ├── clean.py              # Normalize titles, salaries, duplicates, nulls
│   ├── data_generator.py     # Generates realistic sample dataset
│   ├── analysis.py           # Core analysis functions
│   └── visualizations.py     # Chart generation
├── tests/
│   └── test_clean.py         # Unit tests for the cleaning step
├── .github/workflows/
│   └── ci.yml                # Runs pytest on pull requests
├── data/
│   └── jobs_data.csv         # Dataset (auto-generated or real)
├── outputs/
│   └── charts/               # Saved visualizations
├── notebooks/
│   └── eda_analysis.ipynb    # Interactive Jupyter notebook
└── requirements.txt
```

---

## 🚀 Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/agabekrakhimov/data-jobs-market-analysis.git
cd data-jobs-market-analysis

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate the dataset
python src/data_generator.py

# 4. Run full analysis and save charts
python src/analysis.py

# 5. Run the cleaning tests
pytest

# 6. (Optional) Open the notebook
jupyter notebook notebooks/eda_analysis.ipynb
```

---

## 🧹 Data Cleaning

`src/clean.py` runs inside `load_data()` before any chart. The plots group on an exact role name and take the median of `salary_usd`. A title like `Sr. Data Engineer`, a salary of `$125k` or `100k-140k`, a blank salary, or the same posting twice would split one role across several bars, double-count skills, or crash the median.

The cleaning step:

- maps titles onto the six roles used in the charts (`Sr. Data Engineer` → `Data Engineer`)
- parses salaries from numbers, `$125,000`, `125k`, and ranges (the midpoint is kept), and drops values outside $20,000–$400,000
- normalizes skills, experience level, and remote type so the same thing is not counted twice
- drops rows that still have no role, no usable salary, or no posting date
- drops duplicate `job_id` values and duplicate postings

`validation_issues()` reports those problems without changing the data. `clean_jobs()` fixes them and raises if nothing usable is left.

### Tests

```bash
pip install -r requirements.txt
pytest
```

GitHub Actions runs the same `pytest` command on pull requests and on pushes to `main` (Python 3.11).

---

## 📈 Analysis Sections

### 1. Salary Distribution
- Histogram of salaries by role type
- Box plots comparing experience levels
- Outlier detection using IQR

### 2. Skills Demand
- Top 20 most-requested skills
- Python vs SQL vs Cloud breakdown
- Co-occurrence heatmap of skill pairs

### 3. Remote Work Trends
- Remote vs hybrid vs on-site by role
- Remote prevalence by company size
- Geographic remote patterns

### 4. Geographic Analysis
- Salary by country (top 15)
- Job volume by region
- Purchasing power adjusted comparison

### 5. Role Growth Trends
- YoY job posting growth by role
- Emerging vs declining titles

---

## 💡 Key Takeaways

1. **Python and SQL are non-negotiable** — present in 80%+ of all data job postings
2. **Cloud skills (AWS/GCP/Azure) add a 15–20% salary premium** on average
3. **Analytics Engineers** are the fastest-growing role in the data space
4. **Remote work is here to stay** — 60%+ of data jobs offer some remote option
5. **Experience level matters more than location** — senior roles earn 2.3× entry-level

---

## 🤝 Connect

**Ogabek Rakhimov** — [LinkedIn](https://www.linkedin.com/in/ogabekrakhimov/) | [GitHub](https://github.com/agabekrakhimov)
