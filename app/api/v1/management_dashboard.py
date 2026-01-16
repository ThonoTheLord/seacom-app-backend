"""
Management Dashboard API Endpoints
Provides access to SLA monitoring views and real-time metrics
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Database
from app.services.auth import CurrentUser
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["management-dashboard"])


# ============================================================
# Executive SLA Overview
# ============================================================
@router.get("/executive-sla-overview")
def get_executive_sla_overview(
    current_user: CurrentUser
) -> dict:
    """Get executive SLA overview metrics - high-level KPIs for C-suite"""
    try:
        with Database.session() as session:
            result = session.execute(
                text("SELECT * FROM v_executive_sla_overview LIMIT 1")
            )
            row = result.fetchone()
            if not row:
                return {
                    "total_items": 0,
                    "within_sla_count": 0,
                    "at_risk_count": 0,
                    "critical_count": 0,
                    "breached_count": 0,
                    "compliance_percentage": 0,
                    "at_risk_percentage": 0,
                    "last_updated": None
                }
            return row._mapping
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Incident SLA Monitoring
# ============================================================
@router.get("/incident-sla-monitoring")
def get_incident_sla_monitoring(
    current_user: CurrentUser,
    severity: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
) -> dict:
    """Get incident SLA monitoring records with filtering support"""
    try:
        with Database.session() as session:
            query = "SELECT * FROM v_incident_sla_monitoring WHERE 1=1"
            params = {}

            if severity:
                query += " AND severity = :severity"
                params["severity"] = severity

            if region:
                query += " AND region = :region"
                params["region"] = region

            if status:
                query += " AND sla_status = :status"
                params["status"] = status

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
            count_result = session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Get paginated results
            query += f" ORDER BY sla_deadline ASC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]

            return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incident-sla-monitoring/{incident_id}")
def get_incident_sla_detail(
    incident_id: str,
    current_user: CurrentUser
) -> dict:
    """Get detailed incident SLA record"""
    try:
        with Database.session() as session:
            result = session.execute(
                text("SELECT * FROM v_incident_sla_monitoring WHERE id = :id"),
                {"id": incident_id}
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Incident not found")
            return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Task Performance & Compliance
# ============================================================
@router.get("/task-performance")
def get_task_performance(
    current_user: CurrentUser,
    task_type: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
) -> dict:
    """Get task performance and compliance records"""
    try:
        with Database.session() as session:
            query = "SELECT * FROM v_task_performance_compliance WHERE 1=1"
            params = {}

            if task_type:
                query += " AND task_type = :task_type"
                params["task_type"] = task_type

            if region:
                query += " AND region = :region"
                params["region"] = region

            if status:
                query += " AND sla_status = :status"
                params["status"] = status

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
            count_result = session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Get paginated results
            query += f" ORDER BY sla_deadline ASC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]

            return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-performance/{task_id}")
def get_task_performance_detail(
    task_id: str,
    current_user: CurrentUser
) -> dict:
    """Get detailed task performance record"""
    try:
        with Database.session() as session:
            result = session.execute(
                text("SELECT * FROM v_task_performance_compliance WHERE id = :id"),
                {"id": task_id}
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Task not found")
            return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Site Risk & Reliability
# ============================================================
@router.get("/site-risk-reliability")
def get_site_risk_reliability(
    current_user: CurrentUser,
    region: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
) -> dict:
    """Get site risk and reliability metrics"""
    try:
        with Database.session() as session:
            query = "SELECT * FROM v_site_risk_reliability WHERE 1=1"
            params = {}

            if region:
                query += " AND region = :region"
                params["region"] = region

            if risk_level:
                query += " AND risk_level = :risk_level"
                params["risk_level"] = risk_level

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
            count_result = session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Get paginated results
            query += f" ORDER BY incident_count DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]

            return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/site-risk-reliability/{site_id}")
def get_site_risk_detail(
    site_id: str,
    current_user: CurrentUser
) -> dict:
    """Get detailed site risk and reliability record"""
    try:
        with Database.session() as session:
            result = session.execute(
                text("SELECT * FROM v_site_risk_reliability WHERE site_id = :id"),
                {"id": site_id}
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Site not found")
            return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Technician Performance
# ============================================================
@router.get("/technician-performance")
def get_technician_performance(
    current_user: CurrentUser,
    workload_level: Optional[str] = Query(None),
    performance_level: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
) -> dict:
    """Get technician performance metrics (aggregate, non-punitive)"""
    try:
        with Database.session() as session:
            query = "SELECT * FROM v_technician_performance WHERE 1=1"
            params = {}

            if workload_level:
                query += " AND workload_level = :workload_level"
                params["workload_level"] = workload_level

            if performance_level:
                query += " AND performance_level = :performance_level"
                params["performance_level"] = performance_level

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
            count_result = session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Get paginated results
            query += f" ORDER BY total_workload DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]

            return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technician-performance/{technician_id}")
def get_technician_performance_detail(
    technician_id: str,
    current_user: CurrentUser
) -> dict:
    """Get detailed technician performance record"""
    try:
        with Database.session() as session:
            result = session.execute(
                text("SELECT * FROM v_technician_performance WHERE technician_id = :id"),
                {"id": technician_id}
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Technician not found")
            return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Access Request SLA Impact
# ============================================================
@router.get("/access-request-sla")
def get_access_request_sla(
    current_user: CurrentUser,
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
) -> dict:
    """Get access request SLA impact records"""
    try:
        with Database.session() as session:
            query = "SELECT * FROM v_access_request_sla_impact WHERE 1=1"
            params = {}

            if region:
                query += " AND region = :region"
                params["region"] = region

            if status:
                query += " AND sla_status = :status"
                params["status"] = status

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
            count_result = session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Get paginated results
            query += f" ORDER BY sla_deadline ASC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]

            return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Regional SLA Analytics
# ============================================================
@router.get("/regional-sla-analytics")
def get_regional_sla_analytics(
    current_user: CurrentUser
) -> dict:
    """Get regional SLA analytics and performance comparison"""
    try:
        with Database.session() as session:
            result = session.execute(
                text("SELECT * FROM v_regional_sla_analytics ORDER BY overall_sla_compliance DESC")
            )
            records = [dict(row._mapping) for row in result]
            return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SLA Trend Analysis
# ============================================================
@router.get("/sla-trend-analysis")
def get_sla_trend_analysis(
    current_user: CurrentUser,
    metric_type: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(90, ge=1, le=500)
) -> dict:
    """Get historical SLA trend data (90-day window)"""
    try:
        with Database.session() as session:
            query = "SELECT * FROM v_sla_trend_analysis WHERE 1=1"
            params = {}

            if metric_type:
                query += " AND metric_type = :metric_type"
                params["metric_type"] = metric_type

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
            count_result = session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Get paginated results - ordered by date DESC (most recent first)
            query += f" ORDER BY metric_date DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]

            return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SLA Alerts & Escalation
# ============================================================
@router.get("/sla-alerts")
def get_sla_alerts(
    current_user: CurrentUser,
    alert_level: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
) -> dict:
    """Get real-time SLA alerts and escalation items"""
    try:
        with Database.session() as session:
            query = "SELECT * FROM v_sla_alerts_escalation WHERE 1=1"
            params = {}

            if alert_level:
                query += " AND alert_level = :alert_level"
                params["alert_level"] = alert_level

            if item_type:
                query += " AND item_type = :item_type"
                params["item_type"] = item_type

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
            count_result = session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Get paginated results - ordered by priority
            query += f" ORDER BY priority_order ASC, sla_deadline ASC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]

            return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Health Check
# ============================================================
@router.get("/health")
def dashboard_health(
    current_user: CurrentUser
) -> dict:
    """Check if dashboard views are healthy and responsive"""
    try:
        with Database.session() as session:
            # Try to query a simple view
            result = session.execute(
                text("SELECT 1 as status")
            )
            result.scalar()
        return {
            "status": "healthy",
            "timestamp": Database.get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Dashboard health check failed: {str(e)}"
        )
