# ──────────────────────────────────────────────
# Stage 1: Production image
# ──────────────────────────────────────────────
FROM python:3.11-slim

# OCI metadata labels (passed as build args)
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

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching optimization)
# Copying requirements.txt separately ensures pip install layer is
# cached unless dependencies change, even if app code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY VERSION .

# Expose the application port
EXPOSE 5000

# Run with uvicorn in production mode, binding to 0.0.0.0
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
