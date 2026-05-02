# dags/python_bash_xcom.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime

def generate_message():
    return "🌟 Hello from PythonOperator!"

def print_xcom_message(**context):
    msg = context['ti'].xcom_pull(task_ids='generate_task')
    print(f"📬 XCom received message: {msg}")

with DAG(
    dag_id='python_bash_xcom',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    generate_task = PythonOperator(
        task_id='generate_task',
        python_callable=generate_message,
    )

    consume_task = PythonOperator(
        task_id='consume_task',
        python_callable=print_xcom_message,
        provide_context=True
    )

    bash_task = BashOperator(
        task_id='bash_echo',
        bash_command="echo '🎉 Bash task is running!'"
    )

    generate_task >> consume_task >> bash_task
