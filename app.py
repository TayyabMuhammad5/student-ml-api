from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import Optional

app = FastAPI(title="student-ml-api", description="ML Inference Service")


def get_version() -> str:
    """Read application version from VERSION file."""
    version_file = Path(__file__).parent / "VERSION"
    try:
        return version_file.read_text().strip()
    except FileNotFoundError:
        return "unknown"


class PredictRequest(BaseModel):
    value: Optional[float] = None


class PredictResponse(BaseModel):
    input: float
    prediction: float


class HealthResponse(BaseModel):
    status: str
    application: str
    application_version: str
    model_version: str


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint returning application status and version."""
    return {
        "status": "healthy",
        "application": "student-ml-api",
        "application_version": get_version(),
        "model_version": "1.0",
    }


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """Prediction endpoint that accepts a numeric value and returns a prediction."""
    if request.value is None:
        raise HTTPException(status_code=400, detail="Missing 'value' field")

    if not isinstance(request.value, (int, float)):
        raise HTTPException(status_code=400, detail="'value' must be a number")

    # Simple mathematical prediction: multiply by 2
    prediction = request.value * 2

    return {
        "input": request.value,
        "prediction": prediction,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
