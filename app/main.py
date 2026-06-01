import logging
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .alert_worker import start_alert_worker
from .db import get_db, init_db
from .analytics import budget_analytics, gap_analysis, manpower_analytics, priority_scoring
from .dashboard import alerts_latest, district_heatmap, projects_top, summary
from .etl import ingest_budget, ingest_kpi, ingest_manpower, ingest_project_update
from .schemas import (
    AcknowledgeRequest,
    AlertResponse,
    BudgetAnalytics,
    BudgetIngest,
    GapAnalysis,
    IngestionStatus,
    KpiIngest,
    ManpowerAnalytics,
    ManpowerIngest,
    PriorityScoring,
    ProjectUpdateIngest,
)
from .scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('governance.backend')
app = FastAPI(title='Governance Analytics Dashboard')


@app.on_event('startup')
async def startup():
    await init_db()
    start_scheduler()
    start_alert_worker()


@app.post('/ingest/kpi', response_model=IngestionStatus)
async def ingest_kpi_endpoint(payload: KpiIngest, db: AsyncSession = Depends(get_db)):
    result = await ingest_kpi(db, payload.dict())
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@app.post('/ingest/budget', response_model=IngestionStatus)
async def ingest_budget_endpoint(payload: BudgetIngest, db: AsyncSession = Depends(get_db)):
    result = await ingest_budget(db, payload.dict())
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@app.post('/ingest/manpower', response_model=IngestionStatus)
async def ingest_manpower_endpoint(payload: ManpowerIngest, db: AsyncSession = Depends(get_db)):
    result = await ingest_manpower(db, payload.dict())
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@app.post('/ingest/project_update', response_model=IngestionStatus)
async def ingest_project_update_endpoint(payload: ProjectUpdateIngest, db: AsyncSession = Depends(get_db)):
    result = await ingest_project_update(db, payload.dict())
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@app.get('/summary')
async def summary_endpoint(db: AsyncSession = Depends(get_db)):
    return await summary(db)


@app.get('/district/heatmap')
async def district_heatmap_endpoint(db: AsyncSession = Depends(get_db)):
    return await district_heatmap(db)


@app.get('/projects/top')
async def projects_top_endpoint(db: AsyncSession = Depends(get_db)):
    return await projects_top(db)


@app.get('/alerts/latest')
async def alerts_latest_endpoint(db: AsyncSession = Depends(get_db)):
    return await alerts_latest(db)


@app.get('/analytics/budget', response_model=BudgetAnalytics)
async def budget_analytics_endpoint(db: AsyncSession = Depends(get_db)):
    return await budget_analytics(db)


@app.get('/analytics/manpower', response_model=ManpowerAnalytics)
async def manpower_analytics_endpoint(db: AsyncSession = Depends(get_db)):
    return await manpower_analytics(db)


@app.get('/analytics/gap', response_model=GapAnalysis)
async def gap_analysis_endpoint(db: AsyncSession = Depends(get_db)):
    return await gap_analysis(db)


@app.get('/analytics/priorities', response_model=PriorityScoring)
async def priority_scoring_endpoint(db: AsyncSession = Depends(get_db)):
    return await priority_scoring(db)


@app.get('/alerts/live')
async def alerts_live_endpoint(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from .models import Alert
    stmt = (
        select(
            Alert.id,
            Alert.alert_code,
            Alert.title,
            Alert.description,
            Alert.severity,
            Alert.district_id,
            Alert.status,
            Alert.triggered_at,
            Alert.acknowledged_at,
        )
        .where(Alert.status.in_(['open', 'acknowledged']))
        .order_by(Alert.triggered_at.desc())
        .limit(50)
    )
    rows = await db.execute(stmt)
    return [
        {
            'alert_id': row.id,
            'alert_code': row.alert_code,
            'title': row.title,
            'description': row.description,
            'severity': row.severity,
            'district_id': row.district_id,
            'status': row.status,
            'triggered_at': row.triggered_at.isoformat() if row.triggered_at else None,
            'acknowledged_at': row.acknowledged_at.isoformat() if row.acknowledged_at else None,
        }
        for row in rows
    ]


@app.post('/alerts/acknowledge', response_model=IngestionStatus)
async def acknowledge_alert_endpoint(payload: AcknowledgeRequest, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    from sqlalchemy import update
    from .models import Alert
    stmt = (
        update(Alert)
        .where(Alert.id == payload.alert_id)
        .values(status='acknowledged', acknowledged_at=datetime.utcnow())
    )
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount > 0:
        return IngestionStatus(success=True, message='Alert acknowledged', record_id=payload.alert_id)
    else:
        return IngestionStatus(success=False, message='Alert not found')
