# airflow/dags/run_train_script.py

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='bash_run_train',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    run_training = BashOperator(
        task_id='run_train_script',
        bash_command='python3 /opt/airflow/ml_code/train.py'
    )
