"""
This module contains unit tests for the main module of the Fantasy Forge API.

The tests cover various functionalities of the API, including creating users, reading users, 
creating devices for users, reading devices, and retrieving images.

The test cases are implemented using the FastAPI TestClient and SQLAlchemy for database operations.

To run the tests, execute this module using a test runner or by running the file directly.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create a test database
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    """
    Override the get_db function for testing purposes.

    Returns:
        TestingSessionLocal: The testing session local database connection.
    """
    db = TestingSessionLocal()
    try:
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
        "email": "john.doe@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    assert response.json()["name"] == user_data["name"]
    assert response.json()["email"] == user_data["email"]


def test_read_users():
    """
    Test case for reading all users.
    """
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_user():
    """
    Test case for reading a specific user.
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
    assert response.json()["name"] == device_data["name"]
    assert response.json()["model"] == device_data["model"]


def test_read_devices():
    """
    Test case for reading all devices.
    """
    response = client.get("/devices/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_image():
    """
    Test case for getting a specific image.
    """
    response = client.get("/image/test.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_get_images():
    """
    Test case for getting all images.
    """
    response = client.get("/image/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
