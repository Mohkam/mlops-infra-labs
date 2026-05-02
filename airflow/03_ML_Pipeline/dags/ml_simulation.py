# dags/ml_simulation.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os

def load_data():
    print("📥 Data loading complete (simulated)")
    return {"data_path": "/tmp/fake_data.csv"}

def train_model(**context):
    data = context['ti'].xcom_pull(task_ids='load_data')
    print(f"🧪 Data path: {data['data_path']}")
    print("🚀 Model training complete (simulated)")
    return {"model_path": "/tmp/fake_model.pkl"}

def save_model(**context):
    model = context['ti'].xcom_pull(task_ids='train_model')
    print(f"💾 Model save path: {model['model_path']}")
    print("✅ Save complete (simulated)")

with DAG(
    dag_id='ml_simulation',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    t1 = PythonOperator(
        task_id='load_data',
        python_callable=load_data
    )

    t2 = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
        provide_context=True
    )

    t3 = PythonOperator(
        task_id='save_model',
        python_callable=save_model,
        provide_context=True
    )

    t1 >> t2 >> t3
