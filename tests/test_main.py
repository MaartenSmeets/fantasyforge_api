"""
This module contains unit tests for the main module of the Fantasy Forge API.
"""

import logging
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from database import Base

# Create a temporary in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)


# Patch the database connection in the main module to use the temporary database
def override_get_db():
    """
    Override the get_db function to provide a session for testing purposes.

    Returns:
        SessionLocal: The session object for database operations.
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_user():
    """
    Test case for creating a user.
    """
    user_data = {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "password": "password123",
        "role": "user"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"
    assert response.json()["email"] == "johndoe@example.com"


def test_get_users():
    """
    Test case for getting all users.
    """
    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_read_user():
    """
    Test case for reading a user.
    """
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_create_device_for_user():
    """
    Test case for creating a device for a user.
    """
    device_data = {
        "name": "iPhone",
        "model": "12 Pro"
    }
    response = client.post("/users/1/devices/", json=device_data)
    assert response.status_code == 200
    assert response.json()["name"] == "iPhone"
    assert response.json()["model"] == "12 Pro"


def test_read_devices():
    """
    Test case for getting all devices.
    """
    response = client.get("/devices/")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_image():
    """
    Test case for getting an image.
    """
    response = client.get("/image/test_image.png")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/png"


def test_get_images():
    """
    Test case for getting all images.
    """
    response = client.get("/image/")
    assert response.status_code == 200
    assert len(response.json()) > 0
