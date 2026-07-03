import logging
import sqlite3

import db
from config_loader import load_config
from notifiers.email import send_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    config = load_config()
    db.init_db()

    with sqlite3.connect(db.DB_PATH) as conn:
        jobs = db.get_digest_jobs(conn)

    if not jobs:
        logger.info("digest queue empty — skipping email")
        return

    logger.info("sending digest with %d jobs to %s", len(jobs), config.notification.email_to)
    try:
        send_digest(jobs, config.notification.email_to)
    except Exception as exc:
        logger.error("digest send failed — queue preserved for retry: %s", exc)
        return

    with sqlite3.connect(db.DB_PATH) as conn:
        db.clear_digest(conn)
    logger.info("digest queue cleared")


if __name__ == "__main__":
    run()
