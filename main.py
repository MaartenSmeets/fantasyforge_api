import logging
import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from pathvalidate import sanitize_filename

import crud
import models
import schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)
security = HTTPBasic()
app = FastAPI()
image_path = 'images'


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(credentials: Annotated[HTTPBasicCredentials, Depends(security)], skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db)):
    if not crud.validate_user(db, credentials.username, credentials.password, role='admin'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)], user_id: int,
              db: Session = Depends(get_db)):
    db_user_id = crud.get_user(db, user_id=user_id)
    db_user_name = crud.get_user_by_name(db, name=credentials.username)

    if crud.validate_user(db, credentials.username, credentials.password, role='admin'):
        if db_user_id is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user_id
    elif crud.validate_user(db, credentials.username, credentials.password, role='user'):
        if db_user_id is None or db_user_name is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        elif db_user_name.id == db_user_id.id:
            return db_user_id
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/users/{user_id}/devices/", response_model=schemas.Device)
def create_device_for_user(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)], user_id: int,
        device: schemas.DeviceCreate, db: Session = Depends(get_db)
):
    if not crud.validate_user(db, credentials.username, credentials.password, role='user'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.create_user_device(db=db, device=device, user_id=user_id)


@app.get("/devices/", response_model=list[schemas.Device])
def read_devices(credentials: Annotated[HTTPBasicCredentials, Depends(security)],
                 skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if crud.validate_user(db, credentials.username, credentials.password, role='admin'):
        items = crud.get_devices(db, skip=skip, limit=limit)
        return items
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/image/{image_filename}")
async def get_image(image_filename: str, credentials: Annotated[HTTPBasicCredentials, Depends(security)],
                    db: Session = Depends(get_db)):
    if not crud.validate_user(db, credentials.username, credentials.password, role='user'):
        raise HTTPException(status_code=401, detail="Unauthorized")

    sanitized_filename = sanitize_filename(image_filename)
    full_path_filename = os.path.join(image_path, sanitized_filename)
    logger.info('Fetching image: %s', full_path_filename)
    if os.path.isfile(full_path_filename):
        return FileResponse(path=full_path_filename, filename=sanitized_filename, media_type='image/png')
    else:
        return HTTPException(status_code=404, detail="Image not found")


def get_filelist(path: str):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        f.extend(filenames)
        break
    return f


@app.get("/image/")
async def get_images(credentials: Annotated[HTTPBasicCredentials, Depends(security)], db: Session = Depends(get_db)):
    if not crud.validate_user(db, credentials.username, credentials.password, role='user'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    files = get_filelist(image_path)
    response_json = []
    for filename in files:
        file_json = {'filename': filename}
        response_json.append(file_json)
    return JSONResponse(content=response_json)
