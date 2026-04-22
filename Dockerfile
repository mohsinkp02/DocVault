FROM python:3.9-slim

WORKDIR /app

# Give permissions to create folders
RUN mkdir -p /app/data /app/logs && chmod 777 /app/data /app/logs

# Install dependencies
COPY ./server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Force rebuild cache bust v2.1.2007
RUN echo "rebuild-v2.1-2007"

# Copy application files
COPY . /app

# Ensure correct permissions after copy
RUN chmod -R 777 /app/data /app/logs

# Expose port (default for HF Spaces)
EXPOSE 7860

# Run as a package so relative imports work in Hugging Face Spaces
CMD ["python", "-m", "server.app"]
