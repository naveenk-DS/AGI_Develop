# ─────────────────────────────────────────────────────────────────
#  NAVIX AGI  —  Docker Image
#  Base: Python 3.12 + CUDA 12.1 (matches torch==2.5.1+cu121)
# ─────────────────────────────────────────────────────────────────
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# ── System packages ───────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive

# Step 1: Add deadsnakes PPA to get Python 3.12 on Ubuntu 22.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update

# Step 2: Install Python 3.12 + system dependencies
RUN apt-get install -y --no-install-recommends \
    python3.12 python3.12-dev python3.12-venv \
    python3-distutils python3-setuptools \
    gcc g++ build-essential make \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    libasound2-dev \
    libglib2.0-0 libnspr4 libnss3 libxss1 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxi6 libxtst6 libcups2 libdrm2 libgbm1 libxrandr2 \
    wget curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Make python3.12 the default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 \
 && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# ── Bootstrap pip for python3.12 and install uv ──────────────────────
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 \
    && python3.12 -m pip install --no-cache-dir uv

# ── Working directory ─────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies first (layer cache friendly) ──────
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ── Install Playwright browsers ───────────────────────────────────
RUN uv run playwright install chromium --with-deps

# ── Copy application code ─────────────────────────────────────────
COPY app/       ./app/
COPY core/      ./core/
COPY config/    ./config/
COPY tools/     ./tools/
COPY workflows/ ./workflows/
COPY watch/     ./watch/
COPY data/      ./data/
COPY navix_start.py ./
COPY navix_tray.py  ./

# ── Environment ───────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# ── Ports ─────────────────────────────────────────────────────────
# FastAPI / Uvicorn
EXPOSE 8000
# Qdrant (if running inside container)
EXPOSE 6333

# ── Default start command ─────────────────────────────────────────
CMD ["uv", "run", "python", "navix_start.py"]
