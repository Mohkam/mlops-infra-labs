### 🧪 MLOps Integrated Hands-on Project

This project uses **MLflow + Airflow + FastAPI** to provide an end-to-end hands-on structure for training, tracking, promoting, and deploying ML models.

## 📁 Project Structure

```bash
mlops_project/
├── airflow/               🛫 Airflow configuration and DAGs
│   ├── dags/              └── Training DAGs (integrated with MLflow)
│   ├── Dockerfile.airflow
│   └── requirements.txt
│
├── fastapi/               ⚡ FastAPI inference API server
│   ├── app/               └── model serving (main.py)
│   ├── Dockerfile.api
│   └── requirements.txt
│
├── ml_code/               🧠 Model training and promotion code
│   ├── train_mlflow.py    └── Training & MLflow logging
│   └── promote_mlflow.py  └── Model promotion (Staging → Production)
│
├── mlflow_store/          🗂️ MLflow experiment DB & artifact storage
│   ├── mlflow.db          └── SQLite-backed store (for local testing)
│   ├── mlruns/            └── Experiment logs
│   └── artifacts/         └── Model files
```

This README preserves existing English technical terms.
