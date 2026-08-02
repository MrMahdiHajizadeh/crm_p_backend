FROM python:3.12-bookworm

# Prevent Python from buffering stdout/stderr (useful for Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies for PostgreSQL
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb http://mirror.math.princeton.edu/pub/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://mirror.math.princeton.edu/pub/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    (apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=300 || true) && \
    apt-get install -y --no-install-recommends --fix-missing libpq-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv (fast Python package manager).
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb http://mirror.math.princeton.edu/pub/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://mirror.math.princeton.edu/pub/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    (apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=300 || true) && \
    apt-get install -y --no-install-recommends --fix-missing curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.11.28 sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    rm -rf /root/.local /var/lib/apt/lists/*

# Install Python dependencies into /opt/venv
COPY pyproject.toml uv.lock .python-version ./
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen --no-install-project

# Copy backend source
COPY . .

# Put the venv's binaries on PATH so `python`, `gunicorn`, `celery` etc. resolve.
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
