# Dockerfile
FROM --platform=linux/amd64 python:3.10

# Install system dependencies required for PDF processing and OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory for the application
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code into the container
COPY . .

# Set environment variables for input and output directories
ENV INPUT_DIR=/app/input
ENV OUTPUT_DIR=/app/output

# Change working directory to the source code folder
WORKDIR /app/src

# Set the default command to run the main script
CMD ["python", "run.py"]