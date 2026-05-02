import mlflow
import mlflow.pyfunc
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://localhost:5000")  # MLflow server URI

# Create FastAPI instance
app = FastAPI()

# Load MLflow model
model = mlflow.pyfunc.load_model("models:/iris-rf@production")  # Using model alias

# Define input data schema
class InputData(BaseModel):
    features: list  # expects 4 feature values

# Prediction API endpoint
@app.post("/predict")
def predict(data: InputData):
    input_df = pd.DataFrame([data.features], columns=["sepal_length", "sepal_width", "petal_length", "petal_width"])
    pred = model.predict(input_df)
    return {"prediction": int(pred[0])}
