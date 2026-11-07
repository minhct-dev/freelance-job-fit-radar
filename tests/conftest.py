import pytest
import os
from app.utils.settings import settings
from app.services.database import init_db

@pytest.fixture(autouse=True)
def setup_db():
    # Use a separate test database
    test_db = "test_radar.db"
    original_db_url = settings.database_url
    settings.database_url = f"sqlite:///{test_db}"
    
    # Initialize the test database
    init_db(settings.database_url)
    
    yield
    
    # Cleanup
    settings.database_url = original_db_url
    if os.path.exists(test_db):
        os.remove(test_db)
