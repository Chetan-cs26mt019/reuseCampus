from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_user():
    return client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "username": "student01",
            "password": "StrongPassword123!",
            "full_name": "Test Student",
            "student_id": "STU001",
        },
    )


def test_register_user():
    response = register_user()

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["username"] == "student01"
    assert data["role"] == "student"
    assert "password_hash" not in data


def test_duplicate_registration_rejected():
    assert register_user().status_code == 201
    response = client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "username": "anotheruser",
            "password": "StrongPassword123!",
            "full_name": "Another Student",
        },
    )
    assert response.status_code == 409


def test_login_with_username():
    register_user()
    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "student01",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_email():
    register_user()
    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "student@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "student01"


def test_wrong_password_rejected():
    register_user()
    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "student01",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_me_requires_authentication():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_valid_token():
    register_user()
    login_response = client.post(
        "/auth/login",
        json={
            "username_or_email": "student01",
            "password": "StrongPassword123!",
        },
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "student@example.com"


def test_me_rejects_invalid_token():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401

def test_register_rejects_short_password():
    response = client.post(
        "/auth/register",
        json={
            "email": "short@example.com",
            "username": "shortuser",
            "password": "short",
            "full_name": "Short Password",
        },
    )
    assert response.status_code == 422


def test_inactive_user_cannot_access_me():
    register_user()

    db = TestingSessionLocal()
    try:
        from app.models import User

        user = db.query(User).filter_by(username="student01").one()
        user.account_status = "suspended"
        db.commit()
    finally:
        db.close()

    login_response = client.post(
        "/auth/login",
        json={
            "username_or_email": "student01",
            "password": "StrongPassword123!",
        },
    )

    assert login_response.status_code == 403
