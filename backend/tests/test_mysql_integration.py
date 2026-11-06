import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db
from app.main import app
from app.models import Category

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is not configured",
)
def test_categories_endpoint_with_mysql():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    Category.__table__.create(engine, checkfirst=True)

    category_name = f"MySQL Integration {uuid.uuid4().hex[:12]}"

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestingSessionLocal() as db:
            db.add(Category(name=category_name, is_active=True))
            db.commit()

        with TestClient(app) as client:
            response = client.get("/categories")

        assert response.status_code == 200
        assert any(
            item["name"] == category_name
            for item in response.json()["items"]
        )

    finally:
        app.dependency_overrides.pop(get_db, None)

        with TestingSessionLocal() as db:
            category = db.scalar(
                select(Category).where(Category.name == category_name)
            )
            if category is not None:
                db.delete(category)
                db.commit()

        engine.dispose()
