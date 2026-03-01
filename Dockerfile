# Dockerfile
# SynapDrive-AI — simulation-first, reproducible runtime container.

FROM python:3.12-slim

# Prevents Python from writing .pyc files and forces unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps kept minimal (numpy wheels work without build tools on slim for most platforms)
# If you ever hit a wheel build error, add: build-essential gcc
RUN python -m pip install --upgrade pip

# Copy dependency manifests first for layer caching
COPY requirements.txt /app/requirements.txt
COPY requirements-dev.txt /app/requirements-dev.txt
COPY pyproject.toml /app/pyproject.toml

# Install runtime deps (dev deps optional via build arg)
ARG INSTALL_DEV=false
RUN pip install -r requirements.txt && \
    if [ "$INSTALL_DEV" = "true" ]; then pip install -r requirements-dev.txt; fi

# Copy the rest of the repo
COPY . /app

# Default port used by the web dashboard
EXPOSE 5055

# Default command = show CLI help (safe default)
CMD ["python", "-m", "synapdrive_ai", "-h"]
