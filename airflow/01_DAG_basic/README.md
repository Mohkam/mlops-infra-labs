# ☁️ Airflow Basic Lab - Local Execution with Docker


## ✅ Goal

- Install and run Airflow in a local environment using Docker
- Create a basic DAG and verify execution in the Web UI

---


## 🧭 Overall Flow

```
[Step 1] Check Docker & Docker Compose installation
[Step 2] Download official Airflow Docker example
[Step 3] Run docker compose to start Airflow services
[Step 4] Access Web UI and run sample DAG
```

---


## 📁 File Structure

| Filename | Description |
| --- | --- |
| docker-compose.yaml | Defines Airflow services (webserver, scheduler, etc.) |
| dags/hello_airflow.py | Sample DAG example file |
| .env | Environment variables for user permissions (AIRFLOW_UID, etc.) |

---


## 🛠️ Run Commands

```bash
# Download official Docker Compose example
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.2/docker-compose.yaml'

# Create working directories
mkdir -p ./dags ./logs ./plugins

# Set user permission variable
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Start containers
docker-compose up -d
```

---


## 🔍 How to Check

### 🔸 Access Web UI

- Open in browser: [http://localhost:8080](http://localhost:8080/)
- Default login credentials:
    - ID: `airflow`
    - PW: `airflow`

---


### 🔸 Register Sample DAG

```python
# Filename: dags/hello_airflow.py

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(dag_id="hello_airflow", 
         start_date=datetime(2023, 1, 1),
         schedule_interval="@daily",
         catchup=False) as dag:
    
    t1 = BashOperator(
        task_id="print_date",
        bash_command="date"
    )

    t2 = BashOperator(
        task_id="say_hello",
        bash_command="echo 'Hello, Airflow!'"
    )

    t1 >> t2
```


---

## 📈 Verify DAG Execution

1. In Airflow UI → Enable `hello_airflow` DAG from the left menu
2. Click the run button → Check execution
3. Check logs: Graph View or Tree View tab

---


## 🧹 Clean Up Resources

```bash
docker-compose down --volumes --remove-orphans
```

---


## 🧩 Additional Notes

- OS: Ubuntu 24.04 (VMware)
- Cluster: Local Docker-based (not Minikube)
- Port: Airflow UI uses 8080 by default
- Reference commands:

```bash
docker ps
docker-compose logs
```
