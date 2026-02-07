FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY static/ static/

# Create necessary directories
RUN mkdir -p uploads outputs

# Expose port
EXPOSE 5000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
