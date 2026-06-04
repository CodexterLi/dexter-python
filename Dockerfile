# UV source
FROM ghcr.io/astral-sh/uv:latest AS uv-source

# Build stage
FROM public.ecr.aws/docker/library/python:3.14-slim AS builder
WORKDIR /app

# Install uv from official image
COPY --from=uv-source /uv /uvx /usr/local/bin/

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and install project
COPY app/ app/
RUN uv pip install --system .

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
