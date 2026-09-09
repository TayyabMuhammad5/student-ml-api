# student-ml-api

A lightweight ML inference service built with FastAPI, containerized with Docker, and deployed via GitHub Actions CI/CD pipelines.

## API Endpoints

### `GET /health`
Returns application status and version metadata.

```json
{
  "status": "healthy",
  "application": "student-ml-api",
  "application_version": "1.1.0",
  "model_version": "1.0"
}
```

### `POST /predict`
Accepts a numeric value and returns a prediction (value × 2).

**Request:**
```json
{ "value": 10 }
```

**Response:**
```json
{ "input": 10, "prediction": 20 }
```

## Running Locally

```bash
# Build the Docker image
docker build -t student-ml-api:1.1.0 .

# Run the container
docker run -d --name student-ml-api -p 5000:5000 student-ml-api:1.1.0

# Test the endpoints
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict -H "Content-Type: application/json" -d '{"value": 10}'
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Traceability

### v1.1.0

| Item           | Value                                                            |
|----------------|------------------------------------------------------------------|
| PR             | #2                                                               |
| Merge Commit   | `be61f70fcaff3dfcc5bccfd63a9c9381310683a4`                       |
| Git Tag        | `v1.1.0`                                                         |
| Docker Image   | `ghcr.io/tayyabmuhammad5/student-ml-api:1.1.0`                  |
| Image Digest   | `sha256:d0ae7550bb354bc123fb39474d413435c6d6cd583460d1772f07b388e9d9d59c` |
