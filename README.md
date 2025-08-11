## MLAPI — Human Counting API (YOLOv8)

A FastAPI service that detects people in an image using YOLOv8 and returns:
- number of detected people
- per-detection metadata (bbox, confidence, index)
- a URL to retrieve a visualization image (bounding boxes + count)

### Features
- People detection on uploaded images (multipart/form-data)
- Result visualization with bounding boxes and total count overlay
- Simple, production-ready FastAPI app structure
- OpenAPI/Swagger UI available out of the box

### API Endpoints
- POST ` /predict/ `
  - Body: `file` as multipart image
  - Response (JSON):
    ```json
    {
      "num_people": 3,
      "people": [
        {"bbox": [x1, y1, x2, y2], "confidence": 0.95, "index": 0}
      ],
      "msg": "Person(s) Detected: Caution",
      "image_url": "/predict/view-image/<uuid>.jpg"
    }
    ```
- GET ` /predict/view-image/{image_name} `
  - Returns the JPEG visualization image.
  - The file is scheduled for deletion after the first successful GET (a second GET should return 404).

### Quickstart (Local)
1) Install runtime dependencies
```bash
pip install -r requirements.txt
```
2) Start the server
```bash
uvicorn app.main:app --reload
```
3) Open API docs
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Testing
- Install dev dependencies (includes pytest, httpx):
```bash
pip install -r requirements-dev.txt
```
- Run tests:
```bash
python -m pytest -q
```

### cURL Test Script
A helper script is provided to exercise the API end-to-end once the server is running.

- Path: `scripts/curl_test.sh`
- Usage:
```bash
chmod +x scripts/curl_test.sh
scripts/curl_test.sh  # uses test_input/bus.jpg by default
```
- Options:
```bash
SERVER_URL=http://localhost:8000 scripts/curl_test.sh /absolute/path/to/your.jpg
```
- Behavior:
  - POSTs an image to `/predict/`, saves JSON to `/tmp/predict.json`
  - Extracts `image_url`, downloads result image to `/tmp/result.jpg`
  - Performs a second GET to confirm the image was deleted (expects 404)

### Docker
Build and run the service in a container:
```bash
docker build -t mlapi:latest .
docker run --rm -p 8000:8000 mlapi:latest
```
Then open [http://localhost:8000/docs](http://localhost:8000/docs).

#### Recommended run options (performance/robustness)
Uvicorn flags can be appended at runtime (ENTRYPOINT is fixed to `uvicorn app.main:app ...`). Start conservative due to YOLO memory usage:

```bash
# Single worker (recommended default)
docker run --name mlapi_dev_singleworker -p 8000:8000 \
  -e YOLO_CONFIG_DIR=/tmp \
  mlapi:latest \
  --workers 1 \
  --timeout-keep-alive 10 \
  --limit-concurrency 100
```

Behind a reverse proxy (Nginx/ALB):
```bash
docker run --name mlapi_dev_reverseproxy -p 8000:8000 \
  -e YOLO_CONFIG_DIR=/tmp \
  mlapi:latest \
  --proxy-headers --forwarded-allow-ips="*" \
  --workers 1 --timeout-keep-alive 10 --limit-concurrency 100
```

If you need more throughput and have sufficient memory, try 2 workers (each worker loads the YOLO model):
```bash
docker run --name mlapi_dev_2workers -p 8000:8000 \
  -e YOLO_CONFIG_DIR=/tmp \
  mlapi:latest \
  --workers 2 \
  --timeout-keep-alive 10 \
  --limit-concurrency 80 \
  --proxy-headers --forwarded-allow-ips="*"
```

#### Quick validation
```bash
# Docs UI
open http://localhost:8000/docs  # macOS; or use your browser

# Prediction request
curl -F 'file=@test_input/bus.jpg' http://localhost:8000/predict/
```

#### Cleanup
```bash
# Stop and remove the container
docker rm -f mlapi_dev

# Remove the image (optional)
docker rmi -f mlapi:latest
```

### Project Layout
```
MLAPI_dev/
├── app/
│   ├── main.py              # FastAPI application and middleware
│   └── routers/
│       └── predict.py       # /predict endpoints
├── model/
│   ├── load_model.py        # YOLO model loader
│   └── inference.py         # Inference wrapper
├── utils/
│   └── people_count.py      # Postprocess + visualization
├── scripts/
│   └── curl_test.sh         # cURL-based API test script
├── tests/
│   └── test_api.py          # Pytest-based API tests (with mocks)
├── test_input/bus.jpg       # Sample image
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Dev/test dependencies
├── Dockerfile
└── yolov8n.pt               # YOLOv8n weights
```

### Notes & Troubleshooting
- The visualization image served by `GET /predict/view-image/{image_name}` is deleted after the first successful GET; a second GET returns 404 by design.
- If you see `DeprecationWarning` from `httpx` in tests, it does not affect behavior. You can suppress it with a `pytest.ini` filter if desired.
- For reproducible environments, consider using `conda` or `venv`, and ensure your IDE uses the same interpreter as your terminal.