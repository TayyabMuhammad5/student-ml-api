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

---

## Part 22 — CI/CD Workflow Separation

### Workflow Overview

| Workflow | Trigger | Responsibilities | Publishes? |
|----------|---------|------------------|------------|
| **CI** (`ci.yml`) | Pull Request to `main` | Test → Validate → Build-check | ❌ No |
| **Release** (`release.yml`) | Version tag push (`v*.*.*`) | Test → Build → Version → Publish | ✅ Yes |

### Why Publishing Docker Images from Every Pull Request Is Undesirable

Publishing Docker images directly from every Pull Request is problematic for several reasons:

1. **Unreviewed Code Becomes a Published Artifact**: PR code has not yet been reviewed or approved. Publishing it to a registry means untrusted, potentially broken or malicious code exists as a deployable artifact that someone could accidentally pull and run in production.

2. **Tag Collisions and `:latest` Overwrites**: If multiple PRs are open simultaneously and all publish to `:latest`, they race to overwrite each other. The `:latest` tag becomes unpredictable — it no longer represents the most recent *approved* state of the codebase.

3. **Wasted Registry Storage**: Most PRs are iterative — multiple pushes happen before a final merge. Publishing on every push creates dozens of throwaway images that waste storage and clutter the registry. These images are never intended for production use.

4. **No Semantic Version**: PR images lack a meaningful version tag. They cannot be referenced reliably for rollback, auditing, or deployment. A tag like `pr-47-attempt-3` has no traceability value compared to `1.1.0`.

5. **Security Risk**: In open-source projects, external contributors can open PRs. If the CI pipeline publishes images from fork PRs, an attacker could inject malicious code into a published image without maintainer approval.

6. **Environment Contamination**: If staging environments are configured to pull `:latest`, a PR publish could deploy unfinished features to staging, breaking other team members' testing workflows.

**The correct pattern** is what we implement: the CI workflow validates that the code is correct and the Docker image *can* build, but only the Release workflow (triggered by a deliberate version tag) actually publishes to the registry.

---

## Part 23 — Image Metadata (OCI Labels)

### Implementation

The Dockerfile uses `ARG` and `LABEL` instructions to embed OCI-standard metadata at build time:

```dockerfile
ARG APP_VERSION=unknown
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown
ARG REPOSITORY=unknown

LABEL org.opencontainers.image.title="student-ml-api" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.source="${REPOSITORY}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.description="ML Inference Service"
```

The Release workflow passes the actual values via `--build-arg`:

```bash
docker build \
  --build-arg APP_VERSION=1.1.0 \
  --build-arg GIT_COMMIT=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg REPOSITORY=https://github.com/TayyabMuhammad5/student-ml-api \
  -t student-ml-api:1.1.0 .
```

### Verification via `docker inspect`

```bash
$ docker inspect student-ml-api:1.1.0 --format "{{json .Config.Labels}}"
```

**Output:**

```json
{
    "org.opencontainers.image.created": "2026-09-06T09:14:57Z",
    "org.opencontainers.image.description": "ML Inference Service",
    "org.opencontainers.image.revision": "7cefa17f384260bf7b98e6d3a8b4b6d45ff21d50",
    "org.opencontainers.image.source": "https://github.com/TayyabMuhammad5/student-ml-api",
    "org.opencontainers.image.title": "student-ml-api",
    "org.opencontainers.image.version": "1.1.0"
}
```

This proves the image is traceable: given any running container, we can identify the exact version, commit, source repository, and build timestamp.

---

## Part 24 — Commit SHA Tag

### Implementation

The Release workflow tags each image with **three tags**:

```bash
docker build \
  -t ghcr.io/tayyabmuhammad5/student-ml-api:1.1.0 \
  -t ghcr.io/tayyabmuhammad5/student-ml-api:latest \
  -t ghcr.io/tayyabmuhammad5/student-ml-api:7cefa17 \
  .
```

| Tag | Purpose |
|-----|---------|
| `1.1.0` | Semantic version — human-readable release identifier |
| `latest` | Convenience — always points to the most recent release |
| `7cefa17` | Commit SHA — exact source code traceability |

### Why Commit-Specific Tags Are Beneficial

1. **Immutability**: Semantic version tags like `1.1.0` and especially `latest` can be re-tagged to point to different images. A commit SHA is inherently unique — it will always reference the exact same source code. This makes it the most reliable identifier for an image.

2. **Exact Traceability**: Given a running container tagged `7cefa17`, you can immediately trace it back to the source: `git show 7cefa17`. No ambiguity, no lookup tables — the tag *is* the pointer to the code.

3. **Simplified Debugging**: When production breaks, the commit SHA tag tells you exactly which code is running. You can `git diff 7cefa17 HEAD` to see what changed, or `git log 7cefa17..HEAD` to see the full history.

4. **Safe Rollback**: Rolling back to a known-good state is as simple as `docker pull ghcr.io/.../student-ml-api:abc1234`. No need to remember which semver corresponds to which state — every commit is directly addressable.

5. **Parallel Deployments**: In staging or canary environments, multiple versions may run simultaneously. Commit SHA tags allow unambiguous identification of each deployment without tag collisions.

6. **Audit Trail**: For compliance and security audits, commit SHA tags provide cryptographic-level traceability from a deployed artifact back to the exact source code, build pipeline run, and author.

---

## Part 25 — Docker Build Cache Analysis

### Dockerfile Layer Strategy

```dockerfile
# Layer 1: Base image
FROM python:3.11-slim

# Layer 2: Copy ONLY requirements.txt
COPY requirements.txt .

# Layer 3: Install dependencies (expensive — ~30s)
RUN pip install --no-cache-dir -r requirements.txt

# Layer 4: Copy application code
COPY app.py .
COPY VERSION .
```

### Experiment 1: Modify Only `app.py`

After the initial build, I modified `app.py` (added a comment) and rebuilt:

```
#5 [1/6] FROM docker.io/library/python:3.11-slim@sha256:...        0.2s
#6 [2/6] WORKDIR /app
#6 CACHED
#7 [3/6] COPY requirements.txt .
#7 CACHED
#8 [4/6] RUN pip install --no-cache-dir -r requirements.txt
#8 CACHED
#9 [5/6] COPY app.py .
#9 DONE 0.2s
#10 [6/6] COPY VERSION .
#10 DONE 0.1s
```

**Result**: Layers 1–4 (base image, WORKDIR, COPY requirements.txt, pip install) were all **CACHED**. Only layers 5–6 (copying app.py and VERSION) re-executed. The expensive `pip install` step (~30 seconds) was completely skipped. **Total rebuild time: ~1 second.**

### Experiment 2: Modify `requirements.txt`

After modifying `requirements.txt` (added `requests==2.31.0`) and rebuilt:

```
#5 [1/6] FROM docker.io/library/python:3.11-slim@sha256:...        0.2s
#6 [2/6] WORKDIR /app
#6 CACHED
#7 [3/6] COPY requirements.txt .
#7 DONE 0.1s
#8 [4/6] RUN pip install --no-cache-dir -r requirements.txt
#8 DONE 27.0s
#9 [5/6] COPY app.py .
#9 DONE 0.1s
#10 [6/6] COPY VERSION .
#10 DONE 0.0s
```

**Result**: Only layers 1–2 were cached. Layer 3 (COPY requirements.txt) was invalidated because the file changed, which cascaded to invalidate layer 4 (pip install — re-ran in 27s) and all subsequent layers. **Total rebuild time: ~30 seconds.**

### Comparison

| Scenario | Layers Cached | Layers Rebuilt | Build Time |
|----------|--------------|----------------|------------|
| Change `app.py` only | 1, 2, 3, 4 (incl. pip install) | 5, 6 | ~1s |
| Change `requirements.txt` | 1, 2 | 3, 4 (pip install 27s), 5, 6 | ~30s |

### Why Separated `COPY` Is Preferable to `COPY . .`

The naive approach:

```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

With `COPY . .`, Docker hashes the **entire build context** to determine if the layer is cached. This means **any file change** — editing `app.py`, updating `README.md`, even modifying `.gitignore` — invalidates the `COPY . .` layer. Since Docker cache invalidation cascades forward, the `pip install` layer is **also invalidated and re-run from scratch**.

The optimized approach:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
```

Here, the `pip install` layer only depends on `requirements.txt`. Since dependencies change far less frequently than application code, this layer stays cached for the vast majority of builds. During typical development (editing `app.py`), only the final `COPY` layer re-executes — saving 30+ seconds per build.

**In a CI/CD pipeline running hundreds of builds per day, this optimization saves hours of cumulative build time.**

---

## Part 26 — Failure Analysis

### Failure 1: Failed pytest

**Symptom:**
```
$ pytest tests/ -v --tb=short
FAILED tests/test_app.py::test_health_endpoint - AssertionError: assert 'unhealthy' == 'healthy'
=========================== 1 failed, 4 passed in 0.42s ===========================
```
The CI pipeline exits with a non-zero exit code, and the GitHub Actions job shows a red ❌.

**Root Cause:**
The `/health` endpoint was deliberately modified to return `"status": "unhealthy"` instead of `"status": "healthy"`. The test assertion `assert data["status"] == "healthy"` no longer matches the actual response.

**Evidence:**
```python
# Modified app.py (line 38)
"status": "unhealthy",  # <-- Changed from "healthy"
```
```
tests/test_app.py::test_health_endpoint FAILED
>       assert data["status"] == "healthy"
E       AssertionError: assert 'unhealthy' == 'healthy'
```

**Correction:**
Reverted the health endpoint to return `"status": "healthy"`. After fixing, all 5 tests pass:
```
=========================== 5 passed in 0.38s ===========================
```

---

### Failure 2: Application Bound to 127.0.0.1

**Symptom:**
```
$ docker run -d --name test-api -p 5000:5000 student-ml-api:test
$ curl http://localhost:5000/health
curl: (56) Recv failure: Connection reset by peer
```
The container starts successfully (`docker ps` shows it running), but HTTP requests from the host machine are refused.

**Root Cause:**
The Dockerfile CMD was changed to bind to `127.0.0.1` instead of `0.0.0.0`:
```dockerfile
CMD ["uvicorn", "app:app", "--host", "127.0.0.1", "--port", "5000"]
```
Inside a Docker container, `127.0.0.1` refers to the container's own loopback interface, not the host. The port mapping (`-p 5000:5000`) forwards traffic to the container's network interface (`eth0`), but the application is only listening on `lo`. Traffic arrives at the container but no process is listening on that interface.

**Evidence:**
```
$ docker logs test-api
INFO:     Uvicorn running on http://127.0.0.1:5000 (Press CTRL+C to quit)

$ docker exec test-api curl http://127.0.0.1:5000/health
{"status":"healthy",...}   # Works INSIDE the container

$ curl http://localhost:5000/health
curl: (56) Recv failure: Connection reset by peer  # Fails from HOST
```

**Correction:**
Changed the bind address back to `0.0.0.0`:
```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```
`0.0.0.0` binds to all network interfaces inside the container, allowing port-forwarded traffic from the host to reach the application.

---

### Failure 3: Wrong Container Port

**Symptom:**
```
$ docker run -d --name test-api -p 5000:3000 student-ml-api:test
$ curl http://localhost:5000/health
curl: (52) Empty reply from server
```
The container is running but the endpoint returns empty responses or connection errors.

**Root Cause:**
The port mapping `-p 5000:3000` forwards host port 5000 to **container port 3000**, but the application listens on **container port 5000**. No process is listening on port 3000 inside the container.

**Evidence:**
```
$ docker port test-api
5000/tcp -> 0.0.0.0:5000    # Host 5000 → Container 3000 (WRONG)

$ docker logs test-api
INFO:     Uvicorn running on http://0.0.0.0:5000  # App on port 5000, not 3000
```

**Correction:**
Fixed the port mapping to match the application's listening port:
```bash
docker run -d --name test-api -p 5000:5000 student-ml-api:test
```

---

### Failure 4: Missing Dependency

**Symptom:**
```
$ docker build -t student-ml-api:test .
...
=> [3/4] RUN pip install --no-cache-dir -r requirements.txt
...
$ docker run -d --name test-api -p 5000:5000 student-ml-api:test
$ docker logs test-api
Traceback (most recent call last):
  File "/app/app.py", line 1, in <module>
    from fastapi import FastAPI, HTTPException
ModuleNotFoundError: No module named 'fastapi'
```
The container exits immediately after starting.

**Root Cause:**
`fastapi` was removed from `requirements.txt`. The `pip install` step completed successfully (it just installed fewer packages), but at runtime the Python import fails because FastAPI is not installed in the container.

**Evidence:**
```
# Modified requirements.txt — removed fastapi
uvicorn==0.30.6
pydantic==2.9.2
httpx==0.27.2
pytest==8.3.3

$ docker ps -a
CONTAINER ID   IMAGE               STATUS                     
abc123         student-ml-api:test  Exited (1) 2 seconds ago   # Crashed
```

**Correction:**
Restored `fastapi==0.115.0` to `requirements.txt` and rebuilt:
```
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
httpx==0.27.2
pytest==8.3.3
```
