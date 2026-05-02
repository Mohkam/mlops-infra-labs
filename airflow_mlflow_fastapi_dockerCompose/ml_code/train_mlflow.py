# ml_code/train_mlflow.py

import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def run_experiment():
    # Experiment setup
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("iris_experiment")

    with mlflow.start_run() as run:
        # Prepare data
        data = load_iris()
        X, y = data.data, data.target

        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        preds = model.predict(X)

        # Compute metrics
        acc = accuracy_score(y, preds)

        # Logging to MLflow
        mlflow.log_param("n_estimators", 100)
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(model, artifact_path="model", registered_model_name="IrisModel")

        print(f"✅ Run ID: {run.info.run_id}, Accuracy: {acc}")

if __name__ == "__main__":
    run_experiment()
