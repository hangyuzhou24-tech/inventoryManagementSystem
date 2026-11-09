FROM python:3.13-slim

WORKDIR /app

# 先装依赖再拷代码，利用 Docker 层缓存加速重新构建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
