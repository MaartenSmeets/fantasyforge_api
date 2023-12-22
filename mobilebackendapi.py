import logging
from contextlib import asynccontextmanager
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.params import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import json
from sqlmodel import create_engine, Session, SQLModel, Field
from starlette import status
from starlette.responses import FileResponse

sqlite_file_name = "mobile_backgrounds.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    print("Startup event")
    try:
        create_db_and_tables()
        yield
    finally:
        print("Shutdown event")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str
    role: str


class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int


class ApiKey(SQLModel):
    api_key: str


class ImageMetadata(SQLModel):
    imgmetadata: dict


class Image(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    metadata_id: int
    file_path: str


class ImageWithMetadata(SQLModel):
    id: int
    imgmetadata: dict


app = FastAPI(lifespan=app_lifespan, description="Image Management API", version="0.1.0")
logger = logging.getLogger(__name__)
log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
uvicorn.run(app, log_config=log_config)
security = HTTPBasic()


def authenticate_user(session: Session, credentials: HTTPBasicCredentials):
    user = read_user_by_name(credentials.username, session=session)
    if credentials.password != user.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@app.post("/users", response_model=User)
def create_user(user: User, session: Session = Session(engine), credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Create user')
    authenticate_user(session, credentials)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users", response_model=List[User])
def read_users(session: Session = Session(engine), credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Read users')
    authenticate_user(session, credentials)
    users = session.query(User).all()
    return users


@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, session: Session = Session(engine), credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Read user')
    authenticate_user(session, credentials)
    user = (session.query(User).filter(User.id == user_id).first())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/name/{username}", response_model=User)
def read_user_by_name(username: str, session: Session = Session(engine),
                      credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Get user by name')
    authenticate_user(session, credentials)
    user = session.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: User, session: Session = Session(engine),
                credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Update user')
    authenticate_user(session, credentials)
    db_user = session.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.password = user.password
    db_user.role = user.role
    session.commit()
    session.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Session(engine),
                credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Delete user')
    authenticate_user(session, credentials)
    db_user = session.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(db_user)
    session.commit()


@app.post("/devices", response_model=ApiKey)
def register_device(device: Device, session: Session = Session(engine),
                    credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Register device')
    authenticate_user(session, credentials)
    session.add(device)
    session.commit()
    session.refresh(device)
    api_key = ApiKey(api_key=f"api_key_{device.id}")
    return api_key


@app.get("/images", response_model=List[ImageWithMetadata])
def read_images(session: Session = Session(engine), credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Read images')
    authenticate_user(session, credentials)
    images = session.query(Image).all()
    images_with_metadata = []
    for image in images:
        metadata = session.query(ImageMetadata).filter(ImageMetadata.id == image.metadata_id).first()
        metadata_dict = json.loads(metadata.imgmetadata)
        images_with_metadata.append(ImageWithMetadata(id=image.id, metadata=metadata_dict, file_path=image.file_path))
    return images_with_metadata


@app.get("/images/{image_id}")
def read_image(image_id: int, session: Session = Session(engine),
               credentials: HTTPBasicCredentials = Depends(security)):
    logger.info('Read image')
    authenticate_user(session, credentials)
    image = session.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    imgmetadata = session.query(ImageMetadata).filter(ImageMetadata.id == image.metadata_id).first()
    metadata_dict = json.loads(imgmetadata.imgmetadata)
    return FileResponse(image.file_path, media_type="image/png")

uvicorn.run(app, log_config=log_config)
