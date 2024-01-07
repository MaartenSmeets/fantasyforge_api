"""
This module contains the schema definitions for the Fantasy Forge API.

The schemas define the structure and validation rules for the data models used in the API.
"""
from pydantic import BaseModel


class DeviceBase(BaseModel):
    """
    Base model for device schema.
    """
    description: str | None = None


class DeviceCreate(DeviceBase):
    """
    Represents a device creation request.

    This class inherits from the DeviceBase class and can be used to create a new device.
    """


class Device(DeviceBase):
    """
    Model for device schema.
    """
    id: int
    apikey: str
    owner_id: int

    class Config:
        """
        Configuration class for the schema.
        """
        orm_mode = True


class UserBase(BaseModel):
    """
    Base model for user schema.
    """
    email: str
    name: str
    role: str


class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str


class User(UserBase):
    """
    Model for user schema.
    """
    id: int
    is_active: bool
    devices: list[Device] = []
    hashed_password: bytes

    class Config:
        """
        Configuration class for the schema.
        """
        orm_mode = True
