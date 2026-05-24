# Wikipedia Pageviews Pipeline

A daily data pipeline that pulls the top Wikipedia articles by pageviews, loads them into Snowflake, and transforms them into analytics tables using dbt. Infrastructure is managed with Terraform. The repo now also includes an Airflow DAG version of the pipeline for orchestration practice, alongside a GitHub Actions scheduled job for the Python/dbt flow.

---

## What it does

Every day at 5am UTC the pipeline:
1. Fetches the previous day's top 1000 Wikipedia articles from the Wikimedia REST API
2. Loads the raw data into Snowflake
3. Runs dbt to build clean, analytics-ready tables
4. Runs dbt tests to validate the data

No manual steps needed once it's running.

There are now two orchestration paths in the repo:

1. GitHub Actions runs the ingestion script and dbt on a schedule.
2. Airflow runs the same logical pipeline as a DAG with `fetch -> transform -> load` tasks.

---

## Stack

| Layer | Tool |
|---|---|
| Ingestion | Python + Wikimedia REST API |
| Storage | Snowflake |
| Transformation | dbt |
| Infrastructure | Terraform |
| Orchestration | GitHub Actions + Airflow |

---

## Project structure

```
wiki-snowflake-pipeline/
├── dag/
│   └── wiki_pipiline_dag.py # Airflow DAG for fetch/transform/load orchestration
├── ingestion/
│   └── ingest.py           # fetches and loads daily pageview data
├── pipeline/
│   ├── config.py           # shared constants
│   ├── fetch.py           # fetch step used by Airflow/local runner
│   ├── transform.py       # transform step used by Airflow/local runner
│   └── load.py            # Snowflake load helpers
├── scripts/
│   └── run_local.py       # local fetch + transform runner
├── wikipedia_dbt/
│   ├── models/
│   │   ├── staging/        # cleans raw data
│   │   └── marts/          # top articles, monthly rollups, trend analysis
│   └── dbt_project.yml
├── terraform/
│   ├── main.tf             # Snowflake database, warehouse, schemas, grants
│   └── variables.tf
└── .github/workflows/
    └── pipeline.yml        # scheduled GitHub Actions workflow
```

---

## dbt models

- `stg_wiki_pageviews` — cleans raw data, filters noise like Special:Search
- `top_articles_daily` — top 10 articles per day with % share of views
- `top_articles_monthly` — aggregated monthly rankings
- `article_trends` — tracks rank movement day over day (rising / falling / stable)

---

## Running locally

Copy `.env.example` to `.env` and fill in your Snowflake credentials:

```bash
cp .env.example .env
```

Install dependencies and run ingestion:

```bash
pip install -r requirements.txt
python ingestion/ingest.py
```

Run dbt:

```bash
cd wikipedia_dbt
dbt run
dbt test
```

Run the lightweight local runner that exercises fetch + transform without Airflow:

```bash
PYTHONPATH="$(pwd)" python3 scripts/run_local.py 2023-01-01
```

Add `--load` if you want it to write to Snowflake as well:

```bash
PYTHONPATH="$(pwd)" python3 scripts/run_local.py 2023-01-01 --load
```

If you want to run the Airflow DAG locally, install Airflow separately and point `PYTHONPATH` at the repo root so the `pipeline` package imports resolve. The DAG expects a Snowflake Connection in Airflow or equivalent Snowflake environment variables.

---

## Infrastructure setup

Terraform provisions the Snowflake database, schemas, warehouse, and role grants:

```bash
cd terraform
terraform init
terraform apply
```

## Airflow setup

The Airflow DAG lives in `dag/wiki_pipiline_dag.py` and runs three tasks in order: `fetch`, `transform`, `load`.

To run it locally or in a dev Airflow instance:

1. Make sure the repo root is on `PYTHONPATH` so Airflow can import `pipeline.*`.
2. Install Airflow and the Snowflake provider in the same environment.
3. Create a Snowflake Connection in Airflow named `snowflake_default`.
4. Set Snowflake credentials either in that Airflow Connection or in local environment variables for non-Airflow runs.

Example Airflow Connection fields:

- Conn Id: `snowflake_default`
- Conn Type: `Snowflake`
- Login: your Snowflake username
- Password: your Snowflake password
- Extra: `{ "account": "ORG-ACCOUNT", "warehouse": "WIKI_WH", "database": "WIKIPEDIA", "role": "SYSADMIN" }`

To trigger the DAG from the Airflow UI, enable the DAG and click "Trigger DAG". The schedule is daily and catchup is disabled.

---

## GitHub Actions secrets required

```
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PASSWORD
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
```