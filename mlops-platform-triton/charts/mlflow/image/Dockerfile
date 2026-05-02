FROM ghcr.io/mlflow/mlflow:v2.13.0

# Install system tools
RUN apt-get update && apt-get install -y \
    curl \
    telnet \
    postgresql-client \
    awscli \
    procps \
 && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
