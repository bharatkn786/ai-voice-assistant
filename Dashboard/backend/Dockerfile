# ─────────────────────────────────────────────
#  Dashboard API Backend  (FastAPI + Uvicorn)
# ─────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# ── Install only the packages this service needs ──
RUN pip install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn[standard]==0.34.0 \
    pymongo==4.10.1 \
    python-dotenv==1.0.1 \
    python-multipart==0.0.20 \
    pydantic==2.10.5

# ── Copy dashboard backend source ──
COPY . .

# ── Expose dashboard API port ──
EXPOSE 8001

# ── Run with uvicorn ──
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
