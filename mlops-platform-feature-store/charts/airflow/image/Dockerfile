# Based on the official Airflow 3.0.2 with Python 3.12 image
FROM apache/airflow:3.0.2-python3.12

# Copy requirements
COPY requirements.txt requirements.txt

# Install packages as the airflow user
USER airflow

RUN pip install --no-cache-dir -r requirements.txt
