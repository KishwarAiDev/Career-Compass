import sqlite3

import pandas as pd
import requests

url = "https://api.worldbank.org/v2/country/PAK/indicator/SL.UEM.1524.ZS"
params = {"format": "json", "per_page": 100, "date": "2010:2025"}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
data = response.json()

records = data[1]
df = pd.DataFrame(records)
df = df[["date", "value"]]
df = df.rename(columns={"date": "year", "value": "youth_unemployment"})
df["year"] = df["year"].astype(int)
df = df.sort_values("year")

print(df)
print("Missing years:", df["youth_unemployment"].isna().sum())

con = sqlite3.connect("data/career.db")
df.to_sql("youth_unemployment", con, if_exists="replace", index=False)
print(pd.read_sql("SELECT COUNT(*) AS rows_saved FROM youth_unemployment", con))
con.close()