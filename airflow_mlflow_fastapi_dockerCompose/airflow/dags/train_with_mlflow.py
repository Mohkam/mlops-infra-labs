# airflow/dags/train_with_mlflow.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
sys.path.append("/opt/airflow/ml_code")  # set module path

from train_mlflow import run_experiment  # import training function
from promote_mlflow import promote_model  # import promotion function

default_args = {
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='train_with_mlflow',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['ml', 'mlflow'],
) as dag:

    # Model training + registration
    train_task = PythonOperator(
        task_id='run_training', 
        python_callable=run_experiment,
    )
    # Train model and register

    # Promote the latest version to the Production stage
    promote_task = PythonOperator(
        task_id='promote_model_to_production',
        python_callable=promote_model,
    )

    # Define task order
    train_task >> promote_task


