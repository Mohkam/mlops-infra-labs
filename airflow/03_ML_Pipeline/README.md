# 🛠️ Airflow Lab - ML Pipeline Dags

## ✅ Goal

- Simulate a machine learning training flow with Airflow DAG
- Structure the flow: data loading → model training → model saving
- Pass results between tasks using XCom

---


## 📁 File Structure

| Filename | Description |
| --- | --- |
| ml_simulation.py | DAG definition file (should be placed in dags/ directory) |

---


## 🛠️ Run Commands

```bash
# Write the DAG file
nano dags/ml_simulation.py

# Check Airflow webserver and scheduler are running
docker-compose up -d
```

---


## 🔧 DAG Code Structure Summary

- `load_data` → Prints "Loading fake data" message and returns path
- `train_model` → Prints received data path and "Model training complete" message
- `save_model` → Prints received model path and "Model saving complete" message

---


## 🔍 How to Check

---

1. Access Airflow UI in browser → [http://localhost:8080](http://localhost:8080/)
2. Turn ON `ml_simulation` in the DAG list
3. Click ▶ to run
4. Check logs for each Task (UI or CLI)

| Task | Log Message |
| --- | --- |
| load_data | 📥 Data loading complete (fake) |
| train_model | 🧪 Data path: /tmp/fake_data.csv  (🚀 Model training complete (fake)) |
| save_model | 💾 Model save path: /tmp/fake_model.pkl   (✅ Save complete (fake)) |

---

## 🧹 Cleanup

- Removing the DAG file will remove the DAG from Airflow
- (No real external resources used — simulation only)

---

## 🧩 Practical Tips

| Real-world Step | Implementation |
| --- | --- |
| Data ingestion | Load CSV/Parquet from S3 / DB |
| Model training | Use sklearn / PyTorch / XGBoost, etc. |
| Persist results | Upload model files to Registry / S3 |
| Share metrics | Use XCom / MLflow to pass metrics |

---

## 🔧 MLOps Integration Next Steps

- This DAG pattern can be extended with MLflow Tracking, Slack notifications, Kubeflow integration, and more.
- A first step towards practical MLOps pipeline automation.
