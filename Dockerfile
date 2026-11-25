# Container for Hugging Face Spaces (Docker SDK) or any Docker host.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=7860
WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app.py ./
COPY model ./model
COPY web ./web

# Hugging Face runs containers as user 1000
RUN useradd -m -u 1000 user && chown -R user /app
USER user

EXPOSE 7860
CMD gunicorn app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120
