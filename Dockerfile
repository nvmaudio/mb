FROM python:3.10-slim

# Cài đặt các gói thư viện hệ thống tối giản
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Tiến hành cài đặt các gói python tách biệt để tận dụng bộ nhớ đệm
RUN pip install --no-cache-dir -r requirements.txt

# Mẹo: Tải sẵn model EasyOCR vào trong Docker Image lúc BUILD. 
# Tránh việc khi vào Render tải model lúc Runtime gây tràn RAM (OOM) sập app.
RUN python -c "import easyocr; reader = easyocr.Reader(['en'], gpu=False)"

COPY . .

# Chạy uvicorn với duy nhất 1 worker để tiết kiệm RAM tối đa
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "1"]