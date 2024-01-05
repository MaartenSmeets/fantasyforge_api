"""
This module contains functions for CRUD operations on the database.
"""
import bcrypt
from sqlalchemy.orm import Session

import models
import schemas


def get_user(db: Session, user_id: int):
    """
    Retrieve a user from the database by user_id.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        User: The user object if found, None otherwise.
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str, role: str = 'user'):
    """
    Retrieve a user from the database by email and role.

    Args:
        db (Session): The database session.
        email (str): The email of the user.
        role (str, optional): The role of the user. Defaults to 'user'.

    Returns:
        User: The user object if found, None otherwise.
    """
    return db.query(models.User).filter(models.User.email == email and models.User.role == role).first()


def get_user_by_name(db: Session, name: str, role: str = 'user'):
    """
    Retrieve a user from the database by their name and role.

    Args:
        db (Session): The database session.
        name (str): The name of the user.
        role (str, optional): The role of the user. Defaults to 'user'.

    Returns:
        User: The user object if found, otherwise None.
    """
    return db.query(models.User).filter(models.User.name == name and models.User.role == role).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of users from the database.

    Args:
        db (Session): The database session.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to retrieve. Defaults to 100.

    Returns:
        List[User]: A list of User objects.
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def get_hashed_password(plain_text_password):
    """
    Hashes a password using bcrypt.

    Args:
        plain_text_password (str): The plain text password to be hashed.

    Returns:
        bytes: The hashed password.

    """
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    """
    Check if the provided plain text password matches the hashed password.

    Args:
        plain_text_password (str): The plain text password to check.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password)


def validate_user(db: Session, username: str, password: str, role: str = 'user'):
    """
    Validates the user credentials by checking if the provided username and password match the stored values in the database.

    Args:
        db (Session): The database session.
        username (str): The username of the user.
        password (str): The password of the user.
        role (str, optional): The role of the user. Defaults to 'user'.

    Returns:
        bool: True if the user credentials are valid, False otherwise.
    """
    user = get_user_by_name(db, username, role)
    if not user:
        return False
    stored_password_hash = user.hashed_password
    return check_password(password, stored_password_hash)


def create_user(db: Session, user: schemas.UserCreate):
    """
    Create a new user in the database.

    Parameters:
    - db (Session): The database session.
    - user (UserCreate): The user data to be created.

    Returns:
    - User: The created user object.
    """
    hashed_password = get_hashed_password(user.password)
    db_user = models.User(email=user.email, name=user.name,
                          hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_devices(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of devices from the database.

    Args:
        db (Session): The database session.
        skip (int, optional): Number of devices to skip. Defaults to 0.
        limit (int, optional): Maximum number of devices to retrieve. Defaults to 100.

    Returns:
        List[Device]: A list of devices.
    """
    return db.query(models.Device).offset(skip).limit(limit).all()


def create_user_device(db: Session, device: schemas.DeviceCreate, user_id: int):
    """
    Create a new user device in the database.

    Args:
        db (Session): The database session.
        device (DeviceCreate): The device data to be created.
        user_id (int): The ID of the user who owns the device.

    Returns:
        Device: The created device object.
    """
    db_item = models.Device(**device.model_dump(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
