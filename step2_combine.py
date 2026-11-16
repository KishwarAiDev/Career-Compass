import pandas as pd

files = ["data/rozee_sample.json", "data/rozee_data_analyst_oct26.json"]
frames = [pd.read_json(f) for f in files]
jobs = pd.concat(frames, ignore_index=True)

print("Before:", len(jobs))
jobs = jobs.drop_duplicates(subset="job_id")
print("After removing duplicates:", len(jobs))
import pandas as pd

files = ["data/rozee_sample.json", "data/rozee_data_analyst_oct26.json"]
frames = [pd.read_json(f) for f in files]
jobs = pd.concat(frames, ignore_index=True)
jobs = jobs.drop_duplicates(subset="job_id")
print("Jobs after removing duplicates:", len(jobs))


def in_pakistan(points):
    # No coordinates (for example "All Cities"): keep the job
    if len(points) == 0:
        return True
    for point in points:
        lat, lng = point.split(",")
        lat = float(lat)
        lng = float(lng)
        if 23 <= lat <= 37.5 and 60 <= lng <= 78:
            return True
    return False


jobs["in_pakistan"] = jobs["latlng"].apply(in_pakistan)
print(jobs[~jobs["in_pakistan"]][["company", "location"]])

jobs = jobs[jobs["in_pakistan"]]
print("Jobs after removing non-Pakistan locations:", len(jobs))
print(jobs["location"].value_counts())