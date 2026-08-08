# Use Python slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app directory
COPY app/ .

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]