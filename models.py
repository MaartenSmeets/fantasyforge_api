"""
This module defines the database models for the Fantasy Forge API.

It contains the following models:
- User: Represents a user in the system.
- Device: Represents a device owned by a user.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        email (str): The email address of the user.
        name (str): The name of the user.
        hashed_password (str): The hashed password of the user.
        role (str): The role of the user.
        is_active (bool): Indicates whether the user is active or not.
        devices (List[Device]): The devices associated with the user.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default='user')
    is_active = Column(Boolean, default=True)
    devices = relationship("Device", back_populates="owner")


class Device(Base):
    """
    Represents a device owned by a user.

    Attributes:
        id (int): The unique identifier for the device.
        description (str): The description of the device.
        apikey (str): The API key of the device.
        owner_id (int): The ID of the owner user.
        owner (User): The owner user of the device.
    """
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    apikey = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="devices")
