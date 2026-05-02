import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from utils.slack_alerts import send_slack_alert
from loguru import logger
from core.config import settings

def load_model_by_alias(alias: str):
    try:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        client = MlflowClient()
        model_uri = f"models:/{settings.model_name}@{alias}"
        model = mlflow.pyfunc.load_model(model_uri)
        version_info = client.get_model_version_by_alias(settings.model_name, alias)

        logger.info(f"✅ Model loaded successfully: alias={alias}, version={version_info.version}")
        return {
            "model": model,
            "info": {
                "model_name": settings.model_name,
                "alias": alias,
                "version": version_info.version,
                "run_id": version_info.run_id,
                "model_uri": model_uri,
            }
        }
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        send_slack_alert(f"❌ Model loading failed: alias={alias}, {e}")
        return None
