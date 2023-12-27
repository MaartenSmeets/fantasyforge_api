from pydantic import BaseModel


class DeviceBase(BaseModel):
    title: str
    description: str | None = None


class DeviceCreate(DeviceBase):
    pass


class Device(DeviceBase):
    id: int
    apikey: str
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    role: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    devices: list[Device] = []

    class Config:
        orm_mode = True
