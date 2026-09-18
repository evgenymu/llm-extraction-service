"""Schema for a job posting extracted from free text.

Two conventions hold for every field:

- Every key is required, and missing information is stated explicitly: null
  for values, ``unknown`` for a category, an empty list for a collection.
  A key the model may omit is a key it can silently forget; a required key
  forces it to state "not given".
- Nothing is inferred. If the posting does not say it, the answer is empty.
  A guessed salary is worse than no salary.

Field descriptions reach the model only through the prompt, which
``extractor.build_prompt`` renders from them. Ollama turns the JSON schema into
a decoding grammar that ignores descriptions (verified: identical output with
and without them at temperature 0).
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class Seniority(StrEnum):
    INTERN = "intern"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"


class SalaryPeriod(StrEnum):
    HOUR = "hour"
    MONTH = "month"
    YEAR = "year"


class Salary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: int | None = Field(description="Lower bound as a whole number.")
    max: int | None = Field(description="Upper bound; equal to min for a single figure.")
    currency: str | None = Field(description="ISO 4217 code, for example PLN, EUR, USD.")
    period: SalaryPeriod | None = Field(description="What the amount is paid per.")


class JobPosting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(description="Job title as stated. Null if no title is given.")
    company: str | None = Field(
        description="Name of the hiring company. Null if the text does not name one."
    )
    location: str | None = Field(
        description="City and/or country only. Do not include the work arrangement."
    )
    work_mode: WorkMode = Field(description="remote, hybrid or onsite; unknown if not stated.")
    seniority: list[Seniority] = Field(
        description="Every level the posting targets, e.g. mid to senior. Empty when not stated."
    )
    salary: Salary | None = Field(description="Null when the posting gives no pay information.")
    skills: list[str] = Field(description="Technologies and skills explicitly mentioned.")
