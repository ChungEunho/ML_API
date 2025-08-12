# app.schemas.py
from typing import List
from pydantic import BaseModel, Field

class Detection(BaseModel):
    bbox: List[float] = Field(..., examples=[[10.0, 20.0, 100.0, 200.0]])
    confidence: float = Field(..., examples=[0.95])
    index: int = Field(..., examples=[0])
    
class PredictionResponse(BaseModel):
    num_people: int = Field(..., examples=[3])
    people: List[Detection] = Field(..., examples=[
        {"bbox": [48.55, 398.55, 245.34, 902.70], "confidence": 0.86, "index": 0},
        {"bbox": [669.47, 392.18, 809.72, 877.03], "confidence": 0.85, "index": 1}
    ])
    msg: str = Field(..., examples=["Person(s) Detected: Caution"])
    image_url: str = Field(..., examples=["/predict/view-image/a1b2c3d4e5f6.jpg"])