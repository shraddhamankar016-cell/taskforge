FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY worker.py .
RUN useradd -u 10001 -m app
USER 10001
EXPOSE 8001
CMD ["python", "worker.py"]
