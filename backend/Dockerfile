# SmartLink API image. Built by GitHub Actions and pulled by K3s from GHCR.
# No secrets here: configuration arrives at runtime as environment variables.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Dependencies first: this layer is cached while only the code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Unprivileged user with a fixed UID, so Kubernetes can enforce runAsNonRoot.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin smartlink
USER 10001

EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
