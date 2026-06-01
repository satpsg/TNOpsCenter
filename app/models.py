import enum
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Computed,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    text,
)
from sqlalchemy.orm import relationship
from .db import Base


class KpiDomain(str, enum.Enum):
    health = 'health'
    education = 'education'
    agriculture = 'agriculture'
    infrastructure = 'infrastructure'
    economy = 'economy'
    finance = 'finance'


class KpiDirection(str, enum.Enum):
    up_good = 'up_good'
    down_good = 'down_good'


class FrequencyUnit(str, enum.Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    quarterly = 'quarterly'
    yearly = 'yearly'


class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    projects = relationship('Project', back_populates='department')
    kpis = relationship('Kpi', back_populates='department')
    budget_allocations = relationship('BudgetAllocation', back_populates='department')
    manpower = relationship('Manpower', back_populates='department')
    alerts = relationship('Alert', back_populates='department')


class District(Base):
    __tablename__ = 'districts'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    region = Column(String(64))
    population = Column(Integer)
    state = Column(String(64), nullable=False, server_default=text("'Tamil Nadu'"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    projects = relationship('Project', back_populates='district')
    manpower = relationship('Manpower', back_populates='district')
    alerts = relationship('Alert', back_populates='district')
    kpi_values = relationship('KpiValue', back_populates='district')


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    district_id = Column(Integer, ForeignKey('districts.id'))
    start_date = Column(Date)
    target_end_date = Column(Date)
    status = Column(String(64), nullable=False, server_default=text("'planned'"))
    citizen_impact = Column(Integer, nullable=False)
    urgency = Column(Integer, nullable=False)
    economic_benefit = Column(Integer, nullable=False)
    feasibility = Column(Integer, nullable=False)
    impact_score = Column(
        Numeric(5, 2),
        Computed(
            '(citizen_impact * 0.35 + urgency * 0.25 + economic_benefit * 0.25 + feasibility * 0.15)',
            persisted=True,
        ),
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    department = relationship('Department', back_populates='projects')
    district = relationship('District', back_populates='projects')
    kpi_values = relationship('KpiValue', back_populates='project')
    budget_allocations = relationship('BudgetAllocation', back_populates='project')
    manpower = relationship('Manpower', back_populates='project')
    alerts = relationship('Alert', back_populates='project')

    __table_args__ = (
        CheckConstraint('citizen_impact BETWEEN 1 AND 10'),
        CheckConstraint('urgency BETWEEN 1 AND 10'),
        CheckConstraint('economic_benefit BETWEEN 1 AND 10'),
        CheckConstraint('feasibility BETWEEN 1 AND 10'),
    )


class Kpi(Base):
    __tablename__ = 'kpis'

    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    unit = Column(String(64), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    domain = Column(SAEnum(KpiDomain), nullable=False)
    direction = Column(SAEnum(KpiDirection), nullable=False)
    frequency = Column(SAEnum(FrequencyUnit), nullable=False)
    formula_note = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    department = relationship('Department', back_populates='kpis')
    values = relationship('KpiValue', back_populates='kpi')
    alerts = relationship('Alert', back_populates='kpi')


class KpiValue(Base):
    __tablename__ = 'kpi_values'

    id = Column(Integer, primary_key=True)
    kpi_id = Column(Integer, ForeignKey('kpis.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    district_id = Column(Integer, ForeignKey('districts.id'))
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    value = Column(Numeric(18, 4), nullable=False)
    target_value = Column(Numeric(18, 4))
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    kpi = relationship('Kpi', back_populates='values')
    project = relationship('Project', back_populates='kpi_values')
    district = relationship('District', back_populates='kpi_values')


class BudgetAllocation(Base):
    __tablename__ = 'budget_allocations'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    fiscal_year = Column(String(16), nullable=False)
    allocation_amount = Column(Numeric(18, 2), nullable=False)
    released_amount = Column(Numeric(18, 2), nullable=False, server_default=text('0'))
    status = Column(String(64), nullable=False, server_default=text("'approved'"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    project = relationship('Project', back_populates='budget_allocations')
    department = relationship('Department', back_populates='budget_allocations')


class Manpower(Base):
    __tablename__ = 'manpower'

    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    district_id = Column(Integer, ForeignKey('districts.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
    role = Column(String(128), nullable=False)
    headcount = Column(Integer, nullable=False)
    category = Column(String(64), nullable=False)
    effective_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    department = relationship('Department', back_populates='manpower')
    district = relationship('District', back_populates='manpower')
    project = relationship('Project', back_populates='manpower')


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    alert_code = Column(String(32), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    department_id = Column(Integer, ForeignKey('departments.id'))
    district_id = Column(Integer, ForeignKey('districts.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
    kpi_id = Column(Integer, ForeignKey('kpis.id'))
    severity = Column(String(32), nullable=False, server_default=text("'medium'"))
    status = Column(String(32), nullable=False, server_default=text("'open'"))
    triggered_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    resolved_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    department = relationship('Department', back_populates='alerts')
    district = relationship('District', back_populates='alerts')
    project = relationship('Project', back_populates='alerts')
    kpi = relationship('Kpi', back_populates='alerts')
