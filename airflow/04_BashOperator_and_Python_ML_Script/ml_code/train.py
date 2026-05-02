# airflow/ml_code/train.py

import pickle
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
import os

# [1] Log
print("📥 Loading data...")
data = load_iris()
X, y = data.data, data.target

# [2] Training
print("🧠 Training model...")
model = RandomForestClassifier()
model.fit(X, y)

# [3] Save path (container path)
model_path = "/opt/airflow/ml_code/model.pkl"

 # [4] Saving
print(f"💾 Saving model... → {model_path}")
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print("✅ Model save complete!")
