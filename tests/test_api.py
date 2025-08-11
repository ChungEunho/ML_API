import os
import io
import uuid
import pytest

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def ensure_temp_dir(tmp_path, monkeypatch):
    os.makedirs("temp", exist_ok=True)
    yield
    # Cleanup any leftover files in temp after each test
    if os.path.isdir("temp"):
        for name in os.listdir("temp"):
            try:
                os.remove(os.path.join("temp", name))
            except FileNotFoundError:
                pass


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def mock_model(monkeypatch):
    class DummyModel:
        model = type("Inner", (), {"names": {0: "person"}})()

    def fake_get_model(*args, **kwargs):
        return DummyModel()

    # Patch the cached provider where used
    monkeypatch.setattr("app.routers.predict.get_model", fake_get_model, raising=True)
    return DummyModel()


@pytest.fixture()
def mock_inference_success(monkeypatch):
    # Two fake detections
    detections = [
        {"bbox": [10, 20, 100, 200], "confidence": 0.92, "index": 0},
        {"bbox": [30, 40, 120, 220], "confidence": 0.85, "index": 1},
    ]

    def fake_count_people_in_image(model, image_path, confidence_threshold=0.1):
        assert os.path.exists(image_path)
        return detections

    def fake_visualize_people_count(image_path, people_detections, output_path="temp/out.jpg"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xdb")  # minimal bytes; content doesn't matter
        return output_path

    # Patch where used inside the router
    monkeypatch.setattr("app.routers.predict.count_people_in_image", fake_count_people_in_image, raising=True)
    monkeypatch.setattr("app.routers.predict.visualize_people_count", fake_visualize_people_count, raising=True)
    return detections


def test_predict_success_returns_expected_schema(client, mock_model, mock_inference_success):
    test_image_path = os.path.join("test_input", "bus.jpg")
    assert os.path.exists(test_image_path), "Expected test image at test_input/bus.jpg"

    with open(test_image_path, "rb") as f:
        files = {"file": ("bus.jpg", f, "image/jpeg")}
        response = client.post("/predict/", files=files)

    assert response.status_code == 200
    data = response.json()

    assert set(data.keys()) == {"num_people", "people", "msg", "image_url"}
    assert data["num_people"] == len(mock_inference_success)
    assert isinstance(data["people"], list)
    assert all({"bbox", "confidence", "index"}.issubset(d) for d in data["people"])
    assert data["image_url"].startswith("/predict/view-image/")
    # Message should indicate caution when detections exist
    assert "Caution" in data["msg"]

    # Verify the image endpoint serves the file and deletes it afterwards
    img_resp = client.get(data["image_url"])
    assert img_resp.status_code == 200
    assert img_resp.headers.get("content-type") == "image/jpeg"

    # File should be deleted by BackgroundTasks after response is consumed
    image_name = data["image_url"].split("/")[-1]
    image_path = os.path.join("temp", image_name)
    assert not os.path.exists(image_path)


def test_predict_no_person_message_and_zero_count(client, mock_model, monkeypatch):
    def fake_count_people_in_image(model, image_path, confidence_threshold=0.1):
        return []

    def fake_visualize_people_count(image_path, people_detections, output_path="temp/out.jpg"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xdb")
        return output_path

    # Patch where used inside the router
    monkeypatch.setattr("app.routers.predict.count_people_in_image", fake_count_people_in_image, raising=True)
    monkeypatch.setattr("app.routers.predict.visualize_people_count", fake_visualize_people_count, raising=True)

    test_image_path = os.path.join("test_input", "bus.jpg")
    with open(test_image_path, "rb") as f:
        files = {"file": ("bus.jpg", f, "image/jpeg")}
        response = client.post("/predict/", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["num_people"] == 0
    assert data["people"] == []
    assert "safe" in data["msg"].lower()


def test_view_image_404_when_missing(client):
    missing_name = f"{uuid.uuid4().hex}.jpg"
    resp = client.get(f"/predict/view-image/{missing_name}")
    assert resp.status_code == 404
