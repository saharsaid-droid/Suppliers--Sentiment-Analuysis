import os
import json
import yaml
import traceback
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.exceptions import AirflowFailException
from airflow.utils.email import send_email_smtp
import sys
import pandas as pd

sys.path.append("/opt/airflow/project")
sys.path.append("/opt/airflow/project/scripts")

from scripts.logging_confg import setup_logger

logger = setup_logger("sentiment_review_pipeline_dag")
from scripts.extract_data import extract_batch as extract_data_func
from scripts.transform_data import preprocess_text_batch
from scripts.model_utilies import predict_sentiment_batch
from scripts.load_data import load_batch_to_db
from scripts.alert_system import (
    load_district_negative_alerts,
    send_district_alert_emails,
)

# ------------------- Config -------------------
CONFIG_PATH = "/opt/airflow/project/config/setting.yaml"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ------------------- Email Callbacks -------------------
def notify_failure(context):
    task = context.get("task_instance")
    dag_id = context.get("dag").dag_id
    subject = f"[Airflow] Task Failed: {task.task_id}"
    body = f"""
    Task {task.task_id} failed.
    DAG: {dag_id}
    Execution Time: {context.get('execution_date')}
    """
    config = load_config().get("email_settings", {})
    send_email_smtp(to=config.get("email_to", []), subject=subject, html_content=body)


def notify_success(context):
    task = context.get("task_instance")
    dag_id = context.get("dag").dag_id
    subject = f"[Airflow] Task Succeeded: {task.task_id}"
    body = f"""
    Task {task.task_id} succeeded.
    DAG: {dag_id}
    Execution Time: {context.get('execution_date')}
    """
    config = load_config().get("email_settings", {})
    send_email_smtp(to=config.get("email_to", []), subject=subject, html_content=body)


# ------------------- DAG -------------------
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email_on_retry": False,
    "email_on_success": False,
}

dag = DAG(
    dag_id="sentiment_reviews_etl_batches",
    description="ETL for sentiment reviews with batch sentiment prediction and alerting",
    start_date=datetime(2024, 6, 1),
    schedule_interval="*/30 * * * *",
    catchup=False,
    default_args=default_args,
)


# ------------------- Tasks -------------------
def extract_task(**kwargs):
    ti = kwargs["ti"]
    config = load_config()
    file_name = "reviews_data.csv"
    batch_number = config["batch"].get("batch_number", 1)
    batch_size = config["batch"]["batch_size"]
    output_dir = config["paths"]["temp_batches_dir"]

    df_batch_path = extract_data_func(
        file_name,
        batch_number=batch_number,
        batch_size=batch_size,
        output_dir=output_dir,
    )
    if not os.path.exists(df_batch_path):
        raise AirflowFailException(f"Extracted batch file not found: {df_batch_path}")
    df = pd.read_csv(df_batch_path)
    if df.empty:
        raise AirflowFailException("Extracted DataFrame is empty.")
    ti.xcom_push(key="extracted_df", value=df.to_json(orient="records"))
    ti.xcom_push(key="batch_number", value=batch_number)


def transform_task(**kwargs):
    ti = kwargs["ti"]
    df_json = ti.xcom_pull(task_ids="extract_data_task", key="extracted_df")
    if not df_json:
        raise AirflowFailException("No data to transform.")
    df = pd.read_json(df_json, orient="records")

    batch_number = ti.xcom_pull(task_ids="extract_data_task", key="batch_number")
    config = load_config()
    output_dir = config["paths"]["clean_batches_dir"]

    df_cleaned_path = preprocess_text_batch(
        df, col_name="review", batch_number=batch_number, output_dir=output_dir
    )
    df_cleaned = pd.read_csv(df_cleaned_path)
    ti.xcom_push(key="cleaned_df", value=df_cleaned.to_json(orient="records"))
    ti.xcom_push(key="batch_number", value=batch_number)


def predict_batch_task(**kwargs):
    ti = kwargs["ti"]
    df_json = ti.xcom_pull(task_ids="transform_data_task", key="cleaned_df")
    if not df_json:
        print("No cleaned data available for prediction.")
        return
    df = pd.read_json(df_json, orient="records")

    batch_number = ti.xcom_pull(task_ids="transform_data_task", key="batch_number")
    config = load_config()
    model_dir = config["paths"]["model_dir"]
    tokenizer_dir = config["paths"]["tokenizer_dir"]
    output_dir = config["paths"]["predict_batches_dir"]

    # تأكد من وجود الصلاحية
    os.makedirs(output_dir, exist_ok=True)

    # مرر المسار للـ utility
    predict_sentiment_batch(
        df,
        model_dir=model_dir,
        tokenizer_dir=tokenizer_dir,
        batch_number=batch_number,
        output_dir=output_dir,
    )

    predict_path = os.path.join(output_dir, f"batch_{batch_number}.csv")
    ti.xcom_push(key="predicted_batch_path", value=predict_path)


def load_task(**kwargs):
    ti = kwargs["ti"]
    predictions_path = ti.xcom_pull(
        task_ids="predict_sentiment_batch_task", key="predicted_batch_path"
    )
    if not predictions_path or not os.path.exists(predictions_path):
        print("No batch predicted today, skipping load.")
        return
    df = pd.read_csv(predictions_path)
    config = load_config()
    db_conf = config["db"]
    threshold = config["alert_threshold"]
    load_batch_to_db(df, db_conf=db_conf, threshold=threshold)
    ti.xcom_push(key="load_status", value="success")


def load_alerts_task(**kwargs):
    ti = kwargs["ti"]
    alerts = load_district_negative_alerts(CONFIG_PATH)
    ti.xcom_push(key="alerts", value=json.dumps(alerts))


def send_alert_task(**kwargs):
    ti = kwargs["ti"]
    alerts_str = ti.xcom_pull(task_ids="load_alerts_task", key="alerts")
    if not alerts_str:
        return
    alerts = json.loads(alerts_str)
    config = load_config().get("email_settings", {})
    if alerts:
        send_district_alert_emails(alerts, config)


# ------------------- Operators -------------------
extract_op = PythonOperator(
    task_id="extract_data_task",
    python_callable=extract_task,
    dag=dag,
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
)
transform_op = PythonOperator(
    task_id="transform_data_task",
    python_callable=transform_task,
    dag=dag,
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
)
predict_op = PythonOperator(
    task_id="predict_sentiment_batch_task",
    python_callable=predict_batch_task,
    dag=dag,
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
)
load_op = PythonOperator(
    task_id="load_data_task",
    python_callable=load_task,
    dag=dag,
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
)
load_alerts_op = PythonOperator(
    task_id="load_alerts_task",
    python_callable=load_alerts_task,
    dag=dag,
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
)
send_alert_op = PythonOperator(
    task_id="send_alert_task",
    python_callable=send_alert_task,
    dag=dag,
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
)

# ------------------- DAG Flow -------------------
extract_op >> transform_op >> predict_op >> load_op >> load_alerts_op >> send_alert_op
