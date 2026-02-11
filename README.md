# Seacom-App

An application to allow technicians to submit their reports and noc oporators to assign tasks to technicians.

## 1. Installation / Setup

1. Clone the repository into a folder

    ```bash
    git clone https://github.com/Caff-Core/seacom-app-backend.git
    ```

2. Install uv if you don't have it in your system [UV installation](https://docs.astral.sh/uv/getting-started/installation/)

3. Move into the project folder and run the following command:

    ```bash
    uv pip install -r pyproject.toml
    ```

## 2. Database setup

1. Install Postgresql 18 in your system [Postgresql Download](https://docs.astral.sh/uv/getting-started/installation/)

2. Install pgAdmin4 in your system [PgAdmin Download](https://www.pgadmin.org/download/)

3. After setting up your user password add the following file inside the project folder: `.env`

4. Inside the `.env` file add the following:

    ```bash
    # Database
    DB_HOST="localhost"
    DB_USER="postgres"
    DB_PASSWORD="use the password you set here"
    DB_PORT="5432"
    DB_NAME="seacom_app_db"

    # Security
    JWT_TOKEN_EXPIRE_MINUTES=30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
    JWT_SECRET_KEY=""
    JWT_ALGORITH="HS256"
    ```

## 3. Run the application

```bash
uv run uvicorn app.main:app --reload
```

## 4. Report Stability Migration (Task/Report Reliability)

Apply these SQL scripts in order on staging, then production:

1. `scripts/fix_trigger.sql`
2. `scripts/0011_enforce_single_active_report_per_task.sql`

Purpose:
- `fix_trigger.sql` removes/fixes broken `audit_report_changes` trigger paths that can block report updates.
- `0011_enforce_single_active_report_per_task.sql` deduplicates active reports and enforces one active report per task.

Verification queries:

```sql
-- Check trigger status on reports table
SELECT tgname
FROM pg_trigger
WHERE tgrelid = 'reports'::regclass
  AND NOT tgisinternal;

-- Check unique partial index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'reports'
  AND indexname = 'ux_reports_task_id_active';
```
