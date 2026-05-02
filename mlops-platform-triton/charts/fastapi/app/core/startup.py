# core/startup.py

from fastapi import FastAPI
from mlflow.tracking import MlflowClient
import mlflow, os, sys
from loguru import logger
from utils.slack_alerts import send_slack_alert

def register_startup_event(app: FastAPI):
    @app.on_event("startup")
    def startup_event():
        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
        model_name = os.environ.get("MODEL_NAME")

        if not tracking_uri or not model_name:
            logger.error("❌ Missing environment variables: MLFLOW_TRACKING_URI / MODEL_NAME")
            send_slack_alert("❌ [FastAPI] Model loading failed due to missing environment variables")
            app.state.models = {}
            # ✅ It is operationally preferable to expose /metrics even when no model is loaded
            try:
                Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
            except Exception as e:
                logger.warning(f"❌ Failed to expose /metrics (missing environment variables case): {e}")
            return

        app.state.models = {}
        loaded = []

        for alias in ["A", "B"]:
            try:
                mlflow.set_tracking_uri(tracking_uri)
                client = MlflowClient()
                model_uri = f"models:/{model_name}@{alias}"
                model = mlflow.pyfunc.load_model(model_uri)
                version_info = client.get_model_version_by_alias(model_name, alias)

                app.state.models[alias] = {
                    "model": model,
                    "info": {
                        "model_name": model_name,
                        "alias": alias,
                        "version": version_info.version,
                        "run_id": version_info.run_id,
                        "model_uri": model_uri
                    }
                }

                loaded.append(alias)
                logger.info(f"✅ Model loaded successfully: alias={alias}, version={version_info.version}")
            except Exception as e:
                logger.warning(f"❌ Model loading failed: alias={alias}, reason={e}")
                send_slack_alert(f"❌ [FastAPI] Failed to load model alias={alias}: {e}")

        if not loaded:
            logger.error("❌ [FastAPI] Failed to load all models")
            send_slack_alert("❌ [FastAPI] Failed to load all models")
            # Uncomment the next line if you want to keep the process alive on failure
            # sys.exit(1)
        else:
            logger.info(f"✅ Initially loaded models: {loaded}")
            send_slack_alert(f"✅ [FastAPI] Initial model loading complete: {loaded}")
