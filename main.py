"""
This module contains the main FastAPI application for the Fantasy Forge API.

It includes endpoints for creating and retrieving users, creating devices for users,
retrieving a list of devices, and retrieving images.

The module also defines database models, schemas, and CRUD operations for interacting with the database.
"""
import os
import logging
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
IMAGE_PATH = 'images'


def get_db():
    """
    Get a database session.

    Returns:
        Session: The database session.
    """
    logger.info('Getting database session')
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.

    Args:
        user (schemas.UserCreate): The user data.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        schemas.User: The created user.
    """
    logger.info('Creating a new user')
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning('Email already registered')
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user_name = crud.get_user_by_name(db, name=user.name)
    if db_user_name:
        logger.warning('Name already registered')
        raise HTTPException(status_code=400, detail="Name already registered")
    created_user = crud.create_user(db=db, user=user)
    logger.info('User created successfully')
    return created_user


@app.get("/users/", response_model=list[schemas.User])
def get_users(credentials: Annotated[HTTPBasicCredentials, Depends(security)], skip: int = 0, limit: int = 100,
              db: Session = Depends(get_db)):
    """
    Read a list of users

    Args:
        credentials (Annotated[HTTPBasicCredentials, Depends(security)]): The HTTP basic credentials.
        skip (int, optional): Number of users to skip. Defaults to 0.
        limit (int, optional): Maximum number of users to retrieve. Defaults to 100.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        list[schemas.User]: The list of users.
    """
    if not crud.validate_user(db, credentials.username, credentials.password, role='admin'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)], user_id: int,
              db: Session = Depends(get_db)):
    """
    Read a user by ID.

    Args:
        credentials (Annotated[HTTPBasicCredentials, Depends(security)]): The HTTP basic credentials.
        user_id (int): The ID of the user to retrieve.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        schemas.User: The user.
    """
    logger.info('Reading user by ID')
    db_user_id = crud.get_user(db, user_id=user_id)
    db_user_name = crud.get_user_by_name(db, name=credentials.username)

    if crud.validate_user(db, credentials.username, credentials.password, role='admin'):
        if db_user_id is None:
            logger.warning('User not found')
            raise HTTPException(status_code=404, detail="User not found")
        logger.info('User retrieved successfully')
        return db_user_id
    elif crud.validate_user(db, credentials.username, credentials.password, role='user'):
        if db_user_id is None or db_user_name is None:
            logger.warning('Unauthorized')
            raise HTTPException(status_code=401, detail="Unauthorized")
        elif db_user_name.id == db_user_id.id:
            logger.info('User retrieved successfully')
            return db_user_id
        else:
            logger.warning('Unauthorized')
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        logger.warning('Unauthorized')
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/users/{user_id}/devices", response_model=schemas.User)
def create_device_for_user(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)], user_id: int,
        device: schemas.DeviceCreate, db: Session = Depends(get_db)
):
    """
    Create a device for a user.

    Args:
        credentials (Annotated[HTTPBasicCredentials, Depends(security)]): The HTTP basic credentials.
        user_id (int): The ID of the user.
        device (schemas.DeviceCreate): The device data.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        schemas.Device: The created device.
    """
    logger.info('Creating device for user')
    db_user_id = crud.get_user(db, user_id=user_id)
    db_user_name = crud.get_user_by_name(db, name=credentials.username)

    if crud.validate_user(db, credentials.username, credentials.password, role='admin'):
        logger.info('Device created successfully')
        return crud.create_user_device(db=db, device=device, user_id=user_id)
    elif crud.validate_user(db, credentials.username, credentials.password, role='user'):
        if db_user_id is None or db_user_name is None:
            logger.warning('Unauthorized')
            raise HTTPException(status_code=401, detail="Unauthorized")
        elif db_user_name.id == db_user_id.id:
            logger.info('Device created successfully')
            return crud.create_user_device(db=db, device=device, user_id=user_id)
        else:
            logger.warning('Unauthorized')
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        logger.warning('Unauthorized')
        raise HTTPException(status_code=401, detail="Unauthorized")
    
 
@app.get("/devices/", response_model=list[schemas.Device])
def read_devices(credentials: Annotated[HTTPBasicCredentials, Depends(security)],
                 skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Read a list of devices.

    Args:
        credentials (Annotated[HTTPBasicCredentials, Depends(security)]): The HTTP basic credentials.
        skip (int, optional): Number of devices to skip. Defaults to 0.
        limit (int, optional): Maximum number of devices to retrieve. Defaults to 100.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        list[schemas.Device]: The list of devices.
    """
    logger.info('Reading list of devices')
    if crud.validate_user(db, credentials.username, credentials.password, role='admin'):
        items = crud.get_devices(db, skip=skip, limit=limit)
        logger.info('Devices read successfully')
        return items
    logger.warning('Unauthorized')
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/image/{image_filename}")
def get_image(image_filename: str, credentials: Annotated[HTTPBasicCredentials, Depends(security)],
              db: Session = Depends(get_db)):
    """
    Get an image by filename.

    Args:
        image_filename (str): The filename of the image.
        credentials (Annotated[HTTPBasicCredentials, Depends(security)]): The HTTP basic credentials.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        FileResponse: The image file response.
    """
    logger.info('Fetching image: %s', image_filename)
    if not crud.validate_user(db, credentials.username, credentials.password, role='user'):
        logger.warning('Unauthorized')
        raise HTTPException(status_code=401, detail="Unauthorized")

    sanitized_filename = sanitize_filename(image_filename)
    full_path_filename = os.path.join(IMAGE_PATH, sanitized_filename)
    logger.debug('Full path of image: %s', full_path_filename)
    if os.path.isfile(full_path_filename):
        logger.info('Image found: %s', sanitized_filename)
        return FileResponse(path=full_path_filename, filename=sanitized_filename, media_type='image/png')
    else:
        logger.warning('Image not found: %s', sanitized_filename)
        raise HTTPException(status_code=404, detail="Image not found")


def get_filelist(path: str):
    """
    Get a list of files in a directory.

    Args:
        path (str): The directory path.

    Returns:
        list[str]: The list of file names.
    """
    logger.info('Getting file list from path: %s', path)
    f = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        logger.debug('Current directory: %s', dirpath)
        logger.debug('Subdirectories: %s', dirnames)
        logger.debug('Files: %s', filenames)
        f.extend(filenames)
        break
    logger.info('File list retrieved: %s', f)
    return f


@app.get("/image/")
def get_images(credentials: Annotated[HTTPBasicCredentials, Depends(security)], db: Session = Depends(get_db)):
    """
    Get a list of images.

    Args:
        credentials (Annotated[HTTPBasicCredentials, Depends(security)]): The HTTP basic credentials.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        JSONResponse: The JSON response containing the list of images.
    """
    if not crud.validate_user(db, credentials.username, credentials.password, role='user'):
        logger.warning('Unauthorized')
        raise HTTPException(status_code=401, detail="Unauthorized")
    files = get_filelist(IMAGE_PATH)
    response_json = []
    for filename in files:
        file_json = {'filename': filename}
        response_json.append(file_json)
    logger.info('File list retrieved')
    return JSONResponse(content=response_json)
