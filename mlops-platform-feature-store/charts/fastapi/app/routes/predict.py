from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List
import pandas as pd
from services.alias_selector import get_alias
from core.config import settings
from utils.slack_alerts import send_slack_alert
from loguru import logger
from fastapi import Request

router = APIRouter()

class PredictInput(BaseModel):
    data: List[List[float]]

@router.post("/predict")
async def ab_predict(request: Request, input_data: PredictInput, x_client_id: str = Header(...)):
    models = getattr(request.app.state, "models", {})
    if not models:
        raise HTTPException(status_code=503, detail="❌ Model not loaded")

    alias = get_alias(x_client_id)
    if alias not in models:
        raise HTTPException(status_code=503, detail=f"❌ Model {alias} not loaded")

    try:
        df = pd.DataFrame(input_data.data)
        prediction = models[alias]["model"].predict(df)
        logger.info(f"✅ Prediction succeeded: mode={settings.alias_selection_mode}, alias={alias}, client_id={x_client_id}")
        return {
            "variant": alias,
            "mode": settings.alias_selection_mode,
            "client_id": x_client_id,
            "prediction": prediction.tolist()
        }
    except Exception as e:
        logger.exception("❌ Prediction failed")
        send_slack_alert(f"❌ [FastAPI] Prediction failed (alias={alias}): {e}")
        raise HTTPException(status_code=500, detail=f"❌ Prediction failed: {e}")

@router.post("/variant/{alias}/predict")
async def predict_by_alias(alias: str, input_data: PredictInput, request: Request):
    models = getattr(request.app.state, "models", {})
    if alias not in models:
        raise HTTPException(status_code=503, detail=f"⚠️ Model {alias} not loaded")

    try:
        df = pd.DataFrame(input_data.data)
        prediction = models[alias]["model"].predict(df)
        logger.info(f"✅ Manual prediction succeeded: alias={alias}")
        return {
            "variant": alias,
            "prediction": prediction.tolist()
        }
    except Exception as e:
        logger.exception("❌ Manual prediction failed")
        send_slack_alert(f"❌ [FastAPI] Manual prediction failed (alias={alias}): {e}")
        raise HTTPException(status_code=500, detail=f"❌ Manual prediction failed: {e}")
