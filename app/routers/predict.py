#app/router/predict.py

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Path
from fastapi.responses import FileResponse
from app.schemas import PredictionResponse
from app.dependencies import get_model
from utils.people_count import count_people_in_image
from utils.people_count import visualize_people_count
from app.services.predict_service import PredictService
import os

router = APIRouter()
service = PredictService()

@router.post(
    "/",
    response_model=PredictionResponse,
    summary="Upload an image and detect people",
    description="""
    Uploads an image file (JPEG or PNG) to detect the number of people and their bounding boxes.
    A visualization image with detections is generated and can be retrieved via the provided URL.
    """,
    response_description="Successful response with detection results and image URL.",
    status_code=200,
    responses={
        200: {
            "description": "Successful detection and image generation.",
            "content": {
                "application/json": {
                    "example": {
                        "num_people": 2,
                        "people": [
                            {"bbox": [50.0, 50.0, 150.0, 250.0], "confidence": 0.9, "index": 0},
                            {"bbox": [200.0, 100.0, 300.0, 300.0], "confidence": 0.8, "index": 1}
                        ],
                        "msg": "Person(s) Detected: Caution",
                        "image_url": "/predict/view-image/example-uuid.jpg"
                    }
                }
            }
        },
        400: {"description": "Invalid file format or bad request."},
        500: {"description": "Internal server error during processing."}
    }
)
async def predict_image(
    file: UploadFile = File(..., description="Image file (JPEG or PNG) to process.")
):
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

@router.get(
    "/view-image/{image_name}",
    summary="Retrieve a visualized image by name",
    description="""
    Retrieves a previously generated visualization image by its filename.
    The image is automatically deleted from the server after the first successful retrieval
    to save disk space. Subsequent requests for the same image will result in a 404 Not Found.
    """,
    response_class=FileResponse,
    status_code=200,
    responses={
        200: {
            "description": "Image successfully retrieved.",
            "content": {"image/jpeg": {"example": "Binary JPEG image data"}}
        },
        404: {"description": "Image not found or already deleted."},
        500: {"description": "Server error during image retrieval or deletion."}
    }
)
async def view_and_delete_image(
    image_name: str = Path(..., description="The filename (UUID) of the image to retrieve. e.g., `a055e6c2ec704864af2d27c662a134b9.jpg`"),
    background_tasks: BackgroundTasks = BackgroundTasks() # 기존 그대로
):
    image_path = os.path.join("temp", image_name)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    background_tasks.add_task(os.remove, image_path)
    return FileResponse(image_path, media_type="image/jpeg")
