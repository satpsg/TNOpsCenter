from typing import Any, Dict, List
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import BudgetAllocation, Department, District, Manpower, Project


def _is_required_category(category: str) -> bool:
    normalized = (category or '').strip().lower()
    return 'required' in normalized or 'need' in normalized or 'demand' in normalized


def _is_available_category(category: str) -> bool:
    normalized = (category or '').strip().lower()
    return 'available' in normalized or 'current' in normalized or 'existing' in normalized or 'assigned' in normalized


async def budget_analytics(session: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    stmt = (
        select(
            Department.id.label('department_id'),
            Department.name.label('department_name'),
            BudgetAllocation.fiscal_year,
            Project.id.label('project_id'),
            Project.code.label('project_code'),
            Project.name.label('project_name'),
            func.sum(BudgetAllocation.allocation_amount).label('allocated'),
            func.sum(BudgetAllocation.released_amount).label('spent'),
        )
        .join(Department, BudgetAllocation.department_id == Department.id)
        .outerjoin(Project, BudgetAllocation.project_id == Project.id)
        .group_by(Department.id, Department.name, BudgetAllocation.fiscal_year, Project.id, Project.code, Project.name)
    )
    rows = await session.execute(stmt)

    department_map: Dict[Any, Dict[str, Any]] = {}
    project_rows: List[Dict[str, Any]] = []
    for row in rows:
        allocated = float(row.allocated or 0)
        spent = float(row.spent or 0)
        remaining = round(allocated - spent, 2)

        department_key = (row.department_id, row.fiscal_year)
        dept_entry = department_map.get(department_key)
        if not dept_entry:
            dept_entry = {
                'department_id': row.department_id,
                'department_name': row.department_name,
                'fiscal_year': row.fiscal_year,
                'allocated': 0.0,
                'spent': 0.0,
                'remaining': 0.0,
            }
            department_map[department_key] = dept_entry
        dept_entry['allocated'] += allocated
        dept_entry['spent'] += spent
        dept_entry['remaining'] = round(dept_entry['allocated'] - dept_entry['spent'], 2)

        project_rows.append(
            {
                'project_id': row.project_id,
                'project_code': row.project_code,
                'project_name': row.project_name,
                'fiscal_year': row.fiscal_year,
                'allocated': allocated,
                'spent': spent,
                'remaining': remaining,
            }
        )

    return {
        'departments': [
            {
                'department_id': entry['department_id'],
                'department_name': entry['department_name'],
                'fiscal_year': entry['fiscal_year'],
                'allocated': round(entry['allocated'], 2),
                'spent': round(entry['spent'], 2),
                'remaining': round(entry['remaining'], 2),
            }
            for entry in department_map.values()
        ],
        'projects': project_rows,
    }


async def manpower_analytics(session: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    stmt = (
        select(
            Manpower.id,
            Manpower.headcount,
            Manpower.category,
            Department.id.label('department_id'),
            Department.name.label('department_name'),
            District.id.label('district_id'),
            District.name.label('district_name'),
        )
        .outerjoin(Department, Manpower.department_id == Department.id)
        .outerjoin(District, Manpower.district_id == District.id)
    )
    rows = await session.execute(stmt)

    dept_counts: Dict[int, Dict[str, Any]] = {}
    dist_counts: Dict[int, Dict[str, Any]] = {}

    for row in rows:
        category = row.category or ''
        required = row.headcount if _is_required_category(category) else 0
        available = row.headcount if _is_available_category(category) else 0
        unknown = 0
        if required == 0 and available == 0:
            unknown = row.headcount

        if row.department_id is not None:
            dept = dept_counts.setdefault(row.department_id, {
                'department_id': row.department_id,
                'department_name': row.department_name or 'Unknown',
                'required': 0,
                'available': 0,
                'unknown': 0,
            })
            dept['required'] += required
            dept['available'] += available
            dept['unknown'] += unknown

        if row.district_id is not None:
            dist = dist_counts.setdefault(row.district_id, {
                'district_id': row.district_id,
                'district_name': row.district_name or 'Unknown',
                'required': 0,
                'available': 0,
                'unknown': 0,
            })
            dist['required'] += required
            dist['available'] += available
            dist['unknown'] += unknown

    def normalize_group(entry: Dict[str, Any]) -> Dict[str, Any]:
        required = entry['required']
        available = entry['available'] if entry['available'] > 0 else entry['unknown']
        deficit = max(0, required - available)
        return {
            **entry,
            'available': available,
            'deficit': deficit,
        }

    return {
        'by_department': [normalize_group(entry) for entry in dept_counts.values()],
        'by_district': [normalize_group(entry) for entry in dist_counts.values()],
    }


async def gap_analysis(session: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    manpower_summary = await manpower_analytics(session)
    department_items: List[Dict[str, Any]] = []
    for item in manpower_summary['by_department']:
        required = item['required']
        available = item['available']
        deficit = max(0, required - available)
        score = round((deficit / required) if required else 0.0, 4)
        department_items.append(
            {
                'department_id': item['department_id'],
                'department_name': item['department_name'],
                'required': required,
                'available': available,
                'deficit': deficit,
                'deficit_score': round(score * 100, 2),
            }
        )

    district_items: List[Dict[str, Any]] = []
    for item in manpower_summary['by_district']:
        required = item['required']
        available = item['available']
        deficit = max(0, required - available)
        score = round((deficit / required) if required else 0.0, 4)
        district_items.append(
            {
                'district_id': item['district_id'],
                'district_name': item['district_name'],
                'required': required,
                'available': available,
                'deficit': deficit,
                'deficit_score': round(score * 100, 2),
            }
        )

    return {
        'by_department': department_items,
        'by_district': district_items,
    }


async def priority_scoring(session: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    manpower_subq = (
        select(
            Manpower.project_id.label('project_id'),
            func.sum(case((func.lower(Manpower.category).like('%required%') | func.lower(Manpower.category).like('%need%') | func.lower(Manpower.category).like('%demand%'), Manpower.headcount), else_=0)).label('required'),
            func.sum(case((func.lower(Manpower.category).like('%available%') | func.lower(Manpower.category).like('%current%') | func.lower(Manpower.category).like('%existing%') | func.lower(Manpower.category).like('%assigned%'), Manpower.headcount), else_=0)).label('available'),
        )
        .group_by(Manpower.project_id)
        .subquery()
    )

    stmt = (
        select(
            Project.id,
            Project.code,
            Project.name,
            Project.citizen_impact,
            Project.urgency,
            Project.economic_benefit,
            Project.feasibility,
            func.coalesce(manpower_subq.c.required, 0).label('required'),
            func.coalesce(manpower_subq.c.available, 0).label('available'),
        )
        .outerjoin(manpower_subq, Project.id == manpower_subq.c.project_id)
    )

    rows = await session.execute(stmt)
    priorities: List[Dict[str, Any]] = []
    for row in rows:
        required = int(row.required or 0)
        available = int(row.available or 0)
        gap_ratio = float(max(0, required - available) / required) if required else 0.0
        resource_gap = round(gap_ratio * 10, 2)
        priority_score = round(
            0.4 * float(row.citizen_impact or 0)
            + 0.25 * float(row.urgency or 0)
            + 0.15 * float(row.economic_benefit or 0)
            + 0.1 * float(row.feasibility or 0)
            + 0.1 * resource_gap,
            2,
        )
        priorities.append(
            {
                'project_id': row.id,
                'project_code': row.code,
                'project_name': row.name,
                'impact': float(row.citizen_impact or 0),
                'urgency': int(row.urgency or 0),
                'economic_benefit': int(row.economic_benefit or 0),
                'feasibility': int(row.feasibility or 0),
                'required': required,
                'available': available,
                'resource_gap': resource_gap,
                'priority_score': priority_score,
            }
        )

    priorities.sort(key=lambda entry: entry['priority_score'], reverse=True)
    return {'priorities': priorities}
