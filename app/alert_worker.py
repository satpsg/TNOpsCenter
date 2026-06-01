import asyncio
import logging
from datetime import datetime
from .alert_rules import trigger_alerts
from .db import AsyncSessionLocal

logger = logging.getLogger('governance.alerts')


async def alert_worker():
    """
    Background worker that periodically checks alert rules.
    Runs every 30 seconds to simulate real-time monitoring.
    """
    while True:
        try:
            async with AsyncSessionLocal() as session:
                created = await trigger_alerts(session)
                if created > 0:
                    logger.info(f"Alert worker triggered {created} new alerts at {datetime.utcnow().isoformat()}")
        except Exception as e:
            logger.error(f"Error in alert worker: {e}")

        await asyncio.sleep(30)


def start_alert_worker():
    """Start the alert worker in a background task."""
    try:
        asyncio.create_task(alert_worker())
        logger.info("Alert worker started")
    except Exception as e:
        logger.error(f"Failed to start alert worker: {e}")
