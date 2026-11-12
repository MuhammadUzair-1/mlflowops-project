"""Train and evaluate a task-priority classifier using grouped validation."""

import os

import mlflow
import mlflow.sklearn
import pandas as pd

from mlflow.models import infer_signature
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sqlalchemy import create_engine


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://tasks:tasks@localhost:5432/tasks",
)

EXPERIMENT_NAME = "task-priority-classifier"
REGISTERED_MODEL_NAME = "task-priority-classifier"


def load_dataset():
    engine = create_engine(DATABASE_URL)

    df = pd.read_sql(
        """
        SELECT subject_group, title, description, priority
        FROM ml_training_data
        WHERE priority IS NOT NULL
        """,
        engine,
    )

    if df.empty:
        raise RuntimeError(
            "No training data found. Run python model/generate_data.py first."
        )

    df["text"] = (
        df["title"].fillna("") + " " + df["description"].fillna("")
    )

    return df


def main():
    mlflow.set_tracking_uri(
        os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    )
    mlflow.set_experiment(EXPERIMENT_NAME)

    df = load_dataset()

    X = df["text"]
    y = df["priority"]
    groups = df["subject_group"]

    # Keep entire subjects out of the training set.
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.25,
        random_state=42,
    )

    train_idx, test_idx = next(splitter.split(X, y, groups))

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                max_features=3000,
                ngram_range=(1, 2),
                min_df=2,
                sublinear_tf=True,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
            ),
        ),
    ])

    # Majority-class baseline.
    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X_train, y_train)
    baseline_predictions = baseline.predict(X_test)

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions, average="macro")
    precision = precision_score(
        y_test, predictions, average="macro", zero_division=0
    )
    recall = recall_score(
        y_test, predictions, average="macro", zero_division=0
    )

    baseline_accuracy = accuracy_score(y_test, baseline_predictions)
    baseline_f1 = f1_score(
        y_test, baseline_predictions, average="macro", zero_division=0
    )

    report = classification_report(
        y_test, predictions, zero_division=0
    )
    matrix = confusion_matrix(
        y_test, predictions, labels=["high", "medium", "low"]
    )

    print("\n=== Evaluation results ===")
    print(f"Training rows: {len(X_train)}")
    print(f"Test rows: {len(X_test)}")
    print(f"Training subjects: {groups.iloc[train_idx].nunique()}")
    print(f"Unseen test subjects: {groups.iloc[test_idx].nunique()}")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"Macro F1: {f1:.3f}")
    print(f"Macro precision: {precision:.3f}")
    print(f"Macro recall: {recall:.3f}")
    print(f"Baseline accuracy: {baseline_accuracy:.3f}")
    print(f"Baseline macro F1: {baseline_f1:.3f}")
    print("\nClassification report:")
    print(report)
    print("Confusion matrix (high, medium, low):")
    print(matrix)

    with mlflow.start_run():
        mlflow.log_params({
            "model_type": "tfidf+logistic_regression",
            "split_strategy": "group_holdout_by_subject",
            "test_size": 0.25,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "train_subjects": groups.iloc[train_idx].nunique(),
            "test_subjects": groups.iloc[test_idx].nunique(),
            "max_features": 3000,
            "ngram_range": "(1,2)",
            "class_weight": "balanced",
        })

        mlflow.log_metrics({
            "accuracy": accuracy,
            "f1_macro": f1,
            "precision_macro": precision,
            "recall_macro": recall,
            "baseline_accuracy": baseline_accuracy,
            "baseline_f1_macro": baseline_f1,
        })

        mlflow.log_text(report, "evaluation/classification_report.txt")
        mlflow.log_text(
            str(matrix),
            "evaluation/confusion_matrix.txt",
        )

        input_example = pd.DataFrame({
            "text": X_train.iloc[:2].tolist()
        })

        output_example = pipeline.predict(input_example["text"])
        signature = infer_signature(input_example, output_example)

        mlflow.sklearn.log_model(
            pipeline,
            artifact_path="model",
            registered_model_name=REGISTERED_MODEL_NAME,
            input_example=input_example,
            signature=signature,
        )

    print("\nModel successfully logged and registered in MLflow.")


if __name__ == "__main__":
    main()
