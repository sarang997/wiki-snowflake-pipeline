## Publishing Checklist

This repo is being prepared for a public GitHub push. The sensitive pieces should stay out of source control:

- Snowflake password, user, and account identifier should be supplied through GitHub Secrets or local environment variables.
- Terraform variables should live in a local-only `terraform.tfvars` file, based on `terraform/terraform.tfvars.example`.
- dbt should read credentials from `~/.dbt/profiles.yml` locally or from the GitHub Actions workflow at runtime.
- Generated files like `terraform.tfstate`, `*.log`, `dbt_packages/`, `target/`, and the local virtual environment should remain ignored.

## Required GitHub Secrets

Set these in the repository before enabling the workflow:

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_ROLE`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`

## Daily Workflow

The GitHub Actions workflow runs on a daily schedule and also supports manual dispatch. It:

1. Installs the Python dependencies.
2. Creates a dbt profile from GitHub Secrets.
3. Runs the ingestion script for yesterday's data.
4. Runs `dbt run` and `dbt test`.

## Local Setup

Use `.env.example` for the ingestion script and `terraform/terraform.tfvars.example` for Terraform values. Do not commit the filled-in files.
