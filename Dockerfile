# ─────────────────────────────────────────────
#  Main AI Voice Backend  (FastAPI + Uvicorn)
# ─────────────────────────────────────────────

# Use Python 3.11 slim for a smaller base image
FROM python:3.11-slim

WORKDIR /app

# ── System dependencies needed by torch / transformers ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies FIRST (better layer caching) ──
COPY requirements.txt .

# Installs torch==2.8.0 (and all other deps) from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application source ──
COPY . .

# ── Expose FastAPI port ──
EXPOSE 8000

# ── Run with uvicorn ──
#    HOST must be 0.0.0.0 so Docker can route traffic in
CMD ["uvicorn", "hello:app", "--host", "0.0.0.0", "--port", "8000"]
