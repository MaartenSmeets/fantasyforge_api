from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create a test database
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_user():
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
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_create_device_for_user():
    device_data = {
        "name": "iPhone",
        "model": "12 Pro"
    }
    response = client.post("/users/1/devices/", json=device_data)
    assert response.status_code == 200
    assert response.json()["name"] == device_data["name"]
    assert response.json()["model"] == device_data["model"]


def test_read_devices():
    response = client.get("/devices/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_image():
    response = client.get("/image/test.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_get_images():
    response = client.get("/image/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
