# app/main.py

from fastapi import FastAPI, Request
from app.routers import predict
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("Request/Respond")

app = FastAPI(
    title = "Human Counting API",
    description= "YOLOv8 기반 사람 수 카운팅 API",
    version = "1.0.0"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    #요청 정보 기록
    logger.info(f"Request: {request.method} {request.url}")
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    #응답 정보 기록
    logger.info(f"Response status: {response.status_code} ({process_time:.2f}ms)")
    
    return response

app.include_router(predict.router, prefix = "/predict", tags=["Prediction"])
