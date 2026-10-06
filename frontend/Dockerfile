# SmartLink dashboard image. Talks only to the API (API_URL); never to D1.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin smartlink
USER 10001

EXPOSE 8501
# The dashboard is served under /app so that the API can own "/" on the same
# hostname: short links stay short (http://host/abc123), the UI is http://host/app.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.baseUrlPath=app"]
