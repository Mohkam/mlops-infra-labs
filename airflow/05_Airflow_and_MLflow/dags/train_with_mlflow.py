# airflow/dags/train_with_mlflow.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
sys.path.append("/opt/airflow/ml_code")

from train_mlflow import run_experiment

with DAG(
    dag_id='mlflow_tracking_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    run_mlflow = PythonOperator(
        task_id='run_mlflow_training',
        python_callable=run_experiment,
    )
