import pandas as pd
import sqlite3

df = pd.read_json("data/rozee_sample.json")
print(len(df))
print(df.columns.tolist())
print(df[["title", "company", "location", "salary"]].head())
print(df["location"].value_counts())
print(df[df["location"] == "Hyderabad"][["company", "country", "latlng"]])
parts = df["latlng"].str[0].str.split(",", expand=True).astype(float)
df["lat"] = parts[0]
df["lng"] = parts[1]

df = df[df["lat"].between(23, 37.5) & df["lng"].between(60, 78)]
print(len(df))
print(df["location"].value_counts())
df["salary_pkr"] = (df["salary"].str.replace("PKR", "", regex=False)
                                .str.replace(",", "", regex=False)
                                .str.strip())
df["salary_pkr"] = pd.to_numeric(df["salary_pkr"], errors="coerce")

print(df[["salary", "salary_pkr"]].dropna())
print("Jobs with salary:", df["salary_pkr"].notna().sum())
print("Average salary:", df["salary_pkr"].mean())
df["exp_years"] = (df["experience"].str.replace("Fresh", "0", regex=False)
                                   .str.extract(r"(\d+)")[0]
                                   .astype(int))

print(df[["experience", "exp_years"]].head(8))

fresh = df[df["exp_years"] <= 1]
print("Fresher jobs:", len(fresh))
print(fresh[["title", "company", "location"]])
clean = df[["job_id", "title", "company", "location", "salary_pkr",
            "exp_years", "skills", "url", "scraped_at"]].copy()
clean["skills"] = clean["skills"].str.join(", ")

con = sqlite3.connect("data/career.db")
clean.to_sql("jobs", con, if_exists="replace", index=False)

print(pd.read_sql("SELECT location, COUNT(*) AS jobs FROM jobs GROUP BY location", con))
con.close()