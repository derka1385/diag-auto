import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
import pytest
from fastapi.testclient import TestClient
from app.database.models import Base
from app.database.session import SessionLocal, engine
from app.main import app
from app.seed import seed

@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    seed(db)
    db.close()
    yield

@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)
