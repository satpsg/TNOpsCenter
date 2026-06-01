from datetime import datetime
from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Alert, District, Kpi, KpiValue, Project


async def check_health_rules(session: AsyncSession) -> List[Tuple[str, str, str, int, str]]:
    """
    Check health domain rules:
    - Hospital load > 85% => high severity alert
    Returns list of (alert_code, title, severity, district_id, message)
    """
    alerts = []
    stmt = select(
        KpiValue.district_id,
        Kpi.name,
        KpiValue.value,
        District.name.label('district_name'),
    ).join(
        Kpi, KpiValue.kpi_id == Kpi.id
    ).join(
        District, KpiValue.district_id == District.id
    ).where(
        (Kpi.domain == 'health') & (KpiValue.value > 85)
    ).order_by(
        KpiValue.recorded_at.desc()
    ).distinct(
        KpiValue.district_id, Kpi.id
    )

    rows = await session.execute(stmt)
    for row in rows:
        if row.district_id and row.value > 85:
            alert_code = f"HEALTH_LOAD_{row.district_id}"
            title = f"High hospital load in {row.district_name}"
            message = f"{row.name} at {row.value}% exceeds safe threshold"
            alerts.append((alert_code, title, "high", row.district_id, message))

    return alerts


async def check_agriculture_rules(session: AsyncSession) -> List[Tuple[str, str, str, int, str]]:
    """
    Check agriculture domain rules:
    - Rainfall deviation > 30% => medium severity alert
    """
    alerts = []
    stmt = select(
        KpiValue.district_id,
        Kpi.name,
        KpiValue.value,
        KpiValue.target_value,
        District.name.label('district_name'),
    ).join(
        Kpi, KpiValue.kpi_id == Kpi.id
    ).join(
        District, KpiValue.district_id == District.id
    ).where(
        Kpi.domain == 'agriculture'
    ).order_by(
        KpiValue.recorded_at.desc()
    ).distinct(
        KpiValue.district_id, Kpi.id
    )

    rows = await session.execute(stmt)
    for row in rows:
        if row.district_id and row.target_value and row.target_value > 0:
            deviation = abs(float(row.value or 0) - float(row.target_value)) / float(row.target_value)
            if deviation > 0.30:
                alert_code = f"AGR_RAIN_{row.district_id}"
                title = f"Rainfall anomaly in {row.district_name}"
                message = f"{row.name} deviates {round(deviation * 100, 1)}% from target"
                alerts.append((alert_code, title, "medium", row.district_id, message))

    return alerts


async def check_infrastructure_rules(session: AsyncSession) -> List[Tuple[str, str, str, int, str]]:
    """
    Check infrastructure domain rules:
    - Project delay > 30 days => high severity alert
    """
    alerts = []
    from datetime import timedelta, date
    today = date.today()
    delay_threshold = timedelta(days=30)

    stmt = select(
        Project.id,
        Project.code,
        Project.name,
        Project.target_end_date,
        Project.district_id,
        District.name.label('district_name'),
    ).join(
        District, Project.district_id == District.id
    ).where(
        (Project.status == 'active') & (Project.target_end_date < today)
    )

    rows = await session.execute(stmt)
    for row in rows:
        if row.district_id and row.target_end_date:
            delay_days = (today - row.target_end_date).days
            if delay_days > 30:
                alert_code = f"INFRA_DELAY_{row.id}"
                title = f"Project delay: {row.name}"
                message = f"Project {row.code} is {delay_days} days overdue"
                alerts.append((alert_code, title, "high", row.district_id, message))

    return alerts


async def trigger_alerts(session: AsyncSession) -> int:
    """
    Evaluate all rules and create new alerts for breaches.
    Returns count of new alerts created.
    """
    all_alerts = []
    all_alerts.extend(await check_health_rules(session))
    all_alerts.extend(await check_agriculture_rules(session))
    all_alerts.extend(await check_infrastructure_rules(session))

    created_count = 0
    for alert_code, title, severity, district_id, message in all_alerts:
        existing = await session.scalar(
            select(func.count(Alert.id)).where(
                (Alert.alert_code == alert_code) & (Alert.status == 'open')
            )
        )
        if not existing:
            alert = Alert(
                alert_code=alert_code,
                title=title,
                severity=severity,
                district_id=district_id,
                description=message,
                status='open',
                triggered_at=datetime.utcnow(),
            )
            session.add(alert)
            created_count += 1

    if created_count > 0:
        await session.commit()

    return created_count
