# Management Dashboard - Implementation Guide

## Overview

This guide provides comprehensive instructions for implementing the Seacom management dashboard with SLA monitoring, compliance tracking, and operational intelligence.

---

## Architecture

### Backend Stack
- **Database**: PostgreSQL with read-only views
- **API Framework**: FastAPI
- **Language**: Python 3.11+
- **Timezone**: UTC (timezone-aware)

### Frontend Stack
- **Framework**: React 18+ with TypeScript
- **State Management**: TanStack Query (React Query)
- **UI Components**: Shadcn/ui
- **Charts**: Recharts or Chart.js
- **Styling**: Tailwind CSS

---

## Database Setup

### 1. Execute SQL Views

Run the migration file to create all database views:

```bash
# Navigate to backend directory
cd seacom-app-backend

# Execute SQL script
psql -U postgres -d seacom_db -f scripts/01_create_management_dashboard_views.sql
```

### 2. Verify Views Creation

```sql
-- Check all views created
SELECT schemaname, viewname 
FROM pg_views 
WHERE viewname LIKE 'v_%' 
ORDER BY viewname;
```

### 3. Test View Queries

```sql
-- Test executive overview
SELECT * FROM v_executive_sla_overview;

-- Test incident monitoring
SELECT * FROM v_incident_sla_monitoring LIMIT 10;

-- Test alerts
SELECT * FROM v_sla_alerts_escalation LIMIT 5;
```

---

## Backend API Implementation

### 1. Create Dashboard Endpoints

Create new file: `app/api/v1/dashboard.py`

```python
from fastapi import APIRouter, Query, Depends
from typing import List
from sqlalchemy import text

from app.database import Session
from app.models import IncidentResponse, TaskResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# ========== Executive SLA Overview ==========
@router.get("/executive-sla-overview", status_code=200)
def get_executive_sla_overview(session: Session):
    """Get high-level SLA compliance metrics"""
    result = session.execute(
        text("SELECT * FROM v_executive_sla_overview")
    ).fetchone()
    return {
        "total_items": result.total_items,
        "within_sla_count": result.within_sla_count,
        "at_risk_count": result.at_risk_count,
        "critical_count": result.critical_count,
        "breached_count": result.breached_count,
        "compliance_percentage": float(result.compliance_percentage),
        "at_risk_percentage": float(result.at_risk_percentage),
        "last_updated": result.last_updated,
    }

# ========== Incident SLA Monitoring ==========
@router.get("/incident-sla-monitoring", status_code=200)
def get_incident_sla_monitoring(
    session: Session,
    severity: str | None = Query(None),
    region: str | None = Query(None),
    sla_status: str | None = Query(None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Get incident SLA details with filters"""
    query = "SELECT * FROM v_incident_sla_monitoring WHERE 1=1"
    params = {}
    
    if severity:
        query += " AND severity = :severity"
        params["severity"] = severity
    if region:
        query += " AND region = :region"
        params["region"] = region
    if sla_status:
        query += " AND sla_status = :sla_status"
        params["sla_status"] = sla_status
    
    query += f" ORDER BY sla_deadline ASC LIMIT {limit} OFFSET {offset}"
    
    total = session.execute(text(f"SELECT COUNT(*) FROM v_incident_sla_monitoring")).scalar()
    results = session.execute(text(query), params).fetchall()
    
    return {"data": results, "total": total}

# ========== Task Performance ==========
@router.get("/task-performance", status_code=200)
def get_task_performance(
    session: Session,
    task_type: str | None = Query(None),
    region: str | None = Query(None),
    sla_status: str | None = Query(None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Get task performance metrics"""
    query = "SELECT * FROM v_task_performance_compliance WHERE 1=1"
    params = {}
    
    if task_type:
        query += " AND task_type = :task_type"
        params["task_type"] = task_type
    if region:
        query += " AND region = :region"
        params["region"] = region
    if sla_status:
        query += " AND sla_status = :sla_status"
        params["sla_status"] = sla_status
    
    query += f" ORDER BY sla_deadline ASC LIMIT {limit} OFFSET {offset}"
    
    total = session.execute(text(f"SELECT COUNT(*) FROM v_task_performance_compliance")).scalar()
    results = session.execute(text(query), params).fetchall()
    
    return {"data": results, "total": total}

# ========== Site Risk & Reliability ==========
@router.get("/site-risk-reliability", status_code=200)
def get_site_risk_reliability(
    session: Session,
    region: str | None = Query(None),
    risk_level: str | None = Query(None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Get site-level risk assessment"""
    query = "SELECT * FROM v_site_risk_reliability WHERE 1=1"
    params = {}
    
    if region:
        query += " AND region = :region"
        params["region"] = region
    if risk_level:
        query += " AND risk_level = :risk_level"
        params["risk_level"] = risk_level
    
    query += f" ORDER BY incident_count DESC LIMIT {limit} OFFSET {offset}"
    
    total = session.execute(text(f"SELECT COUNT(*) FROM v_site_risk_reliability")).scalar()
    results = session.execute(text(query), params).fetchall()
    
    return {"data": results, "total": total}

# ========== Technician Performance ==========
@router.get("/technician-performance", status_code=200)
def get_technician_performance(
    session: Session,
    workload_level: str | None = Query(None),
    performance_level: str | None = Query(None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Get aggregated technician performance (non-punitive)"""
    query = "SELECT * FROM v_technician_performance WHERE 1=1"
    params = {}
    
    if workload_level:
        query += " AND workload_level = :workload_level"
        params["workload_level"] = workload_level
    if performance_level:
        query += " AND performance_level = :performance_level"
        params["performance_level"] = performance_level
    
    query += f" ORDER BY total_workload DESC LIMIT {limit} OFFSET {offset}"
    
    total = session.execute(text(f"SELECT COUNT(*) FROM v_technician_performance")).scalar()
    results = session.execute(text(query), params).fetchall()
    
    return {"data": results, "total": total}

# ========== Access Request SLA ==========
@router.get("/access-request-sla", status_code=200)
def get_access_request_sla(
    session: Session,
    region: str | None = Query(None),
    sla_status: str | None = Query(None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Get access request SLA impact"""
    query = "SELECT * FROM v_access_request_sla_impact WHERE 1=1"
    params = {}
    
    if region:
        query += " AND region = :region"
        params["region"] = region
    if sla_status:
        query += " AND sla_status = :sla_status"
        params["sla_status"] = sla_status
    
    query += f" ORDER BY sla_deadline ASC LIMIT {limit} OFFSET {offset}"
    
    total = session.execute(text(f"SELECT COUNT(*) FROM v_access_request_sla_impact")).scalar()
    results = session.execute(text(query), params).fetchall()
    
    return {"data": results, "total": total}

# ========== Regional Analytics ==========
@router.get("/regional-sla-analytics", status_code=200)
def get_regional_sla_analytics(session: Session):
    """Get regional performance comparison"""
    results = session.execute(
        text("SELECT * FROM v_regional_sla_analytics ORDER BY overall_sla_compliance DESC")
    ).fetchall()
    return results

# ========== SLA Trends ==========
@router.get("/sla-trend-analysis", status_code=200)
def get_sla_trend_analysis(
    session: Session,
    metric_type: str | None = Query(None),
):
    """Get historical SLA trends"""
    query = "SELECT * FROM v_sla_trend_analysis WHERE 1=1"
    params = {}
    
    if metric_type:
        query += " AND metric_type = :metric_type"
        params["metric_type"] = metric_type
    
    query += " ORDER BY metric_date DESC"
    
    results = session.execute(text(query), params).fetchall()
    return results

# ========== Alerts & Escalation ==========
@router.get("/sla-alerts", status_code=200)
def get_sla_alerts(
    session: Session,
    alert_level: str | None = Query(None),
    item_type: str | None = Query(None),
    limit: int = Query(default=10, le=100),
):
    """Get real-time SLA alerts"""
    query = "SELECT * FROM v_sla_alerts_escalation WHERE 1=1"
    params = {}
    
    if alert_level:
        query += " AND alert_level = :alert_level"
        params["alert_level"] = alert_level
    if item_type:
        query += " AND item_type = :item_type"
        params["item_type"] = item_type
    
    query += f" LIMIT {limit}"
    
    results = session.execute(text(query), params).fetchall()
    return results

# ========== Health Check ==========
@router.get("/health", status_code=200)
def dashboard_health(session: Session):
    """Health check for dashboard services"""
    try:
        session.execute(text("SELECT 1"))
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```

### 2. Update Main App Routes

Add to `app/main.py`:

```python
from app.api.v1 import dashboard

app.include_router(dashboard.router)
```

---

## Frontend Implementation

### 1. Install Required Dependencies

```bash
cd seacom-app-frontend
npm install recharts date-fns @radix-ui/react-tabs
```

### 2. Update Dashboard Overview View

Update `src/pages/dashboards/manager/views/manager-overview.tsx`:

```tsx
import { useExecutiveSLAOverview, useSLAAlerts } from "@/queries/management-dashboard";
import { generateSLASummary } from "@/lib/dashboard-helpers";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/loading-spinner";

const ManagerOverview = () => {
  const { data: overview, isLoading: overviewLoading } = useExecutiveSLAOverview();
  const { data: alerts, isLoading: alertsLoading } = useSLAAlerts({ limit: 5 });

  if (overviewLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        {/* KPI Cards */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.total_items || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Compliance Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {overview?.compliance_percentage.toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              At Risk
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {overview?.at_risk_count || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Breached
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {overview?.breached_count || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>Items requiring immediate attention</CardDescription>
        </CardHeader>
        <CardContent>
          {!alertsLoading && alerts ? (
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <p className="font-medium">{alert.severity} - {alert.location}</p>
                    <p className="text-sm text-muted-foreground">{alert.assigned_to}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    alert.alert_level === 'BREACHED' ? 'bg-red-100 text-red-800' :
                    alert.alert_level === 'CRITICAL' ? 'bg-orange-100 text-orange-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {alert.alert_level}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No critical alerts</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ManagerOverview;
```

### 3. Create Incidents Page

Update `src/pages/dashboards/manager/views/manager-incidents.tsx`:

```tsx
import { useState } from "react";
import { useIncidentSLAMonitoring } from "@/queries/management-dashboard";
import {
  getSLAStatusColor,
  getSLAStatusBadgeLabel,
  formatMinutesDetailed,
  formatDateTime,
  regionDisplayName,
} from "@/lib/dashboard-helpers";
import { DataTable } from "@/components/data-grids/data-table";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const ManagerIncidents = () => {
  const [filters, setFilters] = useState({
    severity: undefined,
    region: undefined,
    sla_status: undefined,
  });

  const { data, isLoading } = useIncidentSLAMonitoring(filters);

  const columns = [
    {
      header: "Reference",
      accessor: "seacom_ref",
    },
    {
      header: "Description",
      accessor: "description",
      cell: (value: string) => value.substring(0, 50) + "...",
    },
    {
      header: "Severity",
      accessor: "severity",
    },
    {
      header: "Site",
      accessor: "site_name",
    },
    {
      header: "Region",
      accessor: "region",
      cell: (value: string) => regionDisplayName(value),
    },
    {
      header: "SLA Deadline",
      accessor: "sla_deadline",
      cell: (value: string) => formatDateTime(value),
    },
    {
      header: "Remaining",
      accessor: "sla_remaining_minutes",
      cell: (value: number) => formatMinutesDetailed(value),
    },
    {
      header: "Status",
      accessor: "sla_status",
      cell: (value: string) => (
        <span className={`px-2 py-1 rounded text-xs font-semibold ${getSLAStatusColor(value)}`}>
          {getSLAStatusBadgeLabel(value as any)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Select value={filters.severity || ""} onValueChange={(v) => setFilters({ ...filters, severity: v || undefined })}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All</SelectItem>
            <SelectItem value="CRITICAL">Critical</SelectItem>
            <SelectItem value="MAJOR">Major</SelectItem>
            <SelectItem value="MINOR">Minor</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.region || ""} onValueChange={(v) => setFilters({ ...filters, region: v || undefined })}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Region" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Regions</SelectItem>
            <SelectItem value="gauteng">Gauteng</SelectItem>
            <SelectItem value="mpumalanga">Mpumalanga</SelectItem>
            <SelectItem value="kwazulu-natal">KZN</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.sla_status || ""} onValueChange={(v) => setFilters({ ...filters, sla_status: v || undefined })}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="SLA Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All</SelectItem>
            <SelectItem value="WITHIN_SLA">Within SLA</SelectItem>
            <SelectItem value="AT_RISK">At Risk</SelectItem>
            <SelectItem value="CRITICAL">Critical</SelectItem>
            <SelectItem value="BREACHED">Breached</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.data || []}
        isLoading={isLoading}
        pagination={{
          total: data?.total || 0,
          pageSize: 20,
        }}
      />
    </div>
  );
};

export default ManagerIncidents;
```

---

## Performance Optimization

### Database Optimization
1. Views use efficient aggregations and window functions
2. Created indexes on frequently filtered columns
3. Materialized views option for real-time dashboards (future)

### Frontend Optimization
1. Query caching with stale time settings
2. Pagination support for large datasets
3. Lazy loading of detail views
4. Real-time updates only for critical alerts

### Refresh Intervals
- **Executive Overview**: 5 minutes
- **Incident/Task SLA**: 1 minute (real-time)
- **Site Risk**: 15 minutes
- **Regional Analytics**: 30 minutes
- **Technician Performance**: Daily
- **Alerts**: Every 1 minute

---

## Monitoring & Alerts

### Email Alerting

```python
# app/services/alert_service.py
from fastapi_mail import FastMail, MessageSchema
from app.core.settings import app_settings

async def send_sla_alert(alert: SLAAlert):
    """Send email alert for SLA breach"""
    message = MessageSchema(
        subject=f"⚠️ SLA Alert: {alert.severity}",
        recipients=[alert.assigned_to_email],
        body=f"""
        {alert.item_type} - {alert.severity}
        Location: {alert.location}
        SLA Deadline: {alert.sla_deadline}
        Status: {alert.alert_level}
        """,
        subtype="html"
    )
    fm = FastMail(app_settings.email_config)
    await fm.send_message(message)
```

### Slack Notifications

```python
# app/services/slack_service.py
from slack_sdk import WebClient

async def send_slack_alert(alert: SLAAlert):
    """Send Slack notification"""
    client = WebClient(token=app_settings.slack_token)
    color = {
        'BREACHED': 'danger',
        'CRITICAL': 'warning',
        'AT_RISK': 'warning'
    }[alert.alert_level]
    
    client.chat_postMessage(
        channel="#operations-alerts",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{alert.alert_level}*: {alert.severity} at {alert.location}"
                }
            }
        ]
    )
```

---

## Testing

### Backend Tests

```python
# tests/test_dashboard.py
def test_executive_sla_overview(client: TestClient):
    response = client.get("/api/v1/dashboard/executive-sla-overview")
    assert response.status_code == 200
    data = response.json()
    assert "compliance_percentage" in data
    assert 0 <= data["compliance_percentage"] <= 100

def test_incident_sla_filtering(client: TestClient):
    response = client.get(
        "/api/v1/dashboard/incident-sla-monitoring?severity=CRITICAL&region=gauteng"
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["severity"] == "CRITICAL" for item in data["data"])
```

### Frontend Tests

```typescript
// tests/queries/management-dashboard.test.ts
describe("Management Dashboard Queries", () => {
  it("should fetch executive SLA overview", async () => {
    const { result } = renderHook(() => useExecutiveSLAOverview(), {
      wrapper: QueryClientProvider,
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toHaveProperty("compliance_percentage");
  });
});
```

---

## Deployment Checklist

- [ ] Database views created and tested
- [ ] Backend endpoints implemented and tested
- [ ] Frontend components built and tested
- [ ] API documentation updated
- [ ] Alerting system configured
- [ ] Performance monitoring enabled
- [ ] User access policies configured
- [ ] Training completed

---

## Support & Troubleshooting

### Common Issues

1. **Views return no data**
   - Ensure incidents/tasks exist in database
   - Check timezone configuration (must be UTC)
   - Verify `created_at` timestamps are within 90-day window

2. **Slow dashboard loads**
   - Enable view materialization for high-traffic views
   - Check database indexes are created
   - Monitor query execution times with `EXPLAIN ANALYZE`

3. **Incorrect SLA calculations**
   - Verify SLA minutes match business rules in views
   - Check incident/task severity classification logic
   - Confirm timestamps are properly timezone-aware

---

## Next Steps

1. Deploy database views to production
2. Implement backend endpoints
3. Build frontend dashboard components
4. Set up alerting integration
5. Configure user access and permissions
6. Monitor performance and optimize as needed

