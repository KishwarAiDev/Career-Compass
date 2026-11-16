from pydantic import BaseModel, ValidationError


class Job(BaseModel):
    title: str
    exp_years: int


print(Job(title="Data Analyst", exp_years=2))

try:
    Job(title="Data Analyst", exp_years="two")
except ValidationError as error:
    print("Rejected:", error)