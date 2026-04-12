# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first for better caching
COPY server/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create data and logs directories
RUN mkdir -p data logs

# Set environment variables
ENV FLASK_APP=server/app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask application
CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0"]
