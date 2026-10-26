import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Student


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        engine.dispose()


def test_create_student(test_db):
    def override_get_db():
        with Session(test_db) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/students",
                json={
                    "name": "Anna",
                    "email": "anna@example.com",
                },
            )

        assert response.status_code == 201

        data = response.json()
        assert isinstance(data["id"], int)
        assert data["name"] == "Anna"
        assert data["email"] == "anna@example.com"

        with Session(test_db) as db:
            student = db.scalar(
                select(Student).where(Student.id == data["id"])
            )

            assert student is not None
            assert student.name == "Anna"
            assert student.email == "anna@example.com"
    finally:
        app.dependency_overrides.clear()


def test_invalid_email(test_db):
    def override_get_db():
        with Session(test_db) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/students",
                json={
                    "name": "Anna",
                    "email": "invalid-email",
                },
            )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_empty_name(test_db):
    def override_get_db():
        with Session(test_db) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/students",
                json={
                    "name": "   ",
                    "email": "anna@example.com",
                },
            )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_duplicate_email(test_db):
    def override_get_db():
        with Session(test_db) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            student = {
                "name": "Anna",
                "email": "anna@example.com",
            }

            first_response = client.post("/students", json=student)
            second_response = client.post("/students", json=student)

        assert first_response.status_code == 201
        assert second_response.status_code == 409
        assert second_response.json() == {
            "detail": "Student with this email already exists"
        }
    finally:
        app.dependency_overrides.clear()