FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    mlflow==2.22.5 \
    "sqlalchemy>=2.0,<2.1" \
    psycopg2-binary \
    boto3

EXPOSE 5000
