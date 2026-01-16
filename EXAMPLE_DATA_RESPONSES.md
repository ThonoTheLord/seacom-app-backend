# Management Dashboard - Example Data & Responses

## Executive SLA Overview Response

```json
{
  "total_items": 247,
  "within_sla_count": 198,
  "at_risk_count": 35,
  "critical_count": 12,
  "breached_count": 2,
  "compliance_percentage": 80.2,
  "at_risk_percentage": 19.0,
  "last_updated": "2024-01-16T14:32:00Z"
}
```

---

## Incident SLA Monitoring Response

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "seacom_ref": "INC-2024-001234",
      "description": "Critical network outage at Johannesburg hub affecting 50+ sites",
      "incident_status": "in-progress",
      "severity": "CRITICAL",
      "sla_minutes": 240,
      "created_at": "2024-01-16T12:00:00Z",
      "start_time": "2024-01-16T12:15:00Z",
      "resolved_at": null,
      "sla_deadline": "2024-01-16T16:00:00Z",
      "sla_remaining_minutes": 84.5,
      "sla_percentage_used": 70.3,
      "sla_status": "AT_RISK",
      "site_id": "jnb-hub-001",
      "site_name": "Johannesburg Hub",
      "region": "gauteng",
      "technician_id": "tech-001",
      "technician_name": "John Mkhize",
      "technician_email": "john.mkhize@seacom.co.za"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "seacom_ref": "INC-2024-001235",
      "description": "Major: Router configuration error in Cape Town office",
      "incident_status": "resolved",
      "severity": "MAJOR",
      "sla_minutes": 480,
      "created_at": "2024-01-16T08:00:00Z",
      "start_time": "2024-01-16T08:30:00Z",
      "resolved_at": "2024-01-16T10:45:00Z",
      "sla_deadline": "2024-01-16T16:00:00Z",
      "sla_remaining_minutes": 445.25,
      "sla_percentage_used": 36.5,
      "sla_status": "WITHIN_SLA",
      "site_id": "cpt-office-001",
      "site_name": "Cape Town Office",
      "region": "western-cape",
      "technician_id": "tech-002",
      "technician_name": "Sarah Van Der Merwe",
      "technician_email": "sarah.vandm@seacom.co.za"
    }
  ],
  "total": 156
}
```

---

## Task Performance & Compliance Response

```json
{
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "seacom_ref": "TSK-2024-005678",
      "description": "Routine maintenance on Pretoria rack equipment",
      "task_type": "routine-maintenance",
      "task_status": "started",
      "sla_minutes": 4320,
      "task_category": "Routine Maintenance",
      "start_time": "2024-01-15T08:00:00Z",
      "scheduled_end_time": "2024-01-17T08:00:00Z",
      "completed_at": null,
      "created_at": "2024-01-13T14:00:00Z",
      "sla_deadline": "2024-01-16T14:00:00Z",
      "sla_remaining_minutes": 1456.75,
      "actual_duration_minutes": 2048.5,
      "sla_status": "WITHIN_SLA",
      "site_id": "pta-rack-001",
      "site_name": "Pretoria Rack Facility",
      "region": "gauteng",
      "technician_id": "tech-003",
      "technician_name": "Peter Ndlela",
      "technician_email": "peter.ndlela@seacom.co.za"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "seacom_ref": "TSK-2024-005679",
      "description": "Corrective: Replace faulty power supply in Durban facility",
      "task_type": "remote-hand-support",
      "task_status": "pending",
      "sla_minutes": 2880,
      "task_category": "Corrective",
      "start_time": "2024-01-16T09:00:00Z",
      "scheduled_end_time": "2024-01-17T09:00:00Z",
      "completed_at": null,
      "created_at": "2024-01-16T10:00:00Z",
      "sla_deadline": "2024-01-18T10:00:00Z",
      "sla_remaining_minutes": 2759.25,
      "actual_duration_minutes": 120.75,
      "sla_status": "WITHIN_SLA",
      "site_id": "dur-facility-001",
      "site_name": "Durban Facility",
      "region": "kwazulu-natal",
      "technician_id": "tech-004",
      "technician_name": "Themba Dlamini",
      "technician_email": "themba.dlamini@seacom.co.za"
    }
  ],
  "total": 89
}
```

---

## Site Risk & Reliability Response

```json
{
  "data": [
    {
      "site_id": "jnb-hub-001",
      "site_name": "Johannesburg Hub",
      "region": "gauteng",
      "incident_count": 12,
      "open_incidents": 2,
      "resolved_incidents": 10,
      "incidents_30_days": 8,
      "incidents_7_days": 3,
      "avg_resolution_time_minutes": 356.5,
      "task_count": 45,
      "pending_tasks": 8,
      "completed_tasks": 37,
      "sla_compliance_percentage": 75.3,
      "risk_level": "HIGH",
      "site_status": "ACTIVE_INCIDENTS",
      "last_updated": "2024-01-16T14:30:00Z"
    },
    {
      "site_id": "cpt-office-001",
      "site_name": "Cape Town Office",
      "region": "western-cape",
      "incident_count": 2,
      "open_incidents": 0,
      "resolved_incidents": 2,
      "incidents_30_days": 1,
      "incidents_7_days": 0,
      "avg_resolution_time_minutes": 245.0,
      "task_count": 12,
      "pending_tasks": 1,
      "completed_tasks": 11,
      "sla_compliance_percentage": 95.8,
      "risk_level": "LOW",
      "site_status": "HEALTHY",
      "last_updated": "2024-01-16T14:30:00Z"
    },
    {
      "site_id": "dur-facility-001",
      "site_name": "Durban Facility",
      "region": "kwazulu-natal",
      "incident_count": 6,
      "open_incidents": 1,
      "resolved_incidents": 5,
      "incidents_30_days": 4,
      "incidents_7_days": 1,
      "avg_resolution_time_minutes": 512.3,
      "task_count": 28,
      "pending_tasks": 5,
      "completed_tasks": 23,
      "sla_compliance_percentage": 68.9,
      "risk_level": "MEDIUM",
      "site_status": "HIGH_FREQUENCY",
      "last_updated": "2024-01-16T14:30:00Z"
    }
  ],
  "total": 23
}
```

---

## Technician Performance Response

```json
{
  "data": [
    {
      "technician_id": "tech-001",
      "full_name": "John Mkhize",
      "email": "john.mkhize@seacom.co.za",
      "incident_count": 18,
      "task_count": 32,
      "open_incidents": 3,
      "pending_tasks": 6,
      "total_workload": 50,
      "incident_sla_compliance": 84.5,
      "task_sla_compliance": 78.2,
      "avg_incident_resolution_minutes": 285.4,
      "avg_task_completion_minutes": 1956.8,
      "workload_level": "HIGH",
      "performance_level": "GOOD",
      "last_updated": "2024-01-16T00:00:00Z"
    },
    {
      "technician_id": "tech-002",
      "full_name": "Sarah Van Der Merwe",
      "email": "sarah.vandm@seacom.co.za",
      "incident_count": 8,
      "task_count": 15,
      "open_incidents": 0,
      "pending_tasks": 1,
      "total_workload": 23,
      "incident_sla_compliance": 96.2,
      "task_sla_compliance": 94.8,
      "avg_incident_resolution_minutes": 198.5,
      "avg_task_completion_minutes": 1245.3,
      "workload_level": "MEDIUM",
      "performance_level": "EXCELLENT",
      "last_updated": "2024-01-16T00:00:00Z"
    },
    {
      "technician_id": "tech-003",
      "full_name": "Peter Ndlela",
      "email": "peter.ndlela@seacom.co.za",
      "incident_count": 12,
      "task_count": 28,
      "open_incidents": 2,
      "pending_tasks": 5,
      "total_workload": 40,
      "incident_sla_compliance": 65.3,
      "task_sla_compliance": 58.9,
      "avg_incident_resolution_minutes": 542.8,
      "avg_task_completion_minutes": 2156.4,
      "workload_level": "HIGH",
      "performance_level": "NEEDS_SUPPORT",
      "last_updated": "2024-01-16T00:00:00Z"
    }
  ],
  "total": 12
}
```

---

## Regional SLA Analytics Response

```json
[
  {
    "region": "gauteng",
    "incident_count": 34,
    "open_incidents": 5,
    "incidents_7_days": 8,
    "incident_sla_compliance": 72.4,
    "avg_resolution_minutes": 356.8,
    "task_count": 67,
    "pending_tasks": 12,
    "task_sla_compliance": 76.2,
    "overall_sla_compliance": 74.3,
    "region_status": "AT_RISK",
    "last_updated": "2024-01-16T14:00:00Z"
  },
  {
    "region": "western-cape",
    "incident_count": 8,
    "open_incidents": 0,
    "incidents_7_days": 1,
    "incident_sla_compliance": 92.3,
    "avg_resolution_minutes": 245.2,
    "task_count": 15,
    "pending_tasks": 1,
    "task_sla_compliance": 95.8,
    "overall_sla_compliance": 94.1,
    "region_status": "EXCELLENT",
    "last_updated": "2024-01-16T14:00:00Z"
  },
  {
    "region": "kwazulu-natal",
    "incident_count": 18,
    "open_incidents": 2,
    "incidents_7_days": 4,
    "incident_sla_compliance": 68.9,
    "avg_resolution_minutes": 512.3,
    "task_count": 34,
    "pending_tasks": 6,
    "task_sla_compliance": 71.5,
    "overall_sla_compliance": 70.2,
    "region_status": "AT_RISK",
    "last_updated": "2024-01-16T14:00:00Z"
  }
]
```

---

## SLA Trend Analysis Response

```json
[
  {
    "metric_date": "2024-01-16",
    "metric_type": "INCIDENT",
    "item_count": 8,
    "compliant_count": 6,
    "daily_compliance_percentage": 75.0
  },
  {
    "metric_date": "2024-01-16",
    "metric_type": "TASK",
    "item_count": 12,
    "compliant_count": 10,
    "daily_compliance_percentage": 83.3
  },
  {
    "metric_date": "2024-01-15",
    "metric_type": "INCIDENT",
    "item_count": 6,
    "compliant_count": 5,
    "daily_compliance_percentage": 83.3
  },
  {
    "metric_date": "2024-01-15",
    "metric_type": "TASK",
    "item_count": 14,
    "compliant_count": 11,
    "daily_compliance_percentage": 78.6
  },
  {
    "metric_date": "2024-01-14",
    "metric_type": "INCIDENT",
    "item_count": 5,
    "compliant_count": 4,
    "daily_compliance_percentage": 80.0
  },
  {
    "metric_date": "2024-01-14",
    "metric_type": "TASK",
    "item_count": 10,
    "compliant_count": 8,
    "daily_compliance_percentage": 80.0
  }
]
```

---

## SLA Alerts & Escalation Response

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "item_type": "INCIDENT",
    "severity": "CRITICAL",
    "created_at": "2024-01-16T12:00:00Z",
    "sla_deadline": "2024-01-16T16:00:00Z",
    "alert_level": "CRITICAL",
    "location": "Johannesburg Hub",
    "assigned_to": "John Mkhize",
    "current_status": "in-progress",
    "priority_order": 2
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "item_type": "TASK",
    "severity": "CORRECTIVE",
    "created_at": "2024-01-15T14:00:00Z",
    "sla_deadline": "2024-01-17T14:00:00Z",
    "alert_level": "CRITICAL",
    "location": "Pretoria Rack Facility",
    "assigned_to": "Peter Ndlela",
    "current_status": "pending",
    "priority_order": 2
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "item_type": "INCIDENT",
    "severity": "MAJOR",
    "created_at": "2024-01-16T08:00:00Z",
    "sla_deadline": "2024-01-16T18:00:00Z",
    "alert_level": "AT_RISK",
    "location": "Durban Facility",
    "assigned_to": "Themba Dlamini",
    "current_status": "in-progress",
    "priority_order": 3
  }
]
```

---

## Access Request SLA Impact Response

```json
{
  "data": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "description": "Site access for network upgrade at Johannesburg",
      "request_status": "requested",
      "sla_minutes": 120,
      "created_at": "2024-01-16T12:30:00Z",
      "start_time": "2024-01-16T13:00:00Z",
      "end_time": "2024-01-16T16:00:00Z",
      "approved_at": null,
      "sla_deadline": "2024-01-16T14:30:00Z",
      "sla_remaining_minutes": -15.5,
      "sla_status": "BREACHED",
      "site_id": "jnb-hub-001",
      "site_name": "Johannesburg Hub",
      "region": "gauteng",
      "technician_id": "tech-001",
      "technician_name": "John Mkhize",
      "technician_email": "john.mkhize@seacom.co.za",
      "task_id": "tsk-001",
      "request_type": "TASK_DEPENDENT"
    },
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "description": "Emergency access for hardware diagnostics",
      "request_status": "approved",
      "sla_minutes": 120,
      "created_at": "2024-01-16T13:00:00Z",
      "start_time": "2024-01-16T13:30:00Z",
      "end_time": "2024-01-16T17:00:00Z",
      "approved_at": "2024-01-16T13:45:00Z",
      "sla_deadline": "2024-01-16T15:00:00Z",
      "sla_remaining_minutes": 75.25,
      "sla_status": "WITHIN_SLA",
      "site_id": "dur-facility-001",
      "site_name": "Durban Facility",
      "region": "kwazulu-natal",
      "technician_id": "tech-004",
      "technician_name": "Themba Dlamini",
      "technician_email": "themba.dlamini@seacom.co.za",
      "task_id": null,
      "request_type": "STANDALONE"
    }
  ],
  "total": 24
}
```

---

## Filter Examples

### Filter by Multiple Criteria
```
GET /api/v1/dashboard/incident-sla-monitoring?severity=CRITICAL&region=gauteng&sla_status=AT_RISK&limit=10&offset=0
```

### Regional Filter
```
GET /api/v1/dashboard/task-performance?region=gauteng&limit=50
```

### Alert Filtering
```
GET /api/v1/dashboard/sla-alerts?alert_level=BREACHED&item_type=INCIDENT&limit=5
```

### Performance Level Filtering
```
GET /api/v1/dashboard/technician-performance?performance_level=NEEDS_SUPPORT&workload_level=HIGH
```

---

## Chart Data Format

### Executive Overview KPI Cards
```javascript
[
  { label: "Total Items", value: 247 },
  { label: "Compliance %", value: 80.2 },
  { label: "At Risk", value: 35 },
  { label: "Breached", value: 2 }
]
```

### Compliance Trend (Line Chart)
```javascript
[
  { date: "2024-01-14", compliance: 78.5, at_risk: 22, breached: 1 },
  { date: "2024-01-15", compliance: 81.2, at_risk: 18, breached: 0 },
  { date: "2024-01-16", compliance: 80.2, at_risk: 19, breached: 2 }
]
```

### Regional Comparison (Bar Chart)
```javascript
[
  { region: "Gauteng", compliance: 74.3, incidents: 34, tasks: 67 },
  { region: "Western Cape", compliance: 94.1, incidents: 8, tasks: 15 },
  { region: "KZN", compliance: 70.2, incidents: 18, tasks: 34 }
]
```

### SLA Status Distribution (Pie Chart)
```javascript
[
  { status: "WITHIN_SLA", count: 198, percentage: 80.2 },
  { status: "AT_RISK", count: 35, percentage: 14.2 },
  { status: "CRITICAL", count: 12, percentage: 4.9 },
  { status: "BREACHED", count: 2, percentage: 0.8 }
]
```

---

## Notes

- All timestamps are in UTC (ISO 8601 format)
- Percentages are returned as floats (0-100)
- Negative remaining minutes indicate breach
- Technician names are from users table via relationships
- Regional data aggregated across all sites in region
- Alert priority order: BREACHED(1) < CRITICAL(2) < AT_RISK(3)
- Non-punitive design: Individual technician metrics not ranked
