FROM python:3.12

WORKDIR /app

COPY app /app
COPY image/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# create logs directory (mount point for NFS)
RUN mkdir -p /app/logs

# create fastapiuser (fixed UID:2001, GID:2001)
RUN addgroup --gid 2001 fastapigroup && \
    adduser --uid 2001 --gid 2001 --disabled-password --gecos "" fastapiuser

# set permissions for logs folder
RUN chown -R fastapiuser:fastapigroup /app/logs

# run as non-root user
USER fastapiuser

# start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
