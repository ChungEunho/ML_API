# app.schemas.py
from pydantic import BaseModel
from typing import List

class Detection(BaseModel):
    bbox: List[float]
    confidence: float
    index: int
    
class PredictionResponse(BaseModel):
    num_people: int
    people: List [Detection]
    msg: str
    image_url: str