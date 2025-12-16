from pydantic import BaseModel


class DeviceBase(BaseModel):
    name: str
    type: str
    status: str


class Device(DeviceBase):
    id: str
    online: bool


class ReturnObject(BaseModel):
    device_id: str
    status: str
    message: str