# Wikipedia Pageviews Pipeline

A daily data pipeline that pulls the top Wikipedia articles by pageviews, loads them into Snowflake, and transforms them into analytics tables using dbt. Infrastructure is managed with Terraform and the whole thing runs automatically via GitHub Actions.

---

## What it does

Every day at 5am UTC the pipeline:
1. Fetches the previous day's top 1000 Wikipedia articles from the Wikimedia REST API
2. Loads the raw data into Snowflake
3. Runs dbt to build clean, analytics-ready tables
4. Runs dbt tests to validate the data

No manual steps needed once it's running.

---

## Stack

| Layer | Tool |
|---|---|
| Ingestion | Python + Wikimedia REST API |
| Storage | Snowflake |
| Transformation | dbt |
| Infrastructure | Terraform |
| Orchestration | GitHub Actions |

---

## Project structure

```
wiki-snowflake-pipeline/
├── ingestion/
│   └── ingest.py           # fetches and loads daily pageview data
├── wikipedia_dbt/
│   ├── models/
│   │   ├── staging/        # cleans raw data
│   │   └── marts/          # top articles, monthly rollups, trend analysis
│   └── dbt_project.yml
├── terraform/
│   ├── main.tf             # Snowflake database, warehouse, schemas, grants
│   └── variables.tf
└── .github/workflows/
    └── daily_pipeline.yml  # scheduled GitHub Actions workflow
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

---

## Infrastructure setup

Terraform provisions the Snowflake database, schemas, warehouse, and role grants:

```bash
cd terraform
terraform init
terraform apply
```

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