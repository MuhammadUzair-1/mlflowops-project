
# MLflowOps — End-to-End MLOps Platform

## 1. Project Overview

MLflowOps is an end-to-end MLOps infrastructure project that demonstrates how to build, deploy, manage, and monitor a machine-learning application using modern DevOps and cloud-native technologies.

The project implements an automated workflow covering the machine-learning model lifecycle and application delivery. It combines infrastructure provisioning, containerisation, model tracking, automated training, model version management, Kubernetes deployment, continuous integration and delivery, and application monitoring.

The application exposes a machine-learning inference service through a REST API. The API loads a registered model from MLflow and uses it to generate predictions from incoming requests.

The infrastructure is deployed on Amazon Web Services (AWS), with Amazon Elastic Kubernetes Service (EKS) providing the Kubernetes environment. Terraform is used for infrastructure provisioning, Docker packages the application, Amazon Elastic Container Registry (ECR) stores container images, and GitHub Actions orchestrates the CI/CD workflow.

MLflow manages experiment tracking and model registration, while Prometheus and Grafana provide application-level monitoring and visualisation.

### Project objectives

The main objectives were to:

- Provision cloud infrastructure using Infrastructure as Code.
- Package a machine-learning inference service into a Docker container.
- Automate model training and experiment tracking.
- Manage model versions through the MLflow Model Registry.
- Store model artifacts in Amazon S3.
- Build an automated CI/CD pipeline using GitHub Actions.
- Deploy the application to Amazon EKS.
- Separate staging and production application deployments.
- Collect prediction metrics using Prometheus.
- Visualise application performance and model information using Grafana.
- Configure alerting based on prediction failures.
- Implement structured logging with model-version information.

---

## 2. Technology Stack

| Area | Technology | Purpose |
|---|---|---|
| Cloud platform | AWS | Cloud infrastructure and application hosting |
| Infrastructure as Code | Terraform | Automated infrastructure provisioning |
| Containerisation | Docker | Packaging the inference application |
| Container registry | Amazon ECR | Storing and distributing Docker images |
| Container orchestration | Amazon EKS | Running the application on Kubernetes |
| Kubernetes CLI | kubectl | Managing Kubernetes resources |
| ML lifecycle management | MLflow | Experiment tracking and model registry |
| Artifact storage | Amazon S3 | Storing model artifacts |
| Model serving | FastAPI | Exposing the inference service through REST endpoints |
| CI/CD | GitHub Actions | Automating testing, building, training and deployment |
| Cloud compute | Amazon EC2 Spot | Running model-training workloads |
| Monitoring | Prometheus | Collecting application and infrastructure metrics |
| Visualisation | Grafana | Monitoring dashboards and alert rules |
| Application metrics | prometheus-client | Exposing custom metrics from FastAPI |
| Source control | Git and GitHub | Version control and workflow integration |
| Container deployment | Kubernetes Deployments and Services | Managing application instances and network access |

---

## 3. High-Level Architecture

The platform connects the machine-learning lifecycle with the application delivery lifecycle.

The overall workflow is:

```text
                     DEVELOPER
                         |
                         v
                  GitHub Repository
                         |
                         v
                 GitHub Actions CI/CD
                         |
             +-----------+-----------+
             |                       |
             v                       v
        Python Tests             Docker Build
                                     |
                                     v
                               Amazon ECR
                                     |
                                     v
                           EC2 Spot Training
                                     |
                                     v
                              MLflow Tracking
                                     |
                                     v
                            MLflow Model Registry
                                     |
                                     v
                             Model Evaluation
                                     |
                                     v
                           Model Promotion
                                     |
                                     v
                              Amazon EKS
                                     |
                     +---------------+---------------+
                     |                               |
                     v                               v
                  Staging                        Production
                     |                               |
                     +---------------+---------------+
                                     |
                                     v
                              FastAPI Service
                                     |
                                     v
                              Model Inference
                                     |
                     +---------------+---------------+
                     |                               |
                     v                               v
                 Prometheus                        JSON Logs
                     |
                     v
                  Grafana
                     |
                     v
               Metrics and Alerts
```

### Main architectural components

**GitHub Repository**

Contains the application source code, training code, infrastructure definitions, container configuration, Kubernetes manifests and CI/CD workflow.

**GitHub Actions**

Coordinates the automation workflow, including testing, image building, model training, model evaluation, promotion and Kubernetes deployment.

**AWS Infrastructure**

Provides the compute, networking, container registry, artifact storage, Kubernetes environment and IAM permissions required by the platform.

**MLflow**

Tracks training runs and manages registered model versions.

**FastAPI**

Provides the HTTP interface through which users submit prediction requests.

**Prometheus and Grafana**

Collect and display application metrics, including prediction counts, prediction errors and the currently loaded model version.

---

## 4. AWS Infrastructure and Terraform

Terraform is used to define and provision the cloud infrastructure required by the application.

Using Infrastructure as Code allows infrastructure resources and their configuration to be maintained in version-controlled files rather than relying exclusively on manual configuration through the AWS Console.

### AWS environment

The project uses the following AWS environment:

| Resource | Configuration |
|---|---|
| AWS Region | eu-central-1 (Frankfurt) |
| AWS Account | 686699774218 |
| EKS Cluster | uzair-mlflowops-eks |
| ECR Repository | mlflowops-api |
| S3 Bucket | uzair-mlflowops-artifacts-686699774218-eu-central-1 |
| IAM Role | GitHubActionsMLflowOpsRole |

### Amazon EKS

Amazon Elastic Kubernetes Service provides the Kubernetes control plane for the application.

The cluster is named:

`uzair-mlflowops-eks`

The application is deployed into the `mlflow` Kubernetes namespace.

Kubernetes Deployments manage the application pods, while Kubernetes Services provide network access to the running application.

The project maintains separate application deployments for staging and production.

### Amazon ECR

Amazon Elastic Container Registry is used to store the Docker images generated by the CI/CD pipeline.

The repository is:

`mlflowops-api`

The pipeline builds a Docker image from the application source code and pushes the resulting image to ECR.

The Kubernetes deployments use images from this repository.

### Amazon S3

Amazon S3 is used as the artifact-storage backend for MLflow.

The configured bucket is:

`uzair-mlflowops-artifacts-686699774218-eu-central-1`

It provides persistent storage for model artifacts independently of the lifecycle of the application containers.

### IAM and GitHub Actions authentication

The CI/CD workflow uses the IAM role:

`GitHubActionsMLflowOpsRole`

GitHub Actions authenticates to AWS using OpenID Connect (OIDC).

This approach allows the workflow to obtain temporary AWS credentials through an IAM trust relationship rather than storing permanent AWS access keys in the GitHub repository.

The IAM role provides the permissions required by the workflow to interact with AWS resources.

---

## 5. Machine-Learning Lifecycle with MLflow

MLflow is responsible for experiment tracking and model version management.

The project uses the MLflow Tracking Server and Model Registry to manage the lifecycle of the prediction model.

### Experiment tracking

The training workflow communicates with the MLflow Tracking Server.

The tracking URI used by the project is:

```text
http://af0ad1a3a2f054ba1b81ae5db45a01c7-1408216736.eu-central-1.elb.amazonaws.com:5000
```

Training runs are recorded in MLflow so that model-development activities can be tracked centrally.

### Model registration

The trained model is registered under the following name:

```text
task-priority-classifier
```

The MLflow Model Registry maintains model versions.

The FastAPI application loads the registered model using the MLflow model URI:

```text
models:/task-priority-classifier/<MODEL_VERSION>
```

The model version is configurable through the `MODEL_VERSION` environment variable.

The application also supports the `MLFLOW_MODEL_URI` environment variable for specifying the model URI directly.

This separates the model lifecycle from the application container. A new registered model version can be selected through deployment configuration without embedding the model artifact directly into the Docker image.

### Model evaluation and promotion

The automated pipeline includes an evaluation stage after training.

The workflow evaluates the newly trained model and performs the configured promotion process before deploying the selected model to the application environment.

The pipeline supports staging and production deployment stages.

This creates a controlled workflow in which model training and application deployment are coordinated through CI/CD.

---

## 6. Model Training Infrastructure

The project uses Amazon EC2 Spot capacity for model-training workloads.

The training process is integrated into the GitHub Actions workflow rather than being limited to a manual local execution.

The training stage is designed to:

1. Start the configured EC2 Spot training workload.
2. Execute the model-training process.
3. Connect the training process to the MLflow Tracking Server.
4. Record the training run in MLflow.
5. Store model artifacts in the configured artifact storage.
6. Register the resulting model.
7. Pass the workflow to the evaluation and promotion stages.

Using EC2 Spot capacity separates the training workload from the Kubernetes inference workload.

The Kubernetes cluster is therefore responsible for serving predictions, while the training workload executes through the separate cloud-compute stage.

---

## 7. FastAPI Model-Serving Application

FastAPI provides the REST interface for the machine-learning model.

The serving application loads the registered MLflow model and exposes endpoints for health checks, predictions and Prometheus metrics.

### Model loading

The application obtains its model configuration from environment variables.

```python
MODEL_VERSION = os.getenv("MODEL_VERSION", "3")

MODEL_URI = os.getenv(
    "MLFLOW_MODEL_URI",
    f"models:/task-priority-classifier/{MODEL_VERSION}"
)
```

This configuration allows the model version to be changed independently of the application source code.

The deployed application was verified with model version 8 loaded.

### API endpoints

The application exposes the following endpoints:

| Endpoint | HTTP Method | Purpose |
|---|---|---|
| `/health` | GET | Application health check |
| `/predict` | POST | Generate a prediction |
| `/metrics` | GET | Expose Prometheus metrics |

### Health endpoint

The health endpoint provides an application-level health check.

It can be used by deployment checks and Kubernetes health monitoring to determine whether the application is responding.

### Prediction endpoint

The prediction endpoint accepts a task title and uses the loaded model to generate a prediction.

Example request:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"title":"This task is urgent and needs immediate attention"}'
```

The API processes the request and returns the prediction result.

The serving application is independent of the training process. It loads a registered model and handles inference requests.

### Metrics endpoint

The `/metrics` endpoint exposes application metrics in Prometheus' exposition format.

The endpoint is implemented using the Python `prometheus-client` library.

Prometheus periodically scrapes this endpoint to collect the metrics generated by the application.

---

## 8. Docker Containerisation

Docker is used to package the FastAPI serving application and its Python dependencies into a container image.

The container provides a consistent runtime environment for the application.

The CI/CD workflow builds the image and pushes it to Amazon ECR.

The image is then referenced by the Kubernetes Deployments.

The containerisation workflow is:

```text
Application Source Code
          |
          v
     Docker Build
          |
          v
    Docker Image
          |
          v
      Amazon ECR
          |
          v
     Amazon EKS
          |
          v
    Running Pod
```

The deployment process uses versioned container images so that the Kubernetes workload can reference a specific application build.

---

## 9. Kubernetes Deployment

Amazon EKS runs the FastAPI application as a Kubernetes workload.

The application namespace is:

```text
mlflow
```

The deployment architecture separates staging and production.

### Staging deployment

The staging application uses:

```text
Deployment: mlflowops-api
Service:    mlflowops-api
```

The staging environment provides a deployment target for the application before production promotion.

### Production deployment

The production application uses:

```text
Deployment: mlflowops-api-production
Service:    mlflowops-api-production
```

This separation allows the staging and production workloads to be managed independently.

### Kubernetes Services

The staging application is exposed internally through a Kubernetes ClusterIP Service.

Its service configuration includes:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mlflowops-api
  labels:
    app: mlflowops-api
spec:
  selector:
    app: mlflowops-api
  ports:
    - name: http
      port: 8000
      targetPort: 8000
```

The Service selects the application pods using Kubernetes labels and forwards traffic to port 8000.

The named HTTP port is also used by the Prometheus ServiceMonitor configuration.

### Model version configuration

The model version is supplied through the application environment configuration.

This enables the staging and production deployments to load the model version selected by the pipeline.

The model registry therefore remains the central source of registered model versions.

---

## 10. CI/CD Pipeline with GitHub Actions

GitHub Actions automates the software delivery and model deployment workflow.

The main workflow is:

```text
.github/workflows/mlflowops-pipeline.yml
```

The pipeline combines conventional application CI/CD with machine-learning lifecycle operations.

### Pipeline stages

**Stage 1 — Automated testing**

The workflow executes the Python tests before proceeding with the image-building and deployment stages.

This provides an automated validation step for application changes.

**Stage 2 — Docker image build**

The workflow builds the application container image.

The resulting image is tagged and prepared for publication to Amazon ECR.

**Stage 3 — ECR image publication**

GitHub Actions authenticates to AWS using OIDC and the configured IAM role.

The Docker image is pushed to the `mlflowops-api` ECR repository.

**Stage 4 — Model training**

The workflow supports an optional training stage.

When enabled, the pipeline launches the EC2 Spot training workload.

The training process records its run in MLflow and registers the resulting model.

**Stage 5 — Model evaluation and staging promotion**

The workflow evaluates the newly trained model and performs the configured staging promotion process.

The selected model version is then available to the staging deployment.

**Stage 6 — Staging deployment**

The pipeline deploys the application to Amazon EKS.

The staging Kubernetes Deployment is:

```text
mlflowops-api
```

The workflow then performs the configured deployment and application health checks.

**Stage 7 — Production approval**

The production stage is separated from staging and includes an approval gate.

This introduces a controlled transition between staging and production.

**Stage 8 — Production promotion and deployment**

After the production approval stage, the workflow promotes the selected model and deploys the application to the production Kubernetes Deployment:

```text
mlflowops-api-production
```

### Workflow execution

The workflow supports manual execution through GitHub Actions with two inputs:

- `run_training`
- `deploy`

The following command starts the workflow with both operations enabled:

```bash
gh workflow run mlflowops-pipeline.yml --ref main \
  -f run_training=true \
  -f deploy=true
```

This allows the user to trigger a complete training and deployment workflow without manually executing each stage.

### CI/CD design

The pipeline combines several important MLOps practices:

- Automated testing before delivery.
- Container image creation and publication.
- Cloud-based model training.
- Centralised experiment tracking.
- Model evaluation and version management.
- Staging and production separation.
- Controlled production promotion.
- Automated Kubernetes deployment.

The result is a delivery workflow in which the application and its machine-learning model are managed through a coordinated automation process.

---

## 11. Application Observability

The serving API exposes custom Prometheus metrics to monitor prediction activity and model information.

The monitoring stack is deployed inside the EKS environment.

The project uses the Prometheus community `kube-prometheus-stack` Helm chart.

The Helm release is:

```text
monitoring
```

The monitoring namespace is:

```text
monitoring
```

### Prometheus

Prometheus collects metrics from the FastAPI application through its `/metrics` endpoint.

A Kubernetes ServiceMonitor defines how Prometheus discovers and scrapes the application.

The ServiceMonitor is named:

```text
mlflowops-api
```

It is deployed in the `monitoring` namespace and selects the application Service in the `mlflow` namespace.

The relevant configuration is:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mlflowops-api
  namespace: monitoring
  labels:
    release: monitoring
spec:
  namespaceSelector:
    matchNames:
      - mlflow
  selector:
    matchLabels:
      app: mlflowops-api
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

Prometheus discovers the application endpoint through Kubernetes service discovery and scrapes the metrics every 15 seconds.

The application target was verified as `UP` in Prometheus.

### Custom application metrics

The serving application defines the following metrics:

**1. Prediction counter**

```text
mlflowops_predictions_total
```

A Prometheus Counter tracks the total number of successful model predictions.

The metric uses the `model_version` label to associate prediction activity with the loaded model version.

**2. Prediction latency**

```text
mlflowops_prediction_latency_seconds
```

A Prometheus Histogram records the time taken to process prediction requests.

The histogram allows latency distributions and percentile-based measurements to be calculated.

**3. Model information**

```text
mlflowops_model_info
```

A Prometheus Gauge identifies the currently loaded model version.

The model version is exposed through the `model_version` label, with a value of `1` for the active version.

For example:

```text
mlflowops_model_info{model_version="8"} 1
```

This indicates that model version 8 is loaded by the serving application.

**4. Prediction error counter**

```text
mlflowops_prediction_errors_total
```

A Prometheus Counter tracks prediction failures.

The metric uses the model-version label to associate failures with the relevant model version.

### Example Prometheus queries

Prediction count:

```promql
mlflowops_predictions_total
```

Prediction request rate:

```promql
sum(rate(mlflowops_predictions_total[5m]))
```

Prediction error rate:

```promql
100 *
sum(rate(mlflowops_prediction_errors_total[5m]))
/
clamp_min(
  sum(rate(mlflowops_prediction_errors_total[5m]))
  +
  sum(rate(mlflowops_predictions_total[5m])),
  0.000001
)
```

Loaded model version:

```promql
mlflowops_model_info
```

These queries provide application-level visibility into prediction activity, prediction failures and the model version currently serving requests.

---

## 12. Grafana Monitoring and Alerting

Grafana is deployed as part of the Prometheus monitoring stack.

It connects to the Prometheus data source and provides visualisation of collected metrics.

The Grafana service is available inside the monitoring namespace:

```text
monitoring-grafana
```

### Application monitoring dashboard

The MLflowOps monitoring dashboard focuses on three application-level indicators.

**Prediction request rate**

Displays the rate of successful predictions over time.

It helps track inference activity and changes in API usage.

**Prediction error rate**

Displays the percentage of failed prediction requests relative to the total number of successful and failed prediction requests.

It provides an application-level indicator of inference reliability.

**Model version in use**

Displays the currently loaded model version.

This allows the deployed inference model to be identified without inspecting the application container directly.

### Prediction error alert

The project defines an alerting policy for prediction failures.

The alert condition is:

```text
Prediction error rate > 5%
```

The intended evaluation configuration is:

| Setting | Value |
|---|---|
| Metric | Prediction error rate |
| Threshold | Above 5% |
| Evaluation interval | 1 minute |
| Pending period | 2 minutes |
| Alert name | MLflowOps-Prediction-Error-Alert |

The alert is designed to identify sustained increases in prediction failures rather than reacting to a single isolated error.

Grafana contact-point configuration provides the notification destination for the alert.

---

## 13. Structured Application Logging

The serving API implements structured JSON logging to make application events easier to inspect and process.

Instead of relying exclusively on unstructured text messages, the application records prediction events using structured fields.

The logging implementation includes information such as:

- Event type.
- Model version.
- Prediction status.
- Prediction latency.
- Error information when a prediction fails.

An example successful prediction log entry is:

```json
{
  "event": "prediction",
  "model_version": "8",
  "status": "success",
  "latency_seconds": 0.025
}
```

A failed prediction event can include the model version and error details.

Including the model version in prediction logs is particularly useful in an MLOps environment because it makes it possible to associate application behaviour with the exact model version used for inference.

Structured logging also provides a consistent format for future integration with centralised log-management systems.

---

## 14. End-to-End Application Workflow

The complete workflow connects source-code changes, model training, model registration, deployment and monitoring.

### Development and delivery

1. Application and infrastructure code are maintained in GitHub.
2. A source-code change triggers the GitHub Actions workflow.
3. Python tests are executed.
4. The Docker image is built.
5. The image is published to Amazon ECR.

### Model lifecycle

6. When training is enabled, GitHub Actions starts the EC2 Spot training workload.
7. The training process communicates with MLflow.
8. The training run and model artifacts are recorded.
9. The model is registered in the MLflow Model Registry.
10. The evaluation and promotion stages select the model for deployment.

### Application deployment

11. GitHub Actions deploys the application to Amazon EKS.
12. The staging Deployment runs the FastAPI inference service.
13. The application loads the selected model version from MLflow.
14. The production approval stage controls the transition to production.
15. The production Deployment runs the production application separately.

### Monitoring

16. Users submit prediction requests to FastAPI.
17. The application generates predictions using the registered model.
18. The application records prediction metrics and structured logs.
19. Prometheus scrapes the `/metrics` endpoint.
20. Grafana visualises prediction activity, prediction errors and the active model version.
21. The configured alerting policy monitors the prediction error rate.

---

## 15. Repository and Configuration

The project is maintained in the GitHub repository:

```text
MuhammadUzair-1/mlflowops-project
```

The main workflow file is:

```text
.github/workflows/mlflowops-pipeline.yml
```

The application configuration uses environment variables for model selection and MLflow connectivity.

Important configuration variables include:

| Variable | Purpose |
|---|---|
| `MODEL_VERSION` | Selects the registered model version |
| `MLFLOW_MODEL_URI` | Defines the MLflow model URI |

The application uses the following default model name:

```text
task-priority-classifier
```

The project also maintains separate configuration for the AWS environment, Kubernetes deployment and monitoring resources.

---

## 16. Engineering Outcomes

The project demonstrates the integration of cloud infrastructure, software delivery automation and machine-learning lifecycle management.

The main engineering outcomes include:

**Infrastructure automation**

AWS infrastructure is provisioned using Terraform, with Kubernetes provided by Amazon EKS.

**Container-based application delivery**

The FastAPI inference service is packaged using Docker and distributed through Amazon ECR.

**Centralised model management**

MLflow provides experiment tracking, model registration and model version management, while Amazon S3 stores model artifacts.

**Automated model and application delivery**

GitHub Actions coordinates testing, image publication, training, model evaluation, promotion and Kubernetes deployment.

**Environment separation**

Staging and production application deployments are maintained separately in EKS.

**Application-level observability**

Prometheus collects custom prediction metrics, and Grafana provides visualisation and alerting capabilities.

**Structured logging**

Prediction events include model-version information, allowing application activity to be associated with the model used for inference.

---

## 17. Conclusion

MLflowOps brings together the main components required to operate a machine-learning inference application in a cloud-native environment.

The project combines Infrastructure as Code, AWS services, Docker, Kubernetes, MLflow, GitHub Actions, Prometheus and Grafana into a connected MLOps workflow.

Rather than treating model training, model deployment and application operations as separate activities, the platform integrates them into a coordinated lifecycle.

The resulting architecture supports automated model training, centralised model version management, containerised inference, controlled staging and production deployment, and application-level monitoring.

The project demonstrates practical implementation of DevOps and MLOps concepts across cloud infrastructure, CI/CD automation, Kubernetes operations, machine-learning lifecycle management and observability.
