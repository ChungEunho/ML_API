# app/services/predict_service.py

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
import aiofiles
import os
import uuid


class PredictService:
    """
    사람 수 탐지 파이프라인을 담당하는 서비스 레이어.
    - 업로드 파일 저장
    - 감지 수행
    - 결과 시각화
    - 임시 입력 파일 정리
    """

    def __init__(self, temp_dir: str = "temp") -> None:
        self.temp_dir = temp_dir

    async def predict(
        self,
        model,
        file: UploadFile,
        count_people_fn,
        visualize_fn,
    ) -> dict:
        """
        모델과 업로드 파일을 받아 감지/시각화까지 수행하고 결과를 반환.

        반환 값 예시:
        {
            "num_people": int,
            "people": List[dict],
            "msg": str,
            "output_image_name": str,
        }
        """

        input_path = None
        try:
            file_ext = os.path.splitext(file.filename or "")[1] or ".jpg"
            input_name = f"temp_{uuid.uuid4().hex}{file_ext}"
            input_path = os.path.join(self.temp_dir, input_name)

            await self._save_upload(file, input_path)

            people_detections = await run_in_threadpool(count_people_fn, model, input_path)

            output_uuid = f"{uuid.uuid4().hex}.jpg"
            output_path = os.path.join(self.temp_dir, output_uuid)

            await run_in_threadpool(
                visualize_fn,
                image_path=input_path,
                people_detections=people_detections,
                output_path=output_path,
            )

            message = (
                "Person(s) Detected: Caution"
                if len(people_detections) > 0
                else "No Person(s) Detected, it is safe"
            )

            return {
                "num_people": len(people_detections),
                "people": people_detections,
                "msg": message,
                "output_image_name": output_uuid,
            }
        finally:
            if input_path and os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except Exception:
                    # 실패하더라도 무시
                    pass
    # 업로드된 파일을 비동기 방식으로 디스크에 저장함.
    async def _save_upload(self, file: UploadFile, file_path: str, chunk_size: int = 1 << 20) -> None:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        async with aiofiles.open(file_path, "wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                await out.write(chunk)

