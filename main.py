import os
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import mlflow
import pandas as pd

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

import cache
from database import Base, engine, get_db
from models import TaskModel


# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI", "http://localhost:5000"
)
MODEL_VERSION = os.getenv("MODEL_VERSION", "3")
MODEL_URI = os.getenv(
    "MLFLOW_MODEL_URI",
    f"models:/task-priority-classifier/{MODEL_VERSION}"
)

model = None

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("mlflowops-api")


# Prometheus metrics
PREDICTIONS_TOTAL = Counter(
    "mlflowops_predictions_total",
    "Total number of model predictions",
    ["model_version"],
)

PREDICTION_ERRORS_TOTAL = Counter(
    "mlflowops_prediction_errors_total",
    "Total number of failed model predictions",
    ["model_version"],
)


PREDICTION_LATENCY = Histogram(
    "mlflowops_prediction_latency_seconds",
    "Prediction latency in seconds",
    ["model_version"],
)

MODEL_INFO = Gauge(
    "mlflowops_model_info",
    "Currently loaded MLflow model version",
    ["model_version"],
)


# Load model during application startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    print(f"Loading MLflow model: {MODEL_URI}")

    model = mlflow.pyfunc.load_model(MODEL_URI)

    MODEL_INFO.labels(model_version=MODEL_VERSION).set(1)

    print(f"Successfully loaded model version {MODEL_VERSION}")

    yield

    model = None


app = FastAPI(
    title="Tasks API with MLflow",
    description="Task management and MLflow model prediction API",
    lifespan=lifespan,
)

Base.metadata.create_all(bind=engine)


# Existing task schemas
class Task(BaseModel):
    title: str
    description: Optional[str] = None
    done: bool = False
    priority: Optional[str] = None


class TaskOut(Task):
    id: int

    model_config = {"from_attributes": True}


# Prediction request schema
class PredictionRequest(BaseModel):
    title: str
    description: Optional[str] = None


# Health endpoint
@app.get("/health")
def health():
    return {"status": "ok", "service": "tasks-api"}


# MLflow prediction endpoint
@app.post("/predict")
def predict(request: PredictionRequest):
    start_time = time.perf_counter()

    if model is None:
        latency = time.perf_counter() - start_time
        PREDICTION_ERRORS_TOTAL.labels(model_version=MODEL_VERSION).inc()
        PREDICTION_LATENCY.labels(model_version=MODEL_VERSION).observe(latency)
        LOGGER.error(json.dumps({
            "event": "prediction_failed",
            "model_version": MODEL_VERSION,
            "reason": "model_not_loaded",
        }))
        raise HTTPException(status_code=503, detail="MLflow model is not loaded")

    text = f"{request.title} {request.description or ''}".strip()

    try:
        input_data = pd.DataFrame({"text": [text]})
        prediction = model.predict(input_data)
        latency = time.perf_counter() - start_time
        priority = str(prediction[0])

        PREDICTIONS_TOTAL.labels(model_version=MODEL_VERSION).inc()
        PREDICTION_LATENCY.labels(model_version=MODEL_VERSION).observe(latency)

        LOGGER.info(json.dumps({
            "event": "prediction_succeeded",
            "model_version": MODEL_VERSION,
            "predicted_priority": priority,
            "latency_seconds": round(latency, 6),
        }))

        return {
            "input": text,
            "predicted_priority": priority,
            "model_version": MODEL_VERSION,
            "latency_seconds": round(latency, 6),
        }

    except Exception as error:
        latency = time.perf_counter() - start_time
        PREDICTION_ERRORS_TOTAL.labels(model_version=MODEL_VERSION).inc()
        PREDICTION_LATENCY.labels(model_version=MODEL_VERSION).observe(latency)

        LOGGER.exception(json.dumps({
            "event": "prediction_failed",
            "model_version": MODEL_VERSION,
            "error": str(error),
            "latency_seconds": round(latency, 6),
        }))

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}",
        )


# Prometheus metrics endpoint
@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Existing task endpoints
@app.get("/tasks", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    cached = cache.get_cached_tasks()

    if cached is not None:
        return cached

    result = [
        TaskOut.model_validate(t).model_dump()
        for t in db.query(TaskModel).order_by(TaskModel.id).all()
    ]

    cache.set_cached_tasks(result)
    return result


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: Task, db: Session = Depends(get_db)):
    db_task = TaskModel(**task.model_dump())

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    cache.invalidate_task_cache(db_task.id)

    return db_task


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    cached = cache.get_cached_task(task_id)

    if cached is not None:
        return cached

    db_task = db.get(TaskModel, task_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result = TaskOut.model_validate(db_task).model_dump()
    cache.set_cached_task(task_id, result)

    return result


@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task: Task,
    db: Session = Depends(get_db),
):
    db_task = db.get(TaskModel, task_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task.model_dump().items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)

    cache.invalidate_task_cache(task_id)

    return db_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.get(TaskModel, task_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()

    cache.invalidate_task_cache(task_id)
