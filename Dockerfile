# syntax=docker/dockerfile:1

# 1) 의존성 설치 전용 스테이지 (캐시 최적화)
FROM python:3.11-slim AS builder
WORKDIR /app

# 의존성만 먼저 복사 → 캐시 최대화
COPY requirements.txt ./

# 빌드용 파이썬 패키지 설치 (런타임 파일은 다음 스테이지로만 전달)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# 2) 런타임 스테이지 (작고 안전한 실행 환경)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# OpenCV 등 런타임에 필요한 시스템 라이브러리
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 빌더에서 설치된 파이썬 패키지 복사
COPY --from=builder /install /usr/local

# 애플리케이션 소스 복사
COPY . .

# 비루트 사용자로 실행 (권장)
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app \
    && chown -R app:app /app
USER app

EXPOSE 8000

# uvicorn을 고정 엔트리포인트로 설정하고, 추가 플래그는 CMD/런타임 인자로 전달
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD []


