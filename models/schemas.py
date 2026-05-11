from pydantic import BaseModel, Field
from typing import List, Optional

class Location(BaseModel):
    type: str = Field(description="remote|hybrid|onsite")
    city: str
    country: str

class CriterionWeight(BaseModel):
    criterion: str
    weight: int

class SalaryRange(BaseModel):
    min: int
    max: int
    currency: str

class ScoringRubric(BaseModel):
    must_have_weight: float = 0.40
    experience_weight: float = 0.25
    skills_weight: float = 0.20
    nice_to_have_weight: float = 0.10
    trajectory_weight: float = 0.05

class JobDescription(BaseModel):
    id: str
    title: str
    department: str
    location: Location
    seniority: str
    responsibilities: List[str]
    must_haves: List[CriterionWeight]
    nice_to_haves: List[CriterionWeight]
    tech_stack: List[str]
    salary_range: Optional[SalaryRange] = None
    scoring_rubric: ScoringRubric = ScoringRubric()
    created_by: str
    status: str

class Contact(BaseModel):
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

class Experience(BaseModel):
    company: str
    title: str
    start: str
    end: str
    description: str

class Education(BaseModel):
    institution: str
    degree: str
    field: str
    year: int

class Skills(BaseModel):
    hard: List[str]
    soft: List[str]

class CandidateProfile(BaseModel):
    id: str
    jd_id: str
    source_channel: str
    applied_at: str
    contact: Contact
    experience: List[Experience]
    education: List[Education]
    skills: Skills
    certifications: List[str] = []
    languages: List[str] = []
    parse_confidence: float
    pii_anonymised: bool

class DimensionScores(BaseModel):
    must_have: int
    experience: int
    skills: int
    nice_to_have: int
    trajectory: int

class CriteriaMet(BaseModel):
    criterion: str
    met: bool
    confidence: float

class CandidateScore(BaseModel):
    id: str
    candidate_id: str
    jd_id: str
    composite_score: int
    rank: Optional[int] = None
    dimension_scores: DimensionScores
    criteria_met: List[CriteriaMet]
    justification: str
    strengths: List[str]
    risks: List[str]
    near_miss_flag: bool
    bias_audit_passed: bool
    scored_at: str
    model_version: str
