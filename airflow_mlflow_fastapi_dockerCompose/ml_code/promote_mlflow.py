from mlflow.tracking import MlflowClient

def promote_model():
    client = MlflowClient()

    # Get latest un-staged version
    latest_versions = client.get_latest_versions("IrisModel", stages=["None"])
    if not latest_versions:
        # Exit if no registered model is found
        print("❗ No registered model found.")
        return

    latest_version = latest_versions[0].version

    # Transition the model to Production stage
    client.transition_model_version_stage(
        name="IrisModel",
        version=latest_version,
        stage="Production"
    )
    print(f"🚀 IrisModel version {latest_version} → promoted to Production")
