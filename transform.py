import glob
import re
import sqlite3
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator

# ---------- 1. Load all raw Rozee files ----------
files = sorted(glob.glob("data/raw/rozee_*.json"))
print("Files found:", len(files))

frames = []
for file in files:
    df = pd.read_json(file)
    print(file, "->", len(df), "jobs")
    frames.append(df)

jobs = pd.concat(frames, ignore_index=True)
print("Total rows:", len(jobs))
# ---------- 1b. Fix city names that came in Chinese ----------
# Rozee sometimes sends city names in Chinese (for example when the proxy is abroad).
CITY_FIXES = {
    "所有城市": "All Cities",
    "拉合尔": "Lahore",
    "伊斯兰堡": "Islamabad",
    "卡拉奇": "Karachi",
    "德拉加济汗": "Dera Ghazi Khan",
}
jobs["location"] = jobs["location"].replace(CITY_FIXES)

# Warn if any city name is still not in English letters
leftover = jobs[jobs["location"].str.contains(r"[^\x00-\x7F]")]["location"].unique()
print("City names still not fixed:", list(leftover))

# ---------- 2. Remove duplicates ----------
jobs = jobs.drop_duplicates(subset="job_id")
print("After removing same job_id:", len(jobs))

jobs = jobs.drop_duplicates(subset=["title", "company", "location"])
print("After removing same title + company + location:", len(jobs))


# ---------- 3. Keep only jobs in Pakistan ----------
def in_pakistan(points):
    # No coordinates (for example "All Cities"): keep the job
    if len(points) == 0:
        return True
    for point in points:
        lat, lng = point.split(",")
        if 23 <= float(lat) <= 37.5 and 60 <= float(lng) <= 78:
            return True
    return False


jobs = jobs[jobs["country"] == "Pakistan"]
jobs = jobs[jobs["latlng"].apply(in_pakistan)]
print("After keeping only Pakistan:", len(jobs))

# ---------- 4. Salary: text to number ----------
jobs["salary_pkr"] = pd.to_numeric(
    jobs["salary"]
    .str.replace("PKR", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip(),
    errors="coerce",
)
print("Jobs with a usable salary:", jobs["salary_pkr"].notna().sum())

# ---------- 5. Experience: text to number ----------
jobs["exp_years"] = pd.to_numeric(
    jobs["experience"]
    .str.replace("Fresh", "0", regex=False)
    .str.extract(r"(\d+)")[0],
    errors="coerce",
)

# Rozee often shows wrong experience for internships, so trust the title instead
title = jobs["title"].str.lower()
is_intern = title.str.contains(r"\b(?:intern|interns|internship|trainee)\b") | (
    jobs["contract_type"] == "Internship"
)
jobs.loc[is_intern, "exp_years"] = 0

# A "junior" job can not need 5 years: keep at most 2 years
is_junior = title.str.contains(r"\b(?:junior|jr)\b")
jobs.loc[is_junior, "exp_years"] = jobs.loc[is_junior, "exp_years"].clip(upper=2)

print("Internships set to 0 years:", is_intern.sum())
print("Fresher jobs (0-1 year):", (jobs["exp_years"] <= 1).sum())


# ---------- 6. Skills: clean names and keep one row per (job, skill) ----------
# Rozee skill tags are messy ("Power BI", "Power-BI", "MS Excel", "Microsoft Excel").
# We keep a list of skills we care about and map every spelling to one clean name.
SKILL_NAMES = {
    "python": "Python",
    "sql": "SQL",
    "machinelearning": "Machine Learning",
    "machinelearningalgorithms": "Machine Learning",
    "deeplearning": "Deep Learning",
    "artificialintelligence": "Artificial Intelligence",
    "generativeai": "Generative AI",
    "largelanguagemodels": "Large Language Models",
    "llm": "Large Language Models",
    "promptengineering": "Prompt Engineering",
    "rag": "RAG",
    "nlp": "NLP",
    "naturallanguageprocessing": "NLP",
    "dataanalysis": "Data Analysis",
    "dataanalytics": "Data Analysis",
    "datavisualization": "Data Visualization",
    "datacleaning": "Data Cleaning",
    "dataengineering": "Data Engineering",
    "datapipelines": "Data Pipelines",
    "datamodeling": "Data Modeling",
    "datascience": "Data Science",
    "statisticalanalysis": "Statistics",
    "statistics": "Statistics",
    "featureengineering": "Feature Engineering",
    "modelevaluation": "Model Evaluation",
    "businessintelligence": "Business Intelligence",
    "dashboarddevelopment": "Dashboard Development",
    "tableau": "Tableau",
    "powerbi": "Power BI",
    "excel": "Excel",
    "msexcel": "Excel",
    "microsoftexcel": "Excel",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikitlearn": "Scikit-learn",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "vectordatabases": "Vector Databases",
        # software engineering
    "pythonprogramming": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "nodejs": "Node.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "vuejs": "Vue.js",
    "csharp": "C#",
    "dotnet": ".NET",
    "dotnetcore": ".NET",
    "aspnet": ".NET",
    "aspnetcore": ".NET",
    "golang": "Go",
    "php": "PHP",
    "git": "Git",
    "gitversioncontrol": "Git",
    "versioncontrol": "Git",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "googlecloudplatform": "Google Cloud",
    "cicd": "CI/CD",
    "devops": "DevOps",
    "developmentoperationsdevops": "DevOps",
    "restapis": "REST APIs",
    "restapi": "REST APIs",
    "microservices": "Microservices",
    "graphql": "GraphQL",
    "datastructures": "Data Structures",
    "algorithms": "Algorithms",
    "objectorientedprogrammingoop": "OOP",
    "oop": "OOP",
    "softwaretesting": "Software Testing",
    "manualtesting": "Software Testing",
    "unittesting": "Unit Testing",
    "qualityassurance": "Quality Assurance",
    "postman": "Postman",
    "spring": "Spring",
    "springboot": "Spring",
    "hibernate": "Hibernate",
    "django": "Django",
    "cascadingstylesheetscss": "CSS",
    "css": "CSS",
    "html": "HTML",
    "plsql": "PL/SQL",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
        # cyber security
    "cybersecurity": "Cyber Security",
    "cyberintelligence": "Cyber Intelligence",
    "threatintelligence": "Threat Intelligence",
    "cyberthreathunting": "Threat Hunting",
    "malwareandvulnerabilities": "Vulnerability Management",
    "vulnerabilitymanagement": "Vulnerability Management",
    "vulnerabilityscanning": "Vulnerability Management",
    "applicationsecurity": "Application Security",
    "webapplicationsecurity": "Application Security",
    "enterpriseapplicationsecurity": "Application Security",
    "applicationsecuritytestingast": "Application Security",
    "cloudsecurity": "Cloud Security",
    "cloudinfrastructuresecurity": "Cloud Security",
    "penetrationtesting": "Penetration Testing",
    "secops": "SecOps",
    "compliance": "Compliance",
    "regulatorycompliance": "Compliance",
    "riskmanagement": "Risk Management",
    "corporaterisk": "Risk Management",
    "networkmonitoring": "Network Monitoring",
    "accesscontrol": "Access Control",
    "securityarchitecture": "Security Architecture",
    "datasecurity": "Data Security",
    "crowdstrike": "CrowdStrike",
    "falcon": "CrowdStrike",
    "crowdstrikefalcon": "CrowdStrike",
    "tenable": "Tenable",
    "darktrace": "Darktrace",
}


def clean_skill(raw):
    # "Power-BI" and "Power BI" both become "powerbi"
    key = re.sub(r"[^a-z0-9+#]", "", raw.lower())
    return SKILL_NAMES.get(key)


skills = jobs[["job_id", "skills"]].explode("skills").dropna(subset=["skills"])
skills["skill"] = skills["skills"].apply(clean_skill)
skills = skills.dropna(subset=["skill"]).drop_duplicates(subset=["job_id", "skill"])
skills = skills[["job_id", "skill"]]
print("Jobs with at least one clean skill:", skills["job_id"].nunique())
print(skills["skill"].value_counts().head(10))

# ---------- 7. Validate every job with Pydantic ----------
class JobRecord(BaseModel):
    job_id: int
    title: str = Field(min_length=3)
    company: str = Field(min_length=1)
    location: str = Field(min_length=2)
    salary_pkr: Optional[float] = None
    exp_years: Optional[float] = Field(default=None, ge=0, le=40)
    url: str
    scraped_at: Optional[str] = None

    @field_validator("salary_pkr")
    @classmethod
    def salary_must_be_realistic(cls, value):
        # A salary outside this range is probably a typing mistake: treat it as unknown
        if value is None:
            return None
        if value < 10_000 or value > 500_000:
            return None
        return value

    @field_validator("url")
    @classmethod
    def url_must_be_rozee(cls, value):
        if not value.startswith("https://www.rozee.pk/"):
            raise ValueError("url must start with https://www.rozee.pk/")
        return value


clean = jobs[["job_id", "title", "company", "location", "salary_pkr",
              "exp_years", "url", "scraped_at"]].copy()
clean["job_id"] = clean["job_id"].astype(int)
clean["scraped_at"] = clean["scraped_at"].astype(str)
salary_before = clean["salary_pkr"].notna().sum()

valid_rows = []
rejected_rows = []
for row in clean.to_dict("records"):
    # pandas uses NaN for missing values, Pydantic expects None
    row = {key: (None if pd.isna(value) else value) for key, value in row.items()}
    try:
        record = JobRecord(**row)
        valid_rows.append(record.model_dump())
    except ValidationError as error:
        reasons = "; ".join(f"{e['loc'][0]}: {e['msg']}" for e in error.errors())
        rejected_rows.append(
            {"job_id": row["job_id"], "title": row["title"], "reason": reasons}
        )

valid = pd.DataFrame(valid_rows)
rejected = pd.DataFrame(rejected_rows, columns=["job_id", "title", "reason"])
print("Valid jobs:", len(valid))
print("Rejected jobs:", len(rejected))
print("Unrealistic salaries set to unknown:",
      salary_before - valid["salary_pkr"].notna().sum())

# keep skills only for jobs that passed validation
skills["job_id"] = skills["job_id"].astype(int)
skills = skills[skills["job_id"].isin(valid["job_id"])]

# ---------- 8. Save to the database ----------
con = sqlite3.connect("data/career.db")
valid.to_sql("jobs", con, if_exists="replace", index=False)
rejected.to_sql("rejected_jobs", con, if_exists="replace", index=False)
skills.to_sql("job_skills", con, if_exists="replace", index=False)
print(pd.read_sql("SELECT COUNT(*) AS jobs_saved FROM jobs", con))
print(pd.read_sql("SELECT COUNT(*) AS skill_rows_saved FROM job_skills", con))
con.close()
