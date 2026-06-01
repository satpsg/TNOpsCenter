from datetime import timedelta
from typing import Any, Dict, List
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Alert, District, Kpi, KpiValue, Project


async def _kpi_trends(session: AsyncSession) -> List[Dict[str, Any]]:
    last7 = func.now() - text("interval '7 days'")
    last30 = func.now() - text("interval '30 days'")
    latest = (
        select(KpiValue.kpi_id, func.max(KpiValue.recorded_at).label('recorded_at'))
        .group_by(KpiValue.kpi_id)
        .subquery()
    )
    current = (
        select(KpiValue.kpi_id, KpiValue.value.label('latest'))
        .join(latest, (KpiValue.kpi_id == latest.c.kpi_id) & (KpiValue.recorded_at == latest.c.recorded_at))
        .subquery()
    )
    avg7 = (
        select(KpiValue.kpi_id, func.avg(KpiValue.value).label('avg7'))
        .where(KpiValue.recorded_at >= last7)
        .group_by(KpiValue.kpi_id)
        .subquery()
    )
    avg30 = (
        select(KpiValue.kpi_id, func.avg(KpiValue.value).label('avg30'))
        .where(KpiValue.recorded_at >= last30)
        .group_by(KpiValue.kpi_id)
        .subquery()
    )
    stmt = (
        select(
            Kpi.id,
            Kpi.name,
            Kpi.unit,
            current.c.latest,
            avg7.c.avg7,
            avg30.c.avg30,
            Kpi.domain,
            Kpi.direction,
        )
        .join(current, Kpi.id == current.c.kpi_id)
        .outerjoin(avg7, Kpi.id == avg7.c.kpi_id)
        .outerjoin(avg30, Kpi.id == avg30.c.kpi_id)
        .order_by(current.c.latest.desc())
        .limit(8)
    )
    rows = await session.execute(stmt)
    result = []
    for row in rows:
        latest_value = float(row.latest) if row.latest is not None else None
        avg7_value = float(row.avg7) if row.avg7 is not None else None
        avg30_value = float(row.avg30) if row.avg30 is not None else None
        result.append(
            {
                'kpi_id': row.id,
                'name': row.name,
                'unit': row.unit,
                'domain': row.domain.value,
                'direction': row.direction.value,
                'latest': latest_value,
                'trend_7d': None if avg7_value is None else round(latest_value - avg7_value, 2),
                'trend_30d': None if avg30_value is None else round(latest_value - avg30_value, 2),
            }
        )
    return result


async def summary(session: AsyncSession) -> Dict[str, Any]:
    kpi_cards = await _kpi_trends(session)
    project_count = await session.scalar(select(func.count()).select_from(Project))
    alert_count = await session.scalar(select(func.count()).select_from(Alert).where(Alert.status == 'open'))
    return {
        'kpi_cards': kpi_cards,
        'project_count': project_count or 0,
        'open_alerts': alert_count or 0,
    }


async def district_heatmap(session: AsyncSession) -> List[Dict[str, Any]]:
    project_stats = (
        select(
            Project.district_id,
            func.count().label('total_projects'),
            func.sum(case((Project.status == 'active', 1), else_=0)).label('active_projects'),
        )
        .group_by(Project.district_id)
        .subquery()
    )
    alert_stats = (
        select(
            Alert.district_id,
            func.count().label('open_alerts'),
        )
        .where(Alert.status == 'open')
        .group_by(Alert.district_id)
        .subquery()
    )
    stmt = (
        select(
            District.id,
            District.name,
            District.code,
            District.region,
            func.coalesce(project_stats.c.total_projects, 0).label('total_projects'),
            func.coalesce(project_stats.c.active_projects, 0).label('active_projects'),
            func.coalesce(alert_stats.c.open_alerts, 0).label('open_alerts'),
        )
        .outerjoin(project_stats, District.id == project_stats.c.district_id)
        .outerjoin(alert_stats, District.id == alert_stats.c.district_id)
    )
    rows = await session.execute(stmt)
    result = []
    for row in rows:
        total = row.total_projects or 0
        active = row.active_projects or 0
        alerts = row.open_alerts or 0
        project_score = 100.0 * active / total if total else 20.0
        penalty = min(alerts * 8.0, 60.0)
        score = max(0.0, min(100.0, project_score - penalty + 20.0))
        result.append(
            {
                'district_id': row.id,
                'name': row.name,
                'code': row.code,
                'region': row.region,
                'performance_score': round(score, 2),
                'active_projects': active,
                'total_projects': total,
                'open_alerts': alerts,
            }
        )
    return result


async def projects_top(session: AsyncSession) -> List[Dict[str, Any]]:
    stmt = (
        select(
            Project.id,
            Project.code,
            Project.name,
            Project.status,
            Project.impact_score,
            Project.citizen_impact,
            Project.urgency,
            Project.economic_benefit,
            Project.feasibility,
        )
        .order_by(Project.impact_score.desc())
        .limit(10)
    )
    rows = await session.execute(stmt)
    return [
        {
            'project_id': row.id,
            'code': row.code,
            'name': row.name,
            'status': row.status,
            'impact_score': float(row.impact_score or 0),
            'citizen_impact': row.citizen_impact,
            'urgency': row.urgency,
            'economic_benefit': row.economic_benefit,
            'feasibility': row.feasibility,
        }
        for row in rows
    ]


async def alerts_latest(session: AsyncSession) -> List[Dict[str, Any]]:
    stmt = (
        select(
            Alert.id,
            Alert.alert_code,
            Alert.title,
            Alert.severity,
            Alert.status,
            Alert.triggered_at,
        )
        .order_by(Alert.triggered_at.desc())
        .limit(10)
    )
    rows = await session.execute(stmt)
    return [
        {
            'alert_id': row.id,
            'code': row.alert_code,
            'title': row.title,
            'severity': row.severity,
            'status': row.status,
            'triggered_at': row.triggered_at.isoformat() if row.triggered_at else None,
        }
        for row in rows
    ]
