from fastapi import FastAPI, Request
import mlflow.pyfunc
import mlflow
from mlflow.tracking import MlflowClient
import os

app = FastAPI()
model = None
model_info = {}

def load_model_from_mlflow():
    global model, model_info

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    model_name = os.environ.get("MODEL_NAME")
    model_stage = os.environ.get("MODEL_STAGE", "Staging")

    mlflow.set_tracking_uri(tracking_uri)
    model_uri = f"models:/{model_name}/{model_stage}"

    model = mlflow.pyfunc.load_model(model_uri)

    client = MlflowClient()
    latest = client.get_latest_versions(name=model_name, stages=[model_stage])[0]
    run_id = latest.run_id
    version = latest.version

    print(f"✅ Reloaded model: name={model_name}, stage={model_stage}, version={version}, run_id={run_id}")
    model_info = {
        "model_name": model_name,
        "stage": model_stage,
        "version": version,
        "run_id": run_id,
        "model_uri": model_uri,
    }

@app.on_event("startup")
def startup_event():
    load_model_from_mlflow()

@app.get("/")
def root():
    return {"message": "FastAPI MLOps is running!"}

@app.get("/model-info")
def get_model_info():
    return model_info

@app.post("/predict")
async def predict(request: Request):
    input_data = await request.json()
    prediction = model.predict(input_data)
    return {"prediction": prediction.tolist()}

@app.post("/reload")
def reload_model():
    try:
        load_model_from_mlflow()
        return {"status": "success", "message": "🔁 Model reloaded successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Reload failed: {str(e)}"}
