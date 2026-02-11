FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including fonts for watermark, Tesseract OCR, LibreOffice, poppler for PDF, MediaPipe)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libglib2.0-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgtk-3-0 \
    fonts-dejavu-core \
    tesseract-ocr \
    tesseract-ocr-eng \
    libreoffice-writer \
    libreoffice-calc \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY models.py .
COPY database.py .
COPY auth.py .
COPY api_auth.py .
COPY schemas.py .
COPY watermark.py .
COPY tools.py .
COPY static/ static/

# Create necessary directories
RUN mkdir -p uploads outputs

# Expose port
EXPOSE 5000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
