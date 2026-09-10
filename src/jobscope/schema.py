"""Extraction schema for JobScope — the contract shared by all three approaches (A/B/C)."""

from enum import Enum

from pydantic import BaseModel


class Seniority(str, Enum):
    STAGE = "stage"
    JUNIOR = "junior"
    CONFIRME = "confirme"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    
class ContractType(str, Enum):
    CDI = "cdi"
    CDD = "cdd"
    FREELANCE = "freelance"
    STAGE = "stage"
    ALTERNANCE = "alternance"
    
class HomeOfficePolicy(str, Enum):
    ON_SITE = "on_site"
    HYBRID = "hybrid"
    REMOTE = "remote"


class SalaryRange(BaseModel):
    min_salary: int | None = None
    max_salary: int | None = None
    
class JobPosting(BaseModel):
    seniority: Seniority
    contract_type: ContractType
    home_office_policy: HomeOfficePolicy
    salary_range: SalaryRange | None = None
    skills: list[str] = []
