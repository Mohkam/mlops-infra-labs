FROM python:3.12

WORKDIR /app

COPY app /app
COPY image/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create the logs directory (the path that will be mounted to NFS)
RUN mkdir -p /app/logs

# Create the fastapiuser account (fixed UID: 2001, GID: 2001)
RUN addgroup --gid 2001 fastapigroup && \
    adduser --uid 2001 --gid 2001 --disabled-password --gecos "" fastapiuser

# Grant permissions on the logs folder
RUN chown -R fastapiuser:fastapigroup /app/logs

# Run as a non-root user
USER fastapiuser

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
