FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["uvicorn", "app.main:app", "--app-dir", "07_API_BACKEND", "--host", "0.0.0.0", "--port", "8000"]
