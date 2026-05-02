# Based on official Airflow 3.0.2 with Python 3.12 image
FROM apache/airflow:3.0.2-python3.12

# Copy requirements
COPY requirements.txt /tmp/requirements.txt

# Install as airflow user
USER airflow

RUN pip install --no-cache-dir -r /tmp/requirements.txt
