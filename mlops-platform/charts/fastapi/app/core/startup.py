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
            logger.error("❌ Missing env vars: MLFLOW_TRACKING_URI / MODEL_NAME")
            send_slack_alert("❌ [FastAPI] model loading failed due to missing env vars")
            app.state.models = {}
            # expose /metrics even if model is missing
            try:
                Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
            except Exception as e:
                logger.warning(f"⚠️ /metrics expose failed (missing env case): {e}")
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
                logger.info(f"✅ 모델 로딩 성공: alias={alias}, version={version_info.version}")
            except Exception as e:
                logger.warning(f"⚠️ 모델 로딩 실패: alias={alias}, 이유={e}")
                send_slack_alert(f"❌ [FastAPI] 모델 alias={alias} 로딩 실패: {e}")

        if not loaded:
            logger.error("🔥 [FastAPI] 모델 전부 로딩 실패")
            send_slack_alert("🔥 [FastAPI] 전 모델 로딩 실패")
            # 필요시 종료 유지하려면 다음 라인 주석 해제
            # sys.exit(1)
        else:
            logger.info(f"✅ 초기 로딩된 모델: {loaded}")
            send_slack_alert(f"✅ [FastAPI] 모델 초기 로딩 완료: {loaded}")
