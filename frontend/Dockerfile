# Use an official Python slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=false

# Set working directory
WORKDIR /app

# Copy requirements first
COPY frontend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the frontend files
COPY frontend/ .

# Expose the port
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
