# Container for Hugging Face Spaces (Docker SDK) or any Docker host.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=7860
WORKDIR /app

# CPU-only PyTorch keeps the image small (~800 MB instead of several GB)
RUN pip install --upgrade pip && \
    pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements-deploy.txt .
RUN pip install -r requirements-deploy.txt

COPY app.py index.html main.js index_to_name.json mobilenetv2_leaf_disease_final.pth ./
COPY static ./static

# Hugging Face runs containers as user 1000
RUN useradd -m -u 1000 user && chown -R user /app
USER user

EXPOSE 7860
CMD gunicorn app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120
