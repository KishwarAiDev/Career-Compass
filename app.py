import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Career Compass", page_icon="🧭", layout="wide")

BLUE = "#2563eb"
GREEN = "#16a34a"
PURPLE = "#7c3aed"

# ---------- Load data from the database ----------
con = sqlite3.connect("data/career.db")
unemp = pd.read_sql(
    "SELECT year, youth_unemployment FROM youth_unemployment "
    "WHERE year >= 2015 ORDER BY year",
    con,
)
jobs = pd.read_sql("SELECT * FROM jobs", con)
job_skills = pd.read_sql("SELECT * FROM job_skills", con)
con.close()

# ---------- Degree -> words we look for in the job title ----------
# "include" = words that fit the degree, "exclude" = words that do not
DEGREES = {
    "BS Artificial Intelligence": {
        "include": r"machine learning|\bml\b|\bai\b|artificial intelligence|deep learning"
                   r"|\bnlp\b|\bllm\b|data scientist|computer vision|mlops|generative",
        "exclude": r"marketing|social media|\bseo\b|content|sales|business development"
                   r"|account manager|advisor",
    },
    "BS Data Science": {
        "include": r"data analyst|data scientist|business analyst|\bbi\b|data analysis"
                   r"|analytics|data engineer|machine learning",
        "exclude": r"marketing|social media|\bseo\b|content|sales|business development"
                   r"|account manager|advisor",
    },
        "BS Computer Science": {
        "include": r"software|developer|programmer|full[- ]?stack|back[- ]?end|front[- ]?end"
                   r"|devops|\bqa\b|\bsqa\b|quality assurance|\bmern\b|web|mobile"
                   r"|android|\bios\b|\.net|java|python|golang|react|node",
        "exclude": r"marketing|social media|\bseo\b|content|sales|business develop"
                   r"|account manager|advisor|helpdesk|help desk",
    },
        "BS Cyber Security": {
        "include": r"cyber|security|secops|\bsoc\b|infosec|penetration|\bciso\b|vulnerab|threat",
        "exclude": r"marketing|social media|business development|account manager"
                   r"|enterprise sales|journalist|content|faculty|professor|instructor",
    },
}

# ---------- Header ----------
st.title("🧭 Career Compass")
st.caption("Which jobs, skills and cities fit your degree in Pakistan?")

# ---------- 1. The bigger picture ----------
st.subheader("The bigger picture: youth unemployment in Pakistan")
left, right = st.columns([2, 1])
peak = unemp.loc[unemp["youth_unemployment"].idxmax()]
latest = unemp.iloc[-1]
with left:
    chart_data = unemp.copy()
    chart_data["year"] = chart_data["year"].astype(str)
    st.line_chart(chart_data, x="year", y="youth_unemployment", color=PURPLE)
with right:
    st.metric(
        "Youth unemployment, latest",
        f"{latest['youth_unemployment']:.1f}%",
        help=f"Ages 15-24, year {int(latest['year'])}",
    )
    st.write(
        f"It peaked at {peak['youth_unemployment']:.1f}% in {int(peak['year'])}. "
        "Knowing which skills employers ask for helps you stand out."
    )
    st.caption("Source: World Bank")

st.divider()

# ---------- 2. Choose your profile ----------
st.subheader("Choose your profile")
f1, f2, f3 = st.columns(3)
degree = f1.selectbox("Degree", ["Any degree"] + list(DEGREES))
level = f2.selectbox(
    "Level",
    ["All levels", "Student / fresher (0-1 year)",
     "Junior (2-3 years)", "Mid-level (4+ years)"],
)
city_names = sorted(
    c for c in jobs["location"].unique() if c not in ("All Cities", "Multiple Cities")
)
city = f3.selectbox("City", ["Any city"] + city_names)
known = st.multiselect(
    "Skills you already know (optional)", sorted(job_skills["skill"].unique())
)

# ---------- Apply the filters ----------
filtered = jobs
if degree != "Any degree":
    rule = DEGREES[degree]
    fits = filtered["title"].str.contains(rule["include"], case=False, regex=True)
    misfits = filtered["title"].str.contains(rule["exclude"], case=False, regex=True)
    filtered = filtered[fits & ~misfits]

if level == "Student / fresher (0-1 year)":
    filtered = filtered[filtered["exp_years"] <= 1]
elif level == "Junior (2-3 years)":
    filtered = filtered[(filtered["exp_years"] >= 2) & (filtered["exp_years"] <= 3)]
elif level == "Mid-level (4+ years)":
    filtered = filtered[filtered["exp_years"] >= 4]

if city != "Any city":
    # also keep jobs that Rozee marks as open to all cities
    filtered = filtered[filtered["location"].isin([city, "All Cities"])]

# ---------- 3. Jobs for your profile ----------
st.subheader("Jobs for your profile")

if len(filtered) == 0:
    st.warning("No jobs match these filters. Try another degree, city or level.")
    st.stop()

with_salary = filtered["salary_pkr"].notna().sum()
m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Job postings",
    len(filtered),
    help="The same role can be open in several cities, one posting per city",
)
m2.metric("Fresher jobs (0-1 year)", int((filtered["exp_years"] <= 1).sum()))
m3.metric("Jobs showing salary", f"{with_salary} of {len(filtered)}")
if with_salary >= 5:
    m4.metric("Typical salary (PKR)", f"{filtered['salary_pkr'].median():,.0f}")
else:
    m4.metric("Typical salary (PKR)", "Too few salaries")

c_left, c_right = st.columns(2)
with c_left:
    st.markdown("**Where the jobs are**")
    st.bar_chart(filtered["location"].value_counts(), color=BLUE)
with c_right:
    st.markdown("**Skills employers ask for**")
    wanted = job_skills[job_skills["job_id"].isin(filtered["job_id"])]
    top_skills = wanted["skill"].value_counts().head(10)
    if len(top_skills) == 0:
        st.write("No skill information for these jobs.")
    else:
        st.bar_chart(top_skills, color=GREEN, horizontal=True)
        st.caption("Number of job postings that ask for each skill")

# ---------- 4. What to learn next ----------
st.subheader("What should you learn next?")
if len(top_skills) == 0:
    st.write("No skill information for these jobs.")
else:
    missing = top_skills[~top_skills.index.isin(known)].head(5)
    if len(missing) == 0:
        st.success("You already know the most asked skills in these jobs.")
    else:
        st.info("Learn next: " + ", ".join(missing.index))
    if not known:
        st.caption("Tip: choose the skills you already know above.")

# ---------- 5. Job list ----------
st.subheader("Job list")
table = filtered[["title", "company", "location", "exp_years", "salary_pkr", "url"]].copy()
table["salary"] = table["salary_pkr"].map(
    lambda x: f"PKR {x:,.0f}" if pd.notna(x) else "Not mentioned"
)
table = table[["title", "company", "location", "exp_years", "salary", "url"]]
st.dataframe(
    table,
    hide_index=True,
    column_config={
        "title": "Job title",
        "company": "Company",
        "location": "City",
        "exp_years": "Experience (years)",
        "salary": "Salary",
        "url": st.column_config.LinkColumn("Apply", display_text="Open"),
    },
)
st.caption("Source: Rozee.pk, sample of " + str(len(jobs)) + " job postings. "
           "The same role can appear once per city (different branches). "
           "Many postings do not show a salary.")