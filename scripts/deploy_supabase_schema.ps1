param(
    [string]$DatabaseUrl = $env:SUPABASE_DB_URL
)

if (-not $DatabaseUrl) {
    $DatabaseUrl = Read-Host "Enter Supabase Postgres connection string (postgres://user:pass@host:port/dbname)"
}

if (-not $DatabaseUrl) {
    Write-Error "No database URL provided. Set SUPABASE_DB_URL environment variable or pass -DatabaseUrl."
    exit 1
}

# Ensure psql is available
if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    Write-Error "psql is not found in PATH. Install PostgreSQL client or add psql to PATH."
    exit 2
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Ordered list of SQL files to apply (schema-only; does not DROP or wipe user data)
$sqlFiles = @(
    "scripts/init-postgis.sql",
    "scripts/02_enable_postgis.sql",
    "scripts/0008_create_user_sessions.sql",
    "scripts/03_create_webhooks_table.sql",
    "scripts/01_create_management_dashboard_views.sql",
    "scripts/fix_trigger.sql"
)

Write-Host "Deploying schema to Supabase (schema-only). Files will be applied in order." -ForegroundColor Cyan

foreach ($rel in $sqlFiles) {
    $path = Join-Path $scriptDir $rel
    if (-not (Test-Path $path)) {
        Write-Warning "Skipping missing file: $rel"
        continue
    }

    Write-Host "Applying $rel..." -NoNewline
    try {
        & psql $DatabaseUrl --set=ON_ERROR_STOP=on -f $path
        if ($LASTEXITCODE -ne 0) { throw "psql exited with code $LASTEXITCODE" }
        Write-Host " DONE" -ForegroundColor Green
    }
    catch {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Error "Error applying $rel: $_"
        exit 10
    }
}

Write-Host "Schema deployment finished successfully." -ForegroundColor Green
Write-Host "Note: This script applies schema DDL only and does not migrate or delete existing data." -ForegroundColor Yellow
