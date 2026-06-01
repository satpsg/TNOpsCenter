import logging
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import BudgetAllocation, Department, District, Kpi, Project, Manpower
from .schemas import (
    BudgetIngest,
    IngestionStatus,
    KpiIngest,
    ManpowerIngest,
    ProjectUpdateIngest,
)

logger = logging.getLogger('governance.ingest')
logger.setLevel(logging.INFO)


async def _resolve_department(session: AsyncSession, payload: Dict[str, Any]) -> Optional[int]:
    if payload.get('department_id'):
        return payload['department_id']
    code = payload.get('department_code')
    if not code:
        return None
    result = await session.execute(select(Department).where(Department.code == code))
    department = result.scalar_one_or_none()
    if department:
        return department.id
    if payload.get('name'):
        department = Department(code=code, name=payload['name'])
        session.add(department)
        await session.flush()
        return department.id
    return None


async def _resolve_district(session: AsyncSession, payload: Dict[str, Any]) -> Optional[int]:
    if payload.get('district_id'):
        return payload['district_id']
    code = payload.get('district_code')
    if not code:
        return None
    result = await session.execute(select(District).where(District.code == code))
    district = result.scalar_one_or_none()
    if district:
        return district.id
    if payload.get('name'):
        district = District(code=code, name=payload['name'])
        session.add(district)
        await session.flush()
        return district.id
    return None


async def _resolve_project(session: AsyncSession, payload: Dict[str, Any]) -> Optional[int]:
    if payload.get('project_id'):
        return payload['project_id']
    code = payload.get('project_code')
    if not code:
        return None
    result = await session.execute(select(Project).where(Project.code == code))
    project = result.scalar_one_or_none()
    if project:
        return project.id
    return None


async def ingest_kpi(session: AsyncSession, raw: Dict[str, Any]) -> IngestionStatus:
    try:
        payload = KpiIngest.parse_obj(raw)
        dept_id = await _resolve_department(session, raw)
        if not dept_id:
            return IngestionStatus(success=False, message='department_id or department_code required')
        result = await session.execute(select(Kpi).where(Kpi.code == payload.code))
        existing = result.scalar_one_or_none()
        if existing:
            existing.name = payload.name
            existing.description = payload.description
            existing.unit = payload.unit
            existing.department_id = dept_id
            existing.domain = payload.domain
            existing.direction = payload.direction
            existing.frequency = payload.frequency
            existing.formula_note = payload.formula_note
            await session.commit()
            return IngestionStatus(success=True, message='kpi updated', record_id=existing.id)
        row = Kpi(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            unit=payload.unit,
            department_id=dept_id,
            domain=payload.domain,
            direction=payload.direction,
            frequency=payload.frequency,
            formula_note=payload.formula_note,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return IngestionStatus(success=True, message='kpi created', record_id=row.id)
    except Exception as exc:
        await session.rollback()
        logger.error('KPI ingest failed: %s', exc)
        return IngestionStatus(success=False, message=str(exc))


async def ingest_budget(session: AsyncSession, raw: Dict[str, Any]) -> IngestionStatus:
    try:
        payload = BudgetIngest.parse_obj(raw)
        dept_id = await _resolve_department(session, raw)
        if not dept_id:
            return IngestionStatus(success=False, message='department_id or department_code required')
        project_id = await _resolve_project(session, raw)
        result = await session.execute(select(BudgetAllocation).where(
            BudgetAllocation.project_id == project_id,
            BudgetAllocation.department_id == dept_id,
            BudgetAllocation.fiscal_year == payload.fiscal_year,
        ))
        existing = result.scalar_one_or_none()
        if existing:
            existing.released_amount = payload.released_amount
            existing.status = payload.status
            existing.allocation_amount = payload.allocation_amount
            await session.commit()
            return IngestionStatus(success=True, message='budget updated', record_id=existing.id)
        row = BudgetAllocation(
            project_id=project_id,
            department_id=dept_id,
            fiscal_year=payload.fiscal_year,
            allocation_amount=payload.allocation_amount,
            released_amount=payload.released_amount,
            status=payload.status,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return IngestionStatus(success=True, message='budget created', record_id=row.id)
    except Exception as exc:
        await session.rollback()
        logger.error('Budget ingest failed: %s', exc)
        return IngestionStatus(success=False, message=str(exc))


async def ingest_manpower(session: AsyncSession, raw: Dict[str, Any]) -> IngestionStatus:
    try:
        payload = ManpowerIngest.parse_obj(raw)
        dept_id = await _resolve_department(session, raw)
        if not dept_id:
            return IngestionStatus(success=False, message='department_id or department_code required')
        district_id = await _resolve_district(session, raw)
        project_id = await _resolve_project(session, raw)
        row = Manpower(
            department_id=dept_id,
            district_id=district_id,
            project_id=project_id,
            role=payload.role,
            headcount=payload.headcount,
            category=payload.category,
            effective_date=payload.effective_date,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return IngestionStatus(success=True, message='manpower created', record_id=row.id)
    except Exception as exc:
        await session.rollback()
        logger.error('Manpower ingest failed: %s', exc)
        return IngestionStatus(success=False, message=str(exc))


async def ingest_project_update(session: AsyncSession, raw: Dict[str, Any]) -> IngestionStatus:
    try:
        payload = ProjectUpdateIngest.parse_obj(raw)
        project_id = await _resolve_project(session, raw)
        if not project_id and not payload.project_id:
            return IngestionStatus(success=False, message='project_id or project_code required')
        project_id = project_id or payload.project_id
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return IngestionStatus(success=False, message='project not found')
        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.department_id or payload.department_code:
            dept_id = await _resolve_department(session, raw)
            if dept_id:
                project.department_id = dept_id
        if payload.district_id or payload.district_code:
            district_id = await _resolve_district(session, raw)
            if district_id:
                project.district_id = district_id
        if payload.start_date is not None:
            project.start_date = payload.start_date
        if payload.target_end_date is not None:
            project.target_end_date = payload.target_end_date
        if payload.status is not None:
            project.status = payload.status
        if payload.citizen_impact is not None:
            project.citizen_impact = payload.citizen_impact
        if payload.urgency is not None:
            project.urgency = payload.urgency
        if payload.economic_benefit is not None:
            project.economic_benefit = payload.economic_benefit
        if payload.feasibility is not None:
            project.feasibility = payload.feasibility
        await session.commit()
        await session.refresh(project)
        return IngestionStatus(success=True, message='project updated', record_id=project.id)
    except Exception as exc:
        await session.rollback()
        logger.error('Project update failed: %s', exc)
        return IngestionStatus(success=False, message=str(exc))
