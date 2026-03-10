# CGS Runtime Wrapper — FastAPI service
# Base: Python 3.11 slim; runs as non-root user

FROM python:3.11-slim

# ── system deps ──────────────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ── non-root user ────────────────────────────────────────────────────────────
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# ── install Python dependencies ──────────────────────────────────────────────
# Copy only the dependency manifests first so Docker layer cache is reused
# when only application code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── copy application code ────────────────────────────────────────────────────
COPY pyproject.toml ./
COPY cgs_runtime_wrapper/ ./cgs_runtime_wrapper/

# Install package in editable mode so imports resolve correctly
RUN pip install --no-cache-dir -e .

# ── ownership ────────────────────────────────────────────────────────────────
RUN chown -R appuser:appgroup /app

USER appuser

# ── runtime ──────────────────────────────────────────────────────────────────
EXPOSE 8000

# Healthcheck — lightweight probe on the FastAPI /docs redirect
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf -H "X-API-Key: ${CGS_API_KEY}" http://localhost:8000/turn || exit 1

CMD ["uvicorn", "cgs_runtime_wrapper.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
