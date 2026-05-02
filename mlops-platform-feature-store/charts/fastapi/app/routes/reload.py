from fastapi import APIRouter, HTTPException, Header, Request
from core.config import settings
from services.model_loader import load_model_by_alias
from utils.slack_alerts import send_slack_alert
import secrets

router = APIRouter()

@router.post("/variant/{alias}/reload")
def reload_model(request: Request, alias: str, x_token: str = Header(...)):
    models = getattr(request.app.state, "models", {})

    expected_token = settings.reload_secret_token
    if not expected_token:
        raise HTTPException(status_code=500, detail="❌ Server configuration error: authentication token is not set")

    if not secrets.compare_digest(x_token, expected_token):
        raise HTTPException(status_code=403, detail="❌ Access denied")

    loaded_model = load_model_by_alias(alias)
    if not loaded_model:
        raise HTTPException(status_code=500, detail="❌ Model loading failed")

    request.app.state.models[alias] = loaded_model
    version_info = loaded_model["info"]
    send_slack_alert(f"🔁  [FastAPI] Model {alias} hot swap complete: v{version_info['version']}, run_id={version_info['run_id']}")

    return {"status": "success", "variant": alias, "version": version_info["version"]}
