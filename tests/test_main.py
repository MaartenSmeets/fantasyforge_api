"""
This module contains test cases for the main.py module of the Fantasy Forge API.

The test cases cover various functionalities such as creating a user, getting all users,
reading a user, creating a device for a user, getting all devices, getting an image,
and getting all images.
"""
import logging
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Create a temporary in-memory SQLite database for testing
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
logger = logging.getLogger(__name__)
# Patch the database connection in the main module to use the temporary database

client = TestClient(app)


@patch("main.get_db", return_value=SessionLocal())
def test_create_user(main):
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