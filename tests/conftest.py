import os
import pytest
from app.utils.settings import settings
from app.services.database import init_db


@pytest.fixture(autouse=True)
def setup_db():
    test_db = "test_radar.db"
    original_db_url = settings.database_url
    original_scheduler = settings.scheduler_enabled
    settings.database_url = f"sqlite:///{test_db}"
    settings.scheduler_enabled = False

    init_db(settings.database_url)

    yield

    settings.database_url = original_db_url
    settings.scheduler_enabled = original_scheduler
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass


@pytest.fixture
def db_file():
    filename = f"test_case_{os.urandom(6).hex()}.db"
    init_db(filename)
    yield filename
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except OSError:
            pass
