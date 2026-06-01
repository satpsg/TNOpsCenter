from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, PositiveInt, condecimal, constr


class KpiDomain(str, Enum):
    health = 'health'
    education = 'education'
    agriculture = 'agriculture'
    infrastructure = 'infrastructure'
    economy = 'economy'
    finance = 'finance'


class KpiDirection(str, Enum):
    up_good = 'up_good'
    down_good = 'down_good'


class FrequencyUnit(str, Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    quarterly = 'quarterly'
    yearly = 'yearly'


class IngestionStatus(BaseModel):
    success: bool
    message: str
    record_id: Optional[int] = None


class KpiIngest(BaseModel):
    code: constr(strip_whitespace=True, min_length=1, max_length=32)
    name: constr(strip_whitespace=True, min_length=1, max_length=200)
    description: Optional[str]
    unit: constr(strip_whitespace=True, min_length=1, max_length=64)
    department_id: Optional[int]
    department_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=16)]
    domain: KpiDomain
    direction: KpiDirection
    frequency: FrequencyUnit
    formula_note: Optional[str]


class BudgetIngest(BaseModel):
    project_id: Optional[int]
    project_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=32)]
    department_id: Optional[int]
    department_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=16)]
    fiscal_year: constr(strip_whitespace=True, min_length=4, max_length=16)
    allocation_amount: condecimal(gt=-1)
    released_amount: Optional[condecimal(gt=-1)] = 0
    status: Optional[constr(strip_whitespace=True, max_length=64)] = 'approved'


class ManpowerIngest(BaseModel):
    department_id: Optional[int]
    department_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=16)]
    district_id: Optional[int]
    district_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=16)]
    project_id: Optional[int]
    project_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=32)]
    role: constr(strip_whitespace=True, min_length=1, max_length=128)
    headcount: PositiveInt
    category: constr(strip_whitespace=True, min_length=1, max_length=64)
    effective_date: date


class ProjectUpdateIngest(BaseModel):
    project_id: Optional[int]
    project_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=32)]
    name: Optional[constr(strip_whitespace=True, max_length=200)]
    description: Optional[str]
    department_id: Optional[int]
    department_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=16)]
    district_id: Optional[int]
    district_code: Optional[constr(strip_whitespace=True, min_length=1, max_length=16)]
    start_date: Optional[date]
    target_end_date: Optional[date]
    status: Optional[constr(strip_whitespace=True, max_length=64)]
    citizen_impact: Optional[int] = Field(None, ge=1, le=10)
    urgency: Optional[int] = Field(None, ge=1, le=10)
    economic_benefit: Optional[int] = Field(None, ge=1, le=10)
    feasibility: Optional[int] = Field(None, ge=1, le=10)


class BudgetAggregationItem(BaseModel):
    department_id: Optional[int]
    department_name: Optional[str]
    fiscal_year: str
    project_id: Optional[int]
    project_code: Optional[str]
    project_name: Optional[str]
    allocated: float
    spent: float
    remaining: float


class BudgetAnalytics(BaseModel):
    departments: List[BudgetAggregationItem]
    projects: List[BudgetAggregationItem]


class ManpowerAnalyticsRow(BaseModel):
    department_id: Optional[int]
    department_name: Optional[str]
    district_id: Optional[int]
    district_name: Optional[str]
    required: int
    available: int
    unknown: int
    deficit: int


class ManpowerAnalytics(BaseModel):
    by_department: List[ManpowerAnalyticsRow]
    by_district: List[ManpowerAnalyticsRow]


class GapAnalysisRow(BaseModel):
    department_id: Optional[int]
    department_name: Optional[str]
    district_id: Optional[int]
    district_name: Optional[str]
    required: int
    available: int
    deficit: int
    deficit_score: float


class GapAnalysis(BaseModel):
    by_department: List[GapAnalysisRow]
    by_district: List[GapAnalysisRow]


class PriorityScoringRow(BaseModel):
    project_id: int
    project_code: Optional[str]
    project_name: Optional[str]
    impact: float
    urgency: int
    economic_benefit: int
    feasibility: int
    required: int
    available: int
    resource_gap: float
    priority_score: float


class PriorityScoring(BaseModel):
    priorities: List[PriorityScoringRow]


class AlertResponse(BaseModel):
    alert_id: int
    alert_code: str
    title: str
    description: Optional[str]
    severity: str
    district_id: Optional[int]
    status: str
    triggered_at: str
    acknowledged_at: Optional[str]


class AcknowledgeRequest(BaseModel):
    alert_id: int


class RawIngestion(BaseModel):
    payload: dict
    source: Optional[str]
    received_at: Optional[datetime] = None
