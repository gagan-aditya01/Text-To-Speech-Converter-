# ============================================================
# VoiceCraft — Multi-Language TTS Converter
# Dockerfile — Production image
# ============================================================
# Usage:
#   docker build -t voicecraft .
#   docker run -p 8501:8501 --env-file .env voicecraft
# ============================================================

# ---- Stage 1: dependency builder -----
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: production runtime ----
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd -r voicecraft && useradd -r -g voicecraft -d /app voicecraft

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=voicecraft:voicecraft app/         ./app/
COPY --chown=voicecraft:voicecraft .streamlit/  ./.streamlit/

# Create output directory with correct ownership
RUN mkdir -p /app/output && chown voicecraft:voicecraft /app/output

# Switch to non-root
USER voicecraft

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" \
    || exit 1

ENTRYPOINT ["python", "-m", "streamlit", "run", "app/main.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0"]
