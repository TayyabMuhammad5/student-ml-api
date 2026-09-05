import pytest
from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


def test_health_endpoint():
    """Test that /health returns correct status, application name, and version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "student-ml-api"
    assert "application_version" in data
    assert "model_version" in data
    assert data["model_version"] == "1.0"


def test_predict_valid_input():
    """Test that /predict returns correct prediction for valid numeric input."""
    response = client.post("/predict", json={"value": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["input"] == 10
    assert data["prediction"] == 20


def test_predict_missing_input():
    """Test that /predict returns 400 when 'value' field is missing."""
    response = client.post("/predict", json={})
    assert response.status_code == 400


def test_predict_invalid_input():
    """Test that /predict returns 422 when 'value' is not a number."""
    response = client.post("/predict", json={"value": "not_a_number"})
    assert response.status_code == 422


def test_predict_negative_input():
    """Test that /predict handles negative values correctly."""
    response = client.post("/predict", json={"value": -5})
    assert response.status_code == 200
    data = response.json()
    assert data["input"] == -5
    assert data["prediction"] == -10


def test_predict_zero_input():
    """Test that /predict handles zero correctly."""
    response = client.post("/predict", json={"value": 0})
    assert response.status_code == 200
    data = response.json()
    assert data["input"] == 0
    assert data["prediction"] == 0
