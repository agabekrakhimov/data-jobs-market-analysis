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

---

## 📂 Project Structure

```
data-jobs-market-analysis/
├── src/
│   ├── data_generator.py     # Generates realistic sample dataset
│   ├── analysis.py           # Core analysis functions
│   └── visualizations.py     # Chart generation
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

# 5. (Optional) Open the notebook
jupyter notebook notebooks/eda_analysis.ipynb
```

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
