from functools import lru_cache
from model.load_model import load_model

# lru_cache로 get_model()의 반환값을 1개 캐시 -> 첫 호출에만 실제 로드, 이후에는 같은 인스턴스 반환
# YOLO 모델 로드 비용 최소화
@lru_cache(maxsize=1)
def get_model():
    """Load the YOLO model once and cache it for reuse."""
    return load_model()