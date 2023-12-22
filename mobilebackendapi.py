from contextlib import asynccontextmanager
from typing import List, Optional, Dict

import sqlalchemy.types
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import json
from sqlalchemy import Column
from sqlmodel import create_engine, Session, SQLModel, Field, select
import logging

sqlite_file_name = "mobile_backgrounds.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup event")
    try:
        create_db_and_tables()
        yield
    finally:
        print("Shutdown event")


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)
log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
uvicorn.run(app, log_config=log_config)

security = HTTPBasic()


class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str
    api_key: str


class ListType(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.String

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value) if value is not None else []


class Image(SQLModel, table=True):
    image_id: Optional[int] = Field(default=None, primary_key=True)
    image: bytes
    image_metadata: List[Dict[str, str]] = Field(sa_column=Column(ListType))


def get_db():
    with Session(engine) as session:
        yield session


def get_device_by_id(db: Session, device_id: str):
    device = db.exec(select(Device).where(Device.device_id == device_id)).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


def authenticate_user(db: Session, credentials: HTTPBasicCredentials):
    device = get_device_by_id(db, credentials.username)
    if device.api_key != credentials.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@app.post("/devices", response_model=Device)
def register_device(device: Device, db: Session = Depends(get_db)):
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@app.get("/devices", response_model=List[Device])
def list_devices(db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(db, credentials)
    devices = db.exec(select(Device)).all()
    return devices


@app.get("/images", response_model=List[Image])
def list_images(db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(db, credentials)
    images = db.exec(select(Image)).all()
    return images


@app.get("/images/{id}", response_model=Image)
def get_image(image_id: int, db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(db, credentials)
    image = db.exec(select(Image).where(Image.image_id == image_id)).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return image
