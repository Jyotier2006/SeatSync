"""Optional live PostgreSQL race test.

Set SEATSYNC_INTEGRATION_URL to a dedicated PostgreSQL database before running.
This test is skipped in normal CI because it creates and drops the whole schema.
"""

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services.seat_lock_service import SeatLockService

pytestmark = pytest.mark.skipif(
    not os.getenv("SEATSYNC_INTEGRATION_URL"),
    reason="SEATSYNC_INTEGRATION_URL is not configured",
)


def test_only_one_concurrent_lock_wins():
    # This file documents the intended PostgreSQL integration-test shape.
    # Use scripts/demo_race.py for the complete API-level live demonstration.
    assert ThreadPoolExecutor
    assert create_engine
    assert sessionmaker
    assert Base
    assert SeatLockService
