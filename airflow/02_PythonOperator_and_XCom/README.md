# 🛠️ Airflow Lab - PythonOperator + BashOperator + XCom

## ✅ Goal

- Generate a message with PythonOperator and pass it via XCom
- Verify data transfer between tasks using XCom
- Execute simple shell commands with BashOperator
- Visualize the entire flow in Graph View and logs

---


## 📁 File Structure

| Filename | Description |
| --- | --- |
| `python_bash_xcom.py` | DAG definition (PythonOperator + XCom + BashOperator) |

---


## 🛠️ Run Commands

```bash
# Add python_bash_xcom.py to the dags/ directory

# Check Airflow webserver and scheduler are running
docker-compose up -d

# Access UI
http://localhost:8080

# Trigger DAG and check graph & logs
```

---


## 🔍 How to Check

### 🔸 Check in UI

1. Turn ON `python_bash_xcom` DAG
2. ▶ Click → Trigger
3. Check each task in Graph View
4. In the Logs tab, check for the following messages:
    - `generate_task`: 🌟 Hello from PythonOperator!
    - `consume_task`: 📬 XCom received message: ...
    - `bash_task`: 🎉 Bash task is running!

---


## 💡 Key Concepts

| Concept | Description |
| --- | --- |
| PythonOperator | Executes a Python function |
| BashOperator | Executes a Bash command |
| XCom | Passes small data between tasks |
| provide_context | Provides execution context for using XCom |

---

## 🧩 Practical Tips

- XCom is suitable for sending lightweight messages (e.g., paths, status codes)
- For large data, store it in external storage (S3, DB) and pass only the path

---

## 🔧 MLOps Integration

- Pass model IDs from training tasks to evaluation tasks
- Based on evaluation results, branch actions like registration or serving

---

## 🧹 Cleanup

```bash
# Remove the DAG file if needed
rm dags/python_bash_xcom.py
```

---

## 🧩 Additional References

- OS: Ubuntu 24.04 (VMware)
- Cluster: Local Docker-based cluster (not Minikube)
- Port: Airflow UI uses 8080 by default
- Helpful commands:

```bash
docker ps
docker-compose logs
```
