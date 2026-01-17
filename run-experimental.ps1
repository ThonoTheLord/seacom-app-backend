# Seacom Backend - Experimental Mode Launcher
# This script runs the backend against the LOCAL experimental database
# NOT the production Supabase database

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EXPERIMENTAL MODE - LOCAL DATABASE   " -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database: seacom_experimental_db" -ForegroundColor Green
Write-Host "Host:     localhost:5432" -ForegroundColor Green
Write-Host "PostGIS:  Enabled" -ForegroundColor Green
Write-Host ""

# Override environment variables for experimental database
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "seacom_experimental_db"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "admin123"

# Run the application
uv run uvicorn app.main:app --reload --port 8000
