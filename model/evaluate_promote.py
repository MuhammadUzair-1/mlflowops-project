import os
import re
import sys
from pathlib import Path
from mlflow import MlflowClient

MODEL = "task-priority-classifier"
client = MlflowClient()
uri = os.environ["MLFLOW_TRACKING_URI"]

experiment = client.get_experiment_by_name(MODEL)
if not experiment:
    sys.exit("Experiment not found")

runs = client.search_runs(
    [experiment.experiment_id],
    filter_string="attributes.status = 'FINISHED'",
    order_by=["attributes.start_time DESC"],
    max_results=1,
)
if not runs:
    sys.exit("No completed training runs found")

run = runs[0]
m = run.data.metrics

required = [
    "accuracy", "f1_macro", "precision_macro",
    "recall_macro", "baseline_f1_macro"
]
missing = [key for key in required if key not in m]
if missing:
    sys.exit(f"Missing metrics: {missing}")

report_path = client.download_artifacts(
    run.info.run_id, "evaluation/classification_report.txt"
)
matrix_path = client.download_artifacts(
    run.info.run_id, "evaluation/confusion_matrix.txt"
)

report = Path(report_path).read_text()
matrix = Path(matrix_path).read_text()

print("\nCLASSIFICATION REPORT\n")
print(report)
print("\nCONFUSION MATRIX\n")
print(matrix)

checks = {
    "Accuracy >= 0.80": m["accuracy"] >= 0.80,
    "Macro F1 >= 0.75": m["f1_macro"] >= 0.75,
    "Macro F1 beats baseline": m["f1_macro"] > m["baseline_f1_macro"],
    "Macro precision >= 0.70": m["precision_macro"] >= 0.70,
    "Macro recall >= 0.70": m["recall_macro"] >= 0.70,
}

# Check each class's F1 score from sklearn's text classification report.
class_f1 = {}
for line in report.splitlines():
    parts = line.split()
    if len(parts) >= 4 and parts[0] in {"high", "medium", "low"}:
        try:
            class_f1[parts[0]] = float(parts[3])
        except ValueError:
            pass

for label in ("high", "medium", "low"):
    checks[f"{label} class F1 >= 0.60"] = (
        label in class_f1 and class_f1[label] >= 0.60
    )

# Compare against the existing Staging model, if one exists.
staging = client.get_latest_versions(MODEL, stages=["Staging"])
previous_f1 = None

if staging and staging[0].run_id != run.info.run_id:
    previous_run = client.get_run(staging[0].run_id)
    previous_f1 = previous_run.data.metrics.get("f1_macro")
    if previous_f1 is not None:
        checks["No more than 0.02 F1 regression vs Staging"] = (
            m["f1_macro"] >= previous_f1 - 0.02
        )

lines = [
    "# MLflow Model Evaluation",
    "",
    f"Run ID: `{run.info.run_id}`",
    "",
    "## Metrics",
    "",
]
for key in required:
    lines.append(f"- {key}: **{m[key]:.4f}**")

if previous_f1 is not None:
    lines.append(f"- Previous Staging macro F1: **{previous_f1:.4f}**")

lines += ["", "## Quality gates", ""]
for name, passed in checks.items():
    lines.append(f"- {'PASS' if passed else 'FAIL'} — {name}")

lines += ["", "## Classification report", "", "```text", report, "```",
          "", "## Confusion matrix", "", "```text", matrix, "```"]

Path("evaluation-report.md").write_text("\n".join(lines))
with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
    f.write("\n".join(lines))

failed = [name for name, passed in checks.items() if not passed]
if failed:
    sys.exit("QUALITY GATE FAILED: " + "; ".join(failed))

versions = client.search_model_versions(f"name='{MODEL}'")
matching = [v for v in versions if v.run_id == run.info.run_id]
if not matching:
    sys.exit("No registered model version matches the evaluated run")

version = max(matching, key=lambda v: int(v.version))
client.transition_model_version_stage(
    name=MODEL,
    version=version.version,
    stage="Staging",
    archive_existing_versions=True,
)
print(f"SUCCESS: model version {version.version} promoted to Staging")
