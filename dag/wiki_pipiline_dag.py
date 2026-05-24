from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from pipeline.fetch import fetch_data
from pipeline.transform import transform
from pipeline.load import load


# defining tasks
def fetch_task(**context):
    ds = context["ds"]
    year, month, day = map(int, ds.split("-"))
    data = fetch_data(year, month, day)
    if data is None:
        raise ValueError("No data returned")
    return data

def transform_task(**context):
    ds = context["ds"]
    year, month, day = map(int, ds.split("-"))
    data = context["ti"].xcom_pull(task_ids="fetch")
    rows = transform(data, year, month, day)
    return rows

def load_task(**context):
    rows = context["ti"].xcom_pull(task_ids="transform")
    if not rows:
        raise ValueError("No rows to load")
    return load(rows)


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}


with DAG(
    dag_id="wiki_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
) as dag:

    task_fetch = PythonOperator(
        task_id="fetch",
        python_callable=fetch_task,
    )

    task_transform = PythonOperator(
        task_id="transform",
        python_callable=transform_task,
    )

    task_load = PythonOperator(
        task_id="load",
        python_callable=load_task,
    )

    task_fetch >> task_transform >> task_load