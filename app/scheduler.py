import asyncio
import logging
from .db import AsyncSessionLocal
from .etl import ingest_budget, ingest_kpi, ingest_manpower, ingest_project_update

logger = logging.getLogger('governance.scheduler')
REFRESH_INTERVAL_SECONDS = 86400


def start_scheduler() -> None:
    asyncio.create_task(_scheduler_loop())


async def _scheduler_loop() -> None:
    while True:
        await _refresh_cycle()
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


async def _refresh_cycle() -> None:
    async with AsyncSessionLocal() as session:
        logger.info('daily refresh starting')
        await ingest_kpi(session, {
            'code': 'KPI_DAILY_SAMPLE',
            'name': 'Daily Sample KPI',
            'unit': 'percent',
            'department_code': 'HEALTH',
            'domain': 'health',
            'direction': 'up_good',
            'frequency': 'daily',
            'formula_note': 'generated sample ingestion',
        })
        await ingest_budget(session, {
            'department_code': 'HEALTH',
            'fiscal_year': '2025-26',
            'allocation_amount': 1000000.00,
            'released_amount': 100000.00,
            'status': 'approved',
        })
        await ingest_manpower(session, {
            'department_code': 'HEALTH',
            'role': 'Data Analyst',
            'headcount': 1,
            'category': 'support',
            'effective_date': '2026-01-01',
        })
        await ingest_project_update(session, {
            'project_code': 'PROJECT_HEALTH_01',
            'status': 'active',
        })
        logger.info('daily refresh completed')
