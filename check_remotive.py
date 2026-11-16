import json

d = json.load(open("data/remotive_raw.json", encoding="utf-8"))
print(d.keys())
print(d.get("job-count"))
print(len(d["jobs"]))
print(d["jobs"][0]["tags"])