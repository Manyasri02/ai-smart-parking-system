from pydantic import BaseModel

class ParkingLotCreate(BaseModel):
    name: str
    location: str
    total_slots: int

class ParkingLotUpdate(BaseModel):
    name: str
    location: str
    total_slots: int
