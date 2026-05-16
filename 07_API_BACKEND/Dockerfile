FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY 07_API_BACKEND/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["sh", "-c", "uvicorn app.main:app --app-dir 07_API_BACKEND --host 0.0.0.0 --port ${PORT:-8000}"]
