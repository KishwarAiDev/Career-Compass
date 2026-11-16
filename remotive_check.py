

"""
Step 1: Remotive API se data nikalna aur dekhna ke andar kya hai.
 
Chalane ka tareeqa (terminal mein):
    pip install requests pandas
    python step1_explore_remotive.py
 
Zaroori: Remotive ka rule hai ke din mein max 4 baar data mangwayen.
Is liye script data ko "remotive_raw.json" file mein save kar leti hai.
Dobara chalane par wo file se parhegi, API ko dobara call nahi karegi.
(Naya data chahiye to remotive_raw.json delete kar dein.)
 
Source: Remotive (https://remotive.com)
"""
 
import json
import os
import re
 
import pandas as pd
import requests
 
API_URL = "https://remotive.com/api/remote-jobs"
RAW_FILE = "remotive_raw.json"
 
 
# ---------- EXTRACT ----------
def get_jobs():
    """API se jobs lata hai, ya agar file pehle se hai to wahan se parhta hai."""
    if os.path.exists(RAW_FILE):
        print(f"'{RAW_FILE}' mil gayi, API call nahi ki.")
        with open(RAW_FILE, encoding="utf-8") as f:
            return json.load(f)
 
    print("API se data mangwa raha hun...")
    # User-Agent batana achhi aadat hai
    headers = {"User-Agent": "student-career-project/1.0"}
    response = requests.get(API_URL, headers=headers, timeout=30)
    response.raise_for_status()  # agar error aaye to yahin ruk jaye
    data = response.json()
 
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"Data '{RAW_FILE}' mein save ho gaya.")
    return data
 
 
# ---------- EXPLORE ----------
# Kuch skills jin ko hum description mein dhoondenge (baad mein list barha sakte hain)
SKILLS = [
    "python", "sql", "machine learning", "deep learning", "pandas",
    "tensorflow", "pytorch", "javascript", "react", "aws", "docker",
    "excel", "tableau", "power bi", "figma", "seo",
]
 
 
def explore(data):
    """DataFrame banata hai aur basic cheezen print karta hai."""
    df = pd.DataFrame(data["jobs"])
 
    print("\n=== 1. Kitni jobs aur kaunse columns? ===")
    print("Jobs:", len(df))
    print("Columns:", list(df.columns))
 
    print("\n=== 2. Categories (kis area mein kitni jobs) ===")
    print(df["category"].value_counts())
 
    print("\n=== 3. Job type ===")
    print(df["job_type"].value_counts(dropna=False))
 
    print("\n=== 4. Salary kitni jobs mein likhi hai? ===")
    has_salary = df["salary"].fillna("").str.strip() != ""
    print(f"{has_salary.sum()} / {len(df)} jobs mein salary hai")
    print(df.loc[has_salary, "salary"].head(5).to_string(index=False))
 
    print("\n=== 5. Location ki pabandi (top 10) ===")
    print(df["candidate_required_location"].value_counts().head(10))
 
    print("\n=== 6. Skills (description mein kitni baar aaye) ===")
    text = df["description"].fillna("").str.lower()
    # \b matlab "poora lafz": taake "aws" lafz "laws" mein na mil jaye
    counts = {
        s: int(text.str.contains(rf"\b{re.escape(s)}\b", regex=True).sum())
        for s in SKILLS
    }
    skills_df = pd.Series(counts).sort_values(ascending=False)
    print(skills_df)
 
    return df
 
 
if __name__ == "__main__":
    jobs_data = get_jobs()
    explore(jobs_data)