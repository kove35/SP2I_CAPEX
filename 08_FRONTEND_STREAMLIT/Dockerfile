FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY 08_FRONTEND_STREAMLIT/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY 08_FRONTEND_STREAMLIT /app

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
