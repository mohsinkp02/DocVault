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

# Run behind a production WSGI server on the Spaces port
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "server.app:create_app()"]
