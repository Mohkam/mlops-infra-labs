# Based on Airflow 3.0.2 with Python 3.12 official image
FROM apache/airflow:3.0.2-python3.12

# Copy requirements
COPY requirements.txt /tmp/requirements.txt

# airflow 권한으로 pip install
USER airflow

# pip install as airflow user
RUN pip install --no-cache-dir -r /tmp/requirements.txt
