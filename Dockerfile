# ── Brawl Stars v26.184 Server — Railway Dockerfile ──────────────────────
FROM python:3.11-slim

# Metadata
LABEL maintainer="brawl-server"
LABEL description="Brawl Stars v26.184 local server emulator"

# Don't buffer stdout/stderr — important for Railway log streaming
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Railway injects $PORT at runtime; the server reads it via os.environ.get("PORT", 9339)
# We don't EXPOSE a fixed port here — Railway's TCP proxy handles the mapping.

CMD ["python", "main.py"]
