# airflow/ml_code/train_mlflow.py

import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import os
import pickle

def run_experiment():
    print("Starting MLflow experiment")
    mlflow.set_tracking_uri("file:/opt/airflow/mlruns")
    mlflow.set_experiment("airflow_mlflow_example")

    with mlflow.start_run():
        # [1] Data loading
        data = load_iris()
        X, y = data.data, data.target

        # [2] Model definition
        model = RandomForestClassifier(n_estimators=50, max_depth=3)
        model.fit(X, y)
        preds = model.predict(X)

        acc = accuracy_score(y, preds)

        # [3] MLflow logging
        mlflow.log_param("n_estimators", 50)
        mlflow.log_param("max_depth", 3)
        mlflow.log_metric("accuracy", acc)

        mlflow.sklearn.log_model(model, "model")

        print("MLflow logging complete: acc =", acc)
