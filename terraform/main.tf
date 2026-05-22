terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.87"
    }
  }
}

locals {
  snowflake_account_parts = split("-", var.snowflake_account)
}

# ✅ new
provider "snowflake" {
  organization_name = local.snowflake_account_parts[0]
  account_name      = local.snowflake_account_parts[1]
  user              = var.snowflake_user
  password          = var.snowflake_password
  role              = "ACCOUNTADMIN"
}

# ── Database ───────────────────────────────────
resource "snowflake_database" "wikipedia" {
  name    = "WIKIPEDIA"
  comment = "Wikipedia pageviews pipeline"
}

# ── Schemas ────────────────────────────────────
resource "snowflake_schema" "raw" {
  database = snowflake_database.wikipedia.name
  name     = "RAW"
  comment  = "Raw ingested data from Python pipeline"
}

resource "snowflake_schema" "staging" {
  database = snowflake_database.wikipedia.name
  name     = "STAGING"
  comment  = "dbt staging models"
}

resource "snowflake_schema" "analytics" {
  database = snowflake_database.wikipedia.name
  name     = "ANALYTICS"
  comment  = "dbt transformed models"
}

# ── Warehouse ──────────────────────────────────
resource "snowflake_warehouse" "wiki_wh" {
  name           = "WIKI_WH"
  warehouse_size = "X-SMALL"
  auto_suspend   = 60 # suspend after 60s idle (saves credits)
  auto_resume    = true
  comment        = "Warehouse for wiki pipeline + dbt"
}

# ── Raw table ──────────────────────────────────
resource "snowflake_table" "wiki_pageviews" {
  database = snowflake_database.wikipedia.name
  schema   = snowflake_schema.raw.name
  name     = "WIKI_PAGEVIEWS"

  column {
    name     = "PAGE_DATE"
    type     = "DATE"
    nullable = false
  }
  column {
    name     = "ARTICLE"
    type     = "VARCHAR"
    nullable = false
  }
  column {
    name     = "VIEWS"
    type     = "NUMBER"
    nullable = false
  }
  column {
    name     = "RANK"
    type     = "NUMBER"
    nullable = false
  }
}

# ── Grants ─────────────────────────────────────
resource "snowflake_grant_privileges_to_account_role" "sysadmin_db" {
  account_role_name = "SYSADMIN"
  privileges        = ["CREATE SCHEMA", "USAGE", "MODIFY"]

  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.wikipedia.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "sysadmin_wh" {
  account_role_name = "SYSADMIN"
  privileges        = ["USAGE", "OPERATE"]

  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.wiki_wh.name
  }
}