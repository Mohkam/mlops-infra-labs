import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import pandas as pd

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("iris-rf-exp")

with mlflow.start_run():
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=100, max_depth=3)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)

    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 3)
    mlflow.log_metric("accuracy", acc)

    mlflow.sklearn.log_model(clf, "model")

