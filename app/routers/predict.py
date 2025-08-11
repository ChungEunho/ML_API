#app/router/predict.py

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.schemas import PredictionResponse
from app.dependencies import get_model
from utils.people_count import count_people_in_image
from utils.people_count import visualize_people_count
from app.services.predict_service import PredictService
import os

router = APIRouter()
service = PredictService()

@router.post("/", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)):
    model = get_model()
    try:
        result = await service.predict(
            model=model,
            file=file,
            count_people_fn=count_people_in_image,
            visualize_fn=visualize_people_count,
        )
        image_url = f"/predict/view-image/{result['output_image_name']}"
        return {
            "num_people": result["num_people"],
            "people": result["people"],
            "msg": result["msg"],
            "image_url": image_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/view-image/{image_name}")
async def view_and_delete_image(image_name: str, background_tasks: BackgroundTasks):
    image_path = os.path.join("temp", image_name)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    background_tasks.add_task(os.remove, image_path)
    return FileResponse(image_path, media_type="image/jpeg")
