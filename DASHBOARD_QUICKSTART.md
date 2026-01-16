# Management Dashboard - Quick Start Guide

## 5-Minute Setup

### 1. Database Views (2 minutes)

```bash
# Connect to PostgreSQL
psql -U postgres -d seacom_db

# Execute the views script
\i scripts/01_create_management_dashboard_views.sql

# Verify views exist
\dv v_*

# Test a view
SELECT * FROM v_executive_sla_overview;
```

### 2. Backend Endpoints (2 minutes)

**Add to `app/main.py`:**
```python
from app.api.v1 import dashboard
app.include_router(dashboard.router)
```

**Test the API:**
```bash
curl http://localhost:8000/api/v1/dashboard/executive-sla-overview
```

### 3. Frontend Views (1 minute)

Views are pre-created in:
- `src/pages/dashboards/manager/` (main dashboard)
- `src/pages/dashboards/manager/views/` (individual view pages)
- Routes already configured in `App.tsx`

**Access in browser:**
```
http://localhost:5173/dashboard/manager/overview
```

---

## Implementation Checklist

### Backend
- [ ] Copy SQL script to `scripts/01_create_management_dashboard_views.sql`
- [ ] Execute SQL views on production database
- [ ] Create `app/api/v1/dashboard.py` with endpoints
- [ ] Add router to `app/main.py`
- [ ] Test endpoints with curl/Postman
- [ ] Run unit tests

### Frontend
- [ ] Verify dashboard structure exists
- [ ] Install dependencies: `npm install recharts date-fns`
- [ ] Create data service: `src/services/management-dashboard.ts`
- [ ] Create query hooks: `src/queries/management-dashboard.ts`
- [ ] Create helpers: `src/lib/dashboard-helpers.ts`
- [ ] Build individual view components
- [ ] Test with `npm run dev`

---

## Database Views Summary

| View | Purpose | Refresh | Key Field |
|------|---------|---------|-----------|
| v_executive_sla_overview | KPI summary | 5min | compliance_percentage |
| v_incident_sla_monitoring | Incident details | 1min | sla_deadline |
| v_task_performance_compliance | Task tracking | 1min | sla_status |
| v_site_risk_reliability | Site risks | 15min | risk_level |
| v_technician_performance | Team metrics | Daily | workload_level |
| v_access_request_sla_impact | Access requests | 1min | sla_status |
| v_regional_sla_analytics | Regional comparison | 30min | overall_sla_compliance |
| v_sla_trend_analysis | Historical trends | Daily | daily_compliance_percentage |
| v_sla_alerts_escalation | Real-time alerts | 1min | alert_level |

---

## API Endpoints Quick Reference

```bash
# Executive Overview
GET /api/v1/dashboard/executive-sla-overview

# Incidents (with filters)
GET /api/v1/dashboard/incident-sla-monitoring?severity=CRITICAL&region=gauteng

# Tasks
GET /api/v1/dashboard/task-performance?sla_status=AT_RISK

# Sites
GET /api/v1/dashboard/site-risk-reliability?risk_level=HIGH

# Technicians
GET /api/v1/dashboard/technician-performance?workload_level=HIGH

# Access Requests
GET /api/v1/dashboard/access-request-sla?sla_status=BREACHED

# Regional Analytics
GET /api/v1/dashboard/regional-sla-analytics

# Trends
GET /api/v1/dashboard/sla-trend-analysis?metric_type=INCIDENT

# Alerts
GET /api/v1/dashboard/sla-alerts?alert_level=BREACHED&limit=10

# Health Check
GET /api/v1/dashboard/health
```

---

## Common Tasks

### View Incident SLA for Gauteng
```bash
curl "http://localhost:8000/api/v1/dashboard/incident-sla-monitoring?region=gauteng&limit=20"
```

### Get All Critical Alerts
```bash
curl "http://localhost:8000/api/v1/dashboard/sla-alerts?alert_level=CRITICAL"
```

### Export Regional Performance
```bash
curl "http://localhost:8000/api/v1/dashboard/regional-sla-analytics" | jq .
```

### Check Technician Workload
```bash
curl "http://localhost:8000/api/v1/dashboard/technician-performance?workload_level=HIGH"
```

---

## Filtering Guide

### Available Filters

**Incident SLA Monitoring:**
- `severity`: CRITICAL, MAJOR, MINOR
- `region`: gauteng, mpumalanga, kwazulu-natal, eastern-cape, etc.
- `sla_status`: WITHIN_SLA, AT_RISK, CRITICAL, BREACHED
- `limit`, `offset`: Pagination

**Task Performance:**
- `task_type`: routine-maintenance, rhs
- `region`: (as above)
- `sla_status`: (as above)

**Site Risk:**
- `region`: (as above)
- `risk_level`: HIGH, MEDIUM, LOW

**Technician Performance:**
- `workload_level`: HIGH, MEDIUM, LOW
- `performance_level`: EXCELLENT, GOOD, NEEDS_SUPPORT, AT_RISK

**Alerts:**
- `alert_level`: BREACHED, CRITICAL, AT_RISK
- `item_type`: INCIDENT, TASK
- `limit`: Number of alerts to return

---

## Testing

### Test Database Views
```sql
-- Test executive overview
SELECT * FROM v_executive_sla_overview;

-- Test with filters
SELECT * FROM v_incident_sla_monitoring 
WHERE severity = 'CRITICAL' AND region = 'gauteng'
LIMIT 5;

-- Check alerts
SELECT * FROM v_sla_alerts_escalation 
WHERE alert_level = 'CRITICAL'
LIMIT 5;
```

### Test API Endpoints
```bash
# Using curl
curl -X GET "http://localhost:8000/api/v1/dashboard/executive-sla-overview"

# Using httpie
http GET localhost:8000/api/v1/dashboard/executive-sla-overview

# Using Python
import requests
response = requests.get("http://localhost:8000/api/v1/dashboard/executive-sla-overview")
print(response.json())
```

### Test Frontend Components
```bash
# Start dev server
npm run dev

# Navigate to dashboard
# http://localhost:5173/dashboard/manager/overview

# Check console for API calls
# Open DevTools > Network tab > API calls
```

---

## Troubleshooting

### "View does not exist" Error
```sql
-- Check if views were created
SELECT viewname FROM pg_views WHERE viewname LIKE 'v_%';

-- If missing, re-run the SQL script
\i scripts/01_create_management_dashboard_views.sql
```

### Empty Results in Views
```sql
-- Check if data exists
SELECT COUNT(*) FROM incidents;
SELECT COUNT(*) FROM tasks;

-- Check date range
SELECT * FROM incidents WHERE created_at >= NOW() - INTERVAL '90 days';
```

### API Returns 500 Error
```bash
# Check backend logs
tail -f logs/app.log

# Verify database connection
psql -U postgres -d seacom_db -c "SELECT 1"

# Test view directly
psql -U postgres -d seacom_db -c "SELECT * FROM v_executive_sla_overview"
```

### Frontend Shows No Data
```javascript
// Check network requests
// 1. Open DevTools > Network tab
// 2. Look for /api/v1/dashboard/* requests
// 3. Check response status (should be 200)
// 4. Check response body has data

// Check React Query state
// Install React Query DevTools:
// npm install @tanstack/react-query-devtools
```

---

## Performance Tips

### Database
1. Run `ANALYZE` on tables monthly
2. Monitor slow queries: `log_min_duration_statement = 1000`
3. Check index usage: `SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan DESC`

### Frontend
1. Use Chrome DevTools Profiler
2. Check component render times
3. Monitor network request timing
4. Use React DevTools Profiler

### API
1. Monitor endpoint response times
2. Check database query execution plans
3. Use `EXPLAIN ANALYZE` for slow queries
4. Consider caching for heavy aggregations

---

## Scaling for Production

### Database
```sql
-- Enable query results caching
CREATE MATERIALIZED VIEW v_executive_sla_overview_cached AS
SELECT * FROM v_executive_sla_overview;

CREATE INDEX ON v_executive_sla_overview_cached(compliance_percentage);

-- Refresh periodically
REFRESH MATERIALIZED VIEW v_executive_sla_overview_cached;
```

### Frontend
```typescript
// Increase stale time for less frequent updates
const queryOptions = {
  staleTime: 10 * 60 * 1000, // 10 minutes
  refetchInterval: 5 * 60 * 1000, // 5 minutes
};
```

### API
```python
# Add caching headers
from fastapi import Response

@router.get("/executive-sla-overview")
def get_overview(response: Response):
    response.headers["Cache-Control"] = "public, max-age=300"
    return data
```

---

## Support Resources

### Documentation
- **Architecture**: See `DASHBOARD_ARCHITECTURE.md`
- **Implementation**: See `DASHBOARD_IMPLEMENTATION_GUIDE.md`
- **SQL**: See `scripts/01_create_management_dashboard_views.sql`

### Code Examples
- **Backend**: See `app/api/v1/dashboard.py` (in implementation guide)
- **Frontend**: See `src/pages/dashboards/manager/`
- **Queries**: See `src/queries/management-dashboard.ts`
- **Helpers**: See `src/lib/dashboard-helpers.ts`

### Getting Help
1. Check error messages in logs
2. Review SQL views with `\d+ v_view_name`
3. Test API directly with curl
4. Check browser DevTools Network/Console tabs
5. Review React Query DevTools state

---

## Next Steps

1. **Execute SQL Views** - Run database migration
2. **Implement Endpoints** - Add dashboard routes
3. **Build Components** - Create React pages
4. **Test Integration** - Verify end-to-end flow
5. **Deploy** - Push to staging, then production
6. **Monitor** - Track performance and alerts

---

## Success Criteria

✅ All 9 database views created  
✅ API endpoints returning data  
✅ Frontend components display correctly  
✅ Filters work as expected  
✅ Real-time updates working (1-5 min)  
✅ Alerts generated for breaches  
✅ Performance <500ms for views  
✅ No SQL errors in logs  

---

**Ready to launch? Start with Step 1: Database Views!**
