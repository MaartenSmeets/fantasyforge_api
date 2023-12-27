import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UUID, Enum
from sqlalchemy.orm import relationship

from database import Base


class Role(Enum):
    user = 1
    admin = 2


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Role, default=Role.user)
    is_active = Column(Boolean, default=True)
    devices = relationship("Device", back_populates="owner")


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    apikey = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="devices")


class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    metadata_filename = Column(String)
