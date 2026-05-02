from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import mlflow.pyfunc
import pandas as pd

app = FastAPI()

# Load MLflow model (Production stage)
mlflow.set_tracking_uri("http://mlflow:5000")
model = mlflow.pyfunc.load_model("models:/IrisModel/Production")

# 🎯 Define input data schema (Pydantic)
class IrisInput(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

@app.get("/")
def home():
    return {"message": "FastAPI + MLflow prediction API"}

@app.post("/predict")
def predict(data: List[IrisInput]):
    # Convert input values to a DataFrame
    input_df = pd.DataFrame([item.dict() for item in data])

    # Rename columns to match model training schema (if needed)
    input_df.columns = [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)"
    ]

    preds = model.predict(input_df)
    return {"predictions": preds.tolist()}

#curl -X POST http://localhost:8000/predict \
#  -H "Content-Type: application/json" \
#  -d '[
#    {
#      "sepal_length": 5.1,
#      "sepal_width": 3.5,
#      "petal_length": 1.4,
#      "petal_width": 0.2
#    },
#    {
#      "sepal_length": 6.0,
#      "sepal_width": 2.9,
#      "petal_length": 4.5,
#      "petal_width": 1.5
#    }
#  ]'

