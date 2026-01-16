/*
===================================================================================
Management Dashboard Database Views
===================================================================================
Purpose: Create read-only PostgreSQL views for executive SLA monitoring and 
         operational intelligence. Each view supports a dashboard tab.

Database: PostgreSQL
Timezone: All timestamps are UTC (timezone-aware)
Performance: Views use efficient aggregations and window functions

SLA Rules (in minutes):
- Critical Incidents: 240 minutes (4 hours)
- Major Incidents: 480 minutes (8 hours) 
- Minor Incidents: 1440 minutes (24 hours)
- Routine Maintenance: 4320 minutes (72 hours)
- Corrective Tasks: 2880 minutes (48 hours)
- Access Requests: 120 minutes (2 hours)
- Incident Reports: 720 minutes (12 hours after resolution)
- Task Reports: 1440 minutes (24 hours after completion)

SLA Status Categories:
- WITHIN_SLA: Remaining time > 30% of total SLA window
- AT_RISK: Remaining time between 30% and 10% (≥70% elapsed)
- CRITICAL: Remaining time ≤ 10% (≥90% elapsed)
- BREACHED: Remaining time < 0
===================================================================================
*/

-- ================================
-- 1. EXECUTIVE SLA OVERVIEW
-- ================================
-- Purpose: High-level KPIs for executive dashboard (C-suite view)
-- Shows SLA compliance percentage, trending, and alerts
-- Metrics: Overall compliance, breached count, at-risk count, by region
CREATE OR REPLACE VIEW v_executive_sla_overview AS
WITH incident_sla AS (
  SELECT
    i.id,
    i.created_at,
    i.resolved_at,
    CASE 
      WHEN i.description ILIKE '%critical%' THEN 240
      WHEN i.description ILIKE '%major%' THEN 480
      ELSE 1440
    END as sla_minutes,
    s.region,
    t.id as technician_id
  FROM incidents i
  LEFT JOIN sites s ON i.site_id = s.id
  LEFT JOIN technicians t ON i.technician_id = t.id
  WHERE i.created_at >= NOW() - INTERVAL '90 days'
),
task_sla AS (
  SELECT
    t.id,
    t.created_at,
    t.completed_at as resolved_at,
    CASE 
      WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
      ELSE 2880
    END as sla_minutes,
    s.region,
    t.technician_id
  FROM tasks t
  LEFT JOIN sites s ON t.site_id = s.id
  WHERE t.created_at >= NOW() - INTERVAL '90 days'
),
combined_sla AS (
  SELECT
    'incident'::text as item_type,
    incident_sla.*
  FROM incident_sla
  UNION ALL
  SELECT
    'task'::text as item_type,
    task_sla.*
  FROM task_sla
),
sla_status AS (
  SELECT
    item_type,
    id,
    region,
    technician_id,
    sla_minutes,
    resolved_at as completion_time,
    EXTRACT(EPOCH FROM (
      resolved_at - created_at
    )) / 60 as actual_minutes,
    CASE
      WHEN (
        EXTRACT(EPOCH FROM (
          resolved_at - created_at
        )) / 60
      ) > (CASE item_type
        WHEN 'incident' THEN EXTRACT(EPOCH FROM (NOW() - created_at)) / 60
        WHEN 'task' THEN EXTRACT(EPOCH FROM (NOW() - created_at)) / 60
      END) THEN 'BREACHED'
      WHEN (CASE item_type
        WHEN 'incident' THEN EXTRACT(EPOCH FROM (NOW() - created_at)) / 60
        WHEN 'task' THEN EXTRACT(EPOCH FROM (NOW() - created_at)) / 60
      END / CASE item_type
        WHEN 'incident' THEN 240
        WHEN 'task' THEN 4320
      END) >= 0.9 THEN 'CRITICAL'
      WHEN (CASE item_type
        WHEN 'incident' THEN EXTRACT(EPOCH FROM (NOW() - created_at)) / 60
        WHEN 'task' THEN EXTRACT(EPOCH FROM (NOW() - created_at)) / 60
      END / CASE item_type
        WHEN 'incident' THEN 240
        WHEN 'task' THEN 4320
      END) >= 0.7 THEN 'AT_RISK'
      ELSE 'WITHIN_SLA'
    END as sla_status
  FROM combined_sla
  WHERE resolved_at IS NOT NULL
)
SELECT
  COUNT(*)::INT as total_items,
  COUNT(CASE WHEN sla_status = 'WITHIN_SLA' THEN 1 END)::INT as within_sla_count,
  COUNT(CASE WHEN sla_status = 'AT_RISK' THEN 1 END)::INT as at_risk_count,
  COUNT(CASE WHEN sla_status = 'CRITICAL' THEN 1 END)::INT as critical_count,
  COUNT(CASE WHEN sla_status = 'BREACHED' THEN 1 END)::INT as breached_count,
  ROUND(
    100.0 * COUNT(CASE WHEN sla_status = 'WITHIN_SLA' THEN 1 END) / 
    NULLIF(COUNT(*), 0), 2
  )::NUMERIC as compliance_percentage,
  ROUND(
    100.0 * COUNT(CASE WHEN sla_status IN ('AT_RISK', 'CRITICAL') THEN 1 END) / 
    NULLIF(COUNT(*), 0), 2
  )::NUMERIC as at_risk_percentage,
  NOW() as last_updated
FROM sla_status;

-- ================================
-- 2. INCIDENT SLA MONITORING
-- ================================
-- Purpose: Detailed incident tracking with SLA compliance
-- Supports filtering by region, status, severity, date range
-- Includes: Incident details, SLA deadline, remaining time, status
CREATE OR REPLACE VIEW v_incident_sla_monitoring AS
SELECT
  i.id,
  i.seacom_ref,
  i.description,
  i.status as incident_status,
  CASE 
    WHEN i.description ILIKE '%critical%' THEN 'CRITICAL'
    WHEN i.description ILIKE '%major%' THEN 'MAJOR'
    ELSE 'MINOR'
  END as severity,
  CASE 
    WHEN i.description ILIKE '%critical%' THEN 240
    WHEN i.description ILIKE '%major%' THEN 480
    ELSE 1440
  END as sla_minutes,
  i.created_at,
  i.start_time,
  i.resolved_at,
  (i.created_at + INTERVAL '1 minute' * 
    CASE 
      WHEN i.description ILIKE '%critical%' THEN 240
      WHEN i.description ILIKE '%major%' THEN 480
      ELSE 1440
    END)::TIMESTAMPTZ as sla_deadline,
  EXTRACT(EPOCH FROM (
    (i.created_at + INTERVAL '1 minute' * 
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END) - NOW()
  )) / 60 as sla_remaining_minutes,
  EXTRACT(EPOCH FROM (
    (i.created_at + INTERVAL '1 minute' * 
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END) - NOW()
  )) / 60 / 
    CASE 
      WHEN i.description ILIKE '%critical%' THEN 240
      WHEN i.description ILIKE '%major%' THEN 480
      ELSE 1440
    END as sla_percentage_used,
  CASE
    WHEN i.resolved_at IS NULL THEN
      CASE
        WHEN EXTRACT(EPOCH FROM (
          (i.created_at + INTERVAL '1 minute' * 
            CASE 
              WHEN i.description ILIKE '%critical%' THEN 240
              WHEN i.description ILIKE '%major%' THEN 480
              ELSE 1440
            END) - NOW()
        )) / 60 < 0 THEN 'BREACHED'
        WHEN EXTRACT(EPOCH FROM (
          (i.created_at + INTERVAL '1 minute' * 
            CASE 
              WHEN i.description ILIKE '%critical%' THEN 240
              WHEN i.description ILIKE '%major%' THEN 480
              ELSE 1440
            END) - NOW()
        )) / 60 / 
          CASE 
            WHEN i.description ILIKE '%critical%' THEN 240
            WHEN i.description ILIKE '%major%' THEN 480
            ELSE 1440
          END >= 0.9 THEN 'CRITICAL'
        WHEN EXTRACT(EPOCH FROM (
          (i.created_at + INTERVAL '1 minute' * 
            CASE 
              WHEN i.description ILIKE '%critical%' THEN 240
              WHEN i.description ILIKE '%major%' THEN 480
              ELSE 1440
            END) - NOW()
        )) / 60 / 
          CASE 
            WHEN i.description ILIKE '%critical%' THEN 240
            WHEN i.description ILIKE '%major%' THEN 480
            ELSE 1440
          END >= 0.7 THEN 'AT_RISK'
        ELSE 'WITHIN_SLA'
      END
    ELSE
      CASE
        WHEN EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60 >
          CASE 
            WHEN i.description ILIKE '%critical%' THEN 240
            WHEN i.description ILIKE '%major%' THEN 480
            ELSE 1440
          END THEN 'BREACHED'
        ELSE 'WITHIN_SLA'
      END
  END as sla_status,
  s.id as site_id,
  s.name as site_name,
  s.region,
  t.id as technician_id,
  (u.name || ' ' || u.surname) as technician_name,
  u.email as technician_email
FROM incidents i
LEFT JOIN sites s ON i.site_id = s.id
LEFT JOIN technicians t ON i.technician_id = t.id
LEFT JOIN users u ON t.user_id = u.id
WHERE i.created_at >= NOW() - INTERVAL '90 days'
ORDER BY sla_deadline ASC;

-- ================================
-- 3. TASK PERFORMANCE & COMPLIANCE
-- ================================
-- Purpose: Task SLA tracking and performance metrics
-- Shows completion status, compliance, and delays
-- Filterable by task type, status, region, technician
CREATE OR REPLACE VIEW v_task_performance_compliance AS
SELECT
  t.id,
  t.seacom_ref,
  t.description,
  t.task_type,
  t.status as task_status,
  CASE 
    WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
    ELSE 2880
  END as sla_minutes,
  CASE 
    WHEN t.task_type::TEXT = 'routine-maintenance' THEN 'Routine Maintenance'
    ELSE 'Corrective'
  END as task_category,
  t.start_time,
  t.end_time as scheduled_end_time,
  t.completed_at,
  t.created_at,
  (t.created_at + INTERVAL '1 minute' * 
    CASE 
      WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
      ELSE 2880
    END)::TIMESTAMPTZ as sla_deadline,
  EXTRACT(EPOCH FROM (
    (t.created_at + INTERVAL '1 minute' * 
      CASE 
        WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
        ELSE 2880
      END) - COALESCE(t.completed_at, NOW())
  )) / 60 as sla_remaining_minutes,
  EXTRACT(EPOCH FROM (
    COALESCE(t.completed_at, NOW()) - t.created_at
  )) / 60 as actual_duration_minutes,
  CASE
    WHEN t.completed_at IS NULL THEN
      CASE
        WHEN EXTRACT(EPOCH FROM (
          (t.created_at + INTERVAL '1 minute' * 
            CASE 
              WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
              ELSE 2880
            END) - NOW()
        )) / 60 < 0 THEN 'BREACHED'
        WHEN EXTRACT(EPOCH FROM (
          (t.created_at + INTERVAL '1 minute' * 
            CASE 
              WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
              ELSE 2880
            END) - NOW()
        )) / 60 / 
          CASE 
            WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
            ELSE 2880
          END >= 0.9 THEN 'CRITICAL'
        WHEN EXTRACT(EPOCH FROM (
          (t.created_at + INTERVAL '1 minute' * 
            CASE 
              WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
              ELSE 2880
            END) - NOW()
        )) / 60 / 
          CASE 
            WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
            ELSE 2880
          END >= 0.7 THEN 'AT_RISK'
        ELSE 'WITHIN_SLA'
      END
    ELSE
      CASE
        WHEN EXTRACT(EPOCH FROM (t.completed_at - t.created_at)) / 60 >
          CASE 
            WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
            ELSE 2880
          END THEN 'BREACHED'
        ELSE 'WITHIN_SLA'
      END
  END as sla_status,
  s.id as site_id,
  s.name as site_name,
  s.region,
  tc.id as technician_id,
  (u.name || ' ' || u.surname) as technician_name,
  u.email as technician_email
FROM tasks t
LEFT JOIN sites s ON t.site_id = s.id
LEFT JOIN technicians tc ON t.technician_id = tc.id
LEFT JOIN users u ON tc.user_id = u.id
WHERE t.created_at >= NOW() - INTERVAL '90 days'
ORDER BY sla_deadline ASC;

-- ================================
-- 4. SITE RISK & RELIABILITY
-- ================================
-- Purpose: Site-level SLA performance and reliability metrics
-- Shows regional breakdown, incident density, compliance by site
-- Supports strategic site assessment and resource allocation
CREATE OR REPLACE VIEW v_site_risk_reliability AS
WITH site_incidents AS (
  SELECT
    s.id,
    s.name,
    s.region,
    COUNT(i.id)::INT as incident_count,
    COUNT(CASE WHEN i.resolved_at IS NULL THEN 1 END)::INT as open_incidents,
    COUNT(CASE WHEN i.status = 'RESOLVED' THEN 1 END)::INT as resolved_incidents,
    COUNT(CASE WHEN i.created_at >= NOW() - INTERVAL '30 days' THEN 1 END)::INT as incidents_30_days,
    COUNT(CASE WHEN i.created_at >= NOW() - INTERVAL '7 days' THEN 1 END)::INT as incidents_7_days,
    ROUND(CAST(AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60) AS NUMERIC), 2) as avg_resolution_time_minutes
  FROM sites s
  LEFT JOIN incidents i ON s.id = i.site_id 
    AND i.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY s.id, s.name, s.region
),
site_tasks AS (
  SELECT
    s.id,
    COUNT(t.id)::INT as task_count,
    COUNT(CASE WHEN t.completed_at IS NULL THEN 1 END)::INT as pending_tasks,
    COUNT(CASE WHEN t.status = 'COMPLETED' THEN 1 END)::INT as completed_tasks
  FROM sites s
  LEFT JOIN tasks t ON s.id = t.site_id 
    AND t.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY s.id
),
site_sla_compliance AS (
  SELECT
    s.id,
    COUNT(CASE WHEN (i.resolved_at IS NOT NULL AND 
      EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60 <=
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END) OR
      (i.resolved_at IS NULL AND
      EXTRACT(EPOCH FROM (NOW() - i.created_at)) / 60 <=
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END)
    THEN 1 END)::FLOAT as compliant_incidents,
    COUNT(i.id)::FLOAT as total_incidents_tracked
  FROM sites s
  LEFT JOIN incidents i ON s.id = i.site_id 
    AND i.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY s.id
)
SELECT
  si.id as site_id,
  si.name as site_name,
  si.region,
  si.incident_count,
  si.open_incidents,
  si.resolved_incidents,
  si.incidents_30_days,
  si.incidents_7_days,
  si.avg_resolution_time_minutes,
  st.task_count,
  st.pending_tasks,
  st.completed_tasks,
  ROUND(
    CAST(100.0 * ssc.compliant_incidents / NULLIF(ssc.total_incidents_tracked, 0) AS NUMERIC), 2
  ) as sla_compliance_percentage,
  CASE
    WHEN si.incident_count > 5 THEN 'HIGH'
    WHEN si.incident_count > 2 THEN 'MEDIUM'
    ELSE 'LOW'
  END as risk_level,
  CASE
    WHEN si.open_incidents > 0 THEN 'ACTIVE_INCIDENTS'
    WHEN si.incidents_7_days >= 3 THEN 'HIGH_FREQUENCY'
    WHEN si.avg_resolution_time_minutes > 480 THEN 'SLOW_RESOLUTION'
    ELSE 'HEALTHY'
  END as site_status,
  NOW() as last_updated
FROM site_incidents si
LEFT JOIN site_tasks st ON si.id = st.id
LEFT JOIN site_sla_compliance ssc ON si.id = ssc.id
ORDER BY incident_count DESC, region ASC;

-- ================================
-- 5. TECHNICIAN PERFORMANCE (Aggregated, Non-Punitive)
-- ================================
-- Purpose: Aggregate performance metrics for team management
-- Non-punitive: Focuses on workload, efficiency, and support needs
-- Supports: Workload balancing, training identification, recognition
CREATE OR REPLACE VIEW v_technician_performance AS
WITH technician_workload AS (
  SELECT
    t.id,
    (u.name || ' ' || u.surname) as technician_name,
    u.email,
    COUNT(DISTINCT i.id)::INT as incident_count,
    COUNT(DISTINCT tk.id)::INT as task_count,
    COUNT(DISTINCT CASE WHEN i.resolved_at IS NULL THEN i.id END)::INT as open_incidents,
    COUNT(DISTINCT CASE WHEN tk.completed_at IS NULL THEN tk.id END)::INT as pending_tasks
  FROM technicians t
  LEFT JOIN users u ON t.user_id = u.id
  LEFT JOIN incidents i ON t.id = i.technician_id 
    AND i.created_at >= NOW() - INTERVAL '90 days'
  LEFT JOIN tasks tk ON t.id = tk.technician_id 
    AND tk.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY t.id, (u.name || ' ' || u.surname), u.email
),
technician_sla_performance AS (
  SELECT
    t.id,
    COUNT(CASE WHEN i.resolved_at IS NOT NULL AND
      EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60 <=
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END
    THEN 1 END)::FLOAT as incidents_within_sla,
    COUNT(CASE WHEN i.resolved_at IS NOT NULL THEN 1 END)::FLOAT as total_resolved_incidents,
    COUNT(CASE WHEN tk.completed_at IS NOT NULL AND
      EXTRACT(EPOCH FROM (tk.completed_at - tk.created_at)) / 60 <=
      CASE 
        WHEN tk.task_type::TEXT = 'routine-maintenance' THEN 4320
        ELSE 2880
      END
    THEN 1 END)::FLOAT as tasks_within_sla,
    COUNT(CASE WHEN tk.completed_at IS NOT NULL THEN 1 END)::FLOAT as total_completed_tasks
  FROM technicians t
  LEFT JOIN incidents i ON t.id = i.technician_id 
    AND i.created_at >= NOW() - INTERVAL '90 days'
  LEFT JOIN tasks tk ON t.id = tk.technician_id 
    AND tk.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY t.id
),
technician_efficiency AS (
  SELECT
    t.id,
    ROUND(CAST(AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60) AS NUMERIC), 2) 
      as avg_incident_resolution_minutes,
    ROUND(CAST(AVG(EXTRACT(EPOCH FROM (tk.completed_at - tk.created_at)) / 60) AS NUMERIC), 2) 
      as avg_task_completion_minutes
  FROM technicians t
  LEFT JOIN incidents i ON t.id = i.technician_id 
    AND i.resolved_at IS NOT NULL
    AND i.created_at >= NOW() - INTERVAL '90 days'
  LEFT JOIN tasks tk ON t.id = tk.technician_id 
    AND tk.completed_at IS NOT NULL
    AND tk.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY t.id
)
SELECT
  tw.id as technician_id,
  tw.technician_name,
  tw.email,
  tw.incident_count,
  tw.task_count,
  tw.open_incidents,
  tw.pending_tasks,
  tw.incident_count + tw.task_count as total_workload,
  ROUND(
    CAST(100.0 * tsp.incidents_within_sla / NULLIF(tsp.total_resolved_incidents, 0) AS NUMERIC), 2
  ) as incident_sla_compliance,
  ROUND(
    CAST(100.0 * tsp.tasks_within_sla / NULLIF(tsp.total_completed_tasks, 0) AS NUMERIC), 2
  ) as task_sla_compliance,
  te.avg_incident_resolution_minutes,
  te.avg_task_completion_minutes,
  CASE
    WHEN tw.incident_count + tw.task_count > 20 THEN 'HIGH'
    WHEN tw.incident_count + tw.task_count > 10 THEN 'MEDIUM'
    ELSE 'LOW'
  END as workload_level,
  CASE
    WHEN tsp.incidents_within_sla / NULLIF(tsp.total_resolved_incidents, 0) >= 0.95 THEN 'EXCELLENT'
    WHEN tsp.incidents_within_sla / NULLIF(tsp.total_resolved_incidents, 0) >= 0.80 THEN 'GOOD'
    WHEN tsp.incidents_within_sla / NULLIF(tsp.total_resolved_incidents, 0) >= 0.60 THEN 'NEEDS_SUPPORT'
    ELSE 'AT_RISK'
  END as performance_level,
  NOW() as last_updated
FROM technician_workload tw
LEFT JOIN technician_sla_performance tsp ON tw.id = tsp.id
LEFT JOIN technician_efficiency te ON tw.id = te.id
ORDER BY tw.incident_count + tw.task_count DESC;

-- ================================
-- 6. ACCESS REQUEST SLA IMPACT
-- ================================
-- Purpose: Monitor access request approval SLA
-- Critical for technician field access and task initiation
-- Affects downstream incident/task resolution timelines
CREATE OR REPLACE VIEW v_access_request_sla_impact AS
SELECT
  ar.id,
  ar.description,
  ar.status as request_status,
  120 as sla_minutes, -- 2 hour SLA
  ar.created_at,
  ar.start_time,
  ar.end_time,
  ar.approved_at,
  (ar.created_at + INTERVAL '2 hours')::TIMESTAMPTZ as sla_deadline,
  EXTRACT(EPOCH FROM (
    (ar.created_at + INTERVAL '2 hours') - 
    COALESCE(ar.approved_at, NOW())
  )) / 60 as sla_remaining_minutes,
  CASE
    WHEN ar.approved_at IS NULL THEN
      CASE
        WHEN EXTRACT(EPOCH FROM (
          (ar.created_at + INTERVAL '2 hours') - NOW()
        )) / 60 < 0 THEN 'BREACHED'
        WHEN EXTRACT(EPOCH FROM (
          (ar.created_at + INTERVAL '2 hours') - NOW()
        )) / 60 <= 36 THEN 'CRITICAL' -- 30% of 2 hours
        WHEN EXTRACT(EPOCH FROM (
          (ar.created_at + INTERVAL '2 hours') - NOW()
        )) / 60 <= 84 THEN 'AT_RISK' -- 70% of 2 hours
        ELSE 'WITHIN_SLA'
      END
    ELSE
      CASE
        WHEN EXTRACT(EPOCH FROM (ar.approved_at - ar.created_at)) / 60 > 120 THEN 'BREACHED'
        ELSE 'WITHIN_SLA'
      END
  END as sla_status,
  s.id as site_id,
  s.name as site_name,
  s.region,
  t.id as technician_id,
  (u.name || ' ' || u.surname) as technician_name,
  u.email as technician_email,
  ar.task_id,
  CASE
    WHEN ar.task_id IS NOT NULL THEN 'TASK_DEPENDENT'
    ELSE 'STANDALONE'
  END as request_type
FROM access_requests ar
LEFT JOIN sites s ON ar.site_id = s.id
LEFT JOIN technicians t ON ar.technician_id = t.id
LEFT JOIN users u ON t.user_id = u.id
WHERE ar.created_at >= NOW() - INTERVAL '90 days'
  AND ar.status IN ('REQUESTED', 'APPROVED')
ORDER BY sla_deadline ASC;

-- ================================
-- 7. REGIONAL SLA ANALYTICS
-- ================================
-- Purpose: Regional performance comparison and trends
-- Supports: Regional management, resource planning, trend analysis
-- Metrics: Compliance by region, workload distribution, risk assessment
CREATE OR REPLACE VIEW v_regional_sla_analytics AS
WITH regional_incident_metrics AS (
  SELECT
    s.region,
    COUNT(i.id)::INT as incident_count,
    COUNT(CASE WHEN i.resolved_at IS NULL THEN 1 END)::INT as open_incidents,
    COUNT(CASE WHEN i.created_at >= NOW() - INTERVAL '7 days' THEN 1 END)::INT as incidents_7_days,
    COUNT(CASE WHEN i.resolved_at IS NOT NULL AND
      EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60 <=
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END
    THEN 1 END)::FLOAT as incidents_within_sla,
    COUNT(CASE WHEN i.resolved_at IS NOT NULL THEN 1 END)::FLOAT as resolved_incidents,
    ROUND(CAST(AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60) AS NUMERIC), 2) 
      as avg_resolution_minutes
  FROM sites s
  LEFT JOIN incidents i ON s.id = i.site_id 
    AND i.created_at >= NOW() - INTERVAL '90 days'
  WHERE s.region IS NOT NULL
  GROUP BY s.region
),
regional_task_metrics AS (
  SELECT
    s.region,
    COUNT(t.id)::INT as task_count,
    COUNT(CASE WHEN t.completed_at IS NULL THEN 1 END)::INT as pending_tasks,
    COUNT(CASE WHEN t.completed_at IS NOT NULL AND
      EXTRACT(EPOCH FROM (t.completed_at - t.created_at)) / 60 <=
      CASE 
        WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
        ELSE 2880
      END
    THEN 1 END)::FLOAT as tasks_within_sla,
    COUNT(CASE WHEN t.completed_at IS NOT NULL THEN 1 END)::FLOAT as completed_tasks
  FROM sites s
  LEFT JOIN tasks t ON s.id = t.site_id 
    AND t.created_at >= NOW() - INTERVAL '90 days'
  WHERE s.region IS NOT NULL
  GROUP BY s.region
)
SELECT
  rim.region,
  rim.incident_count,
  rim.open_incidents,
  rim.incidents_7_days,
  ROUND(
    CAST(100.0 * rim.incidents_within_sla / NULLIF(rim.resolved_incidents, 0) AS NUMERIC), 2
  ) as incident_sla_compliance,
  rim.avg_resolution_minutes,
  rtm.task_count,
  rtm.pending_tasks,
  ROUND(
    CAST(100.0 * rtm.tasks_within_sla / NULLIF(rtm.completed_tasks, 0) AS NUMERIC), 2
  ) as task_sla_compliance,
  ROUND(
    CAST((100.0 * rim.incidents_within_sla / NULLIF(rim.resolved_incidents, 0) +
     100.0 * rtm.tasks_within_sla / NULLIF(rtm.completed_tasks, 0)) / 2 AS NUMERIC), 2
  ) as overall_sla_compliance,
  CASE
    WHEN ROUND(
      CAST((100.0 * rim.incidents_within_sla / NULLIF(rim.resolved_incidents, 0) +
       100.0 * rtm.tasks_within_sla / NULLIF(rtm.completed_tasks, 0)) / 2 AS NUMERIC), 2
    ) >= 95 THEN 'EXCELLENT'
    WHEN ROUND(
      CAST((100.0 * rim.incidents_within_sla / NULLIF(rim.resolved_incidents, 0) +
       100.0 * rtm.tasks_within_sla / NULLIF(rtm.completed_tasks, 0)) / 2 AS NUMERIC), 2
    ) >= 85 THEN 'GOOD'
    WHEN ROUND(
      CAST((100.0 * rim.incidents_within_sla / NULLIF(rim.resolved_incidents, 0) +
       100.0 * rtm.tasks_within_sla / NULLIF(rtm.completed_tasks, 0)) / 2 AS NUMERIC), 2
    ) >= 70 THEN 'AT_RISK'
    ELSE 'CRITICAL'
  END as region_status,
  NOW() as last_updated
FROM regional_incident_metrics rim
LEFT JOIN regional_task_metrics rtm ON rim.region = rtm.region
ORDER BY overall_sla_compliance DESC;

-- ================================
-- 8. SLA TREND ANALYSIS
-- ================================
-- Purpose: Historical trends for strategic decision making
-- Tracks compliance trends over time
-- Supports forecasting and early risk detection
CREATE OR REPLACE VIEW v_sla_trend_analysis AS
SELECT
  DATE(i.resolved_at)::DATE as metric_date,
  'INCIDENT'::text as metric_type,
  COUNT(DISTINCT i.id)::INT as item_count,
  COUNT(DISTINCT CASE WHEN 
    EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60 <=
    CASE 
      WHEN i.description ILIKE '%critical%' THEN 240
      WHEN i.description ILIKE '%major%' THEN 480
      ELSE 1440
    END
  THEN i.id END)::INT as compliant_count,
  ROUND(
    CAST(100.0 * COUNT(DISTINCT CASE WHEN 
      EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60 <=
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END
    THEN i.id END) / NULLIF(COUNT(DISTINCT i.id), 0) AS NUMERIC), 2
  ) as daily_compliance_percentage
FROM incidents i
WHERE i.created_at >= NOW() - INTERVAL '90 days'
  AND i.resolved_at IS NOT NULL
GROUP BY DATE(i.resolved_at)
UNION ALL
SELECT
  DATE(tk.completed_at)::DATE as metric_date,
  'TASK'::text as metric_type,
  COUNT(DISTINCT tk.id)::INT as item_count,
  COUNT(DISTINCT CASE WHEN 
    EXTRACT(EPOCH FROM (tk.completed_at - tk.created_at)) / 60 <=
    CASE 
      WHEN tk.task_type::TEXT = 'routine-maintenance' THEN 4320
      ELSE 2880
    END
  THEN tk.id END)::INT as compliant_count,
  ROUND(
    CAST(100.0 * COUNT(DISTINCT CASE WHEN 
      EXTRACT(EPOCH FROM (tk.completed_at - tk.created_at)) / 60 <=
      CASE 
        WHEN tk.task_type::TEXT = 'routine-maintenance' THEN 4320
        ELSE 2880
      END
    THEN tk.id END) / NULLIF(COUNT(DISTINCT tk.id), 0) AS NUMERIC), 2
  ) as daily_compliance_percentage
FROM tasks tk
WHERE tk.created_at >= NOW() - INTERVAL '90 days'
  AND tk.completed_at IS NOT NULL
GROUP BY DATE(tk.completed_at)
ORDER BY metric_date DESC;

-- ================================
-- 9. ALERTS & ESCALATION VIEW
-- ================================
-- Purpose: Identify items requiring immediate attention
-- Real-time alerting for at-risk and breached SLAs
-- Prioritizes by severity and impact
CREATE OR REPLACE VIEW v_sla_alerts_escalation AS
WITH critical_incidents AS (
  SELECT
    i.id,
    'INCIDENT'::text as item_type,
    CASE 
      WHEN i.description ILIKE '%critical%' THEN 'CRITICAL'
      WHEN i.description ILIKE '%major%' THEN 'MAJOR'
      ELSE 'MINOR'
    END as severity,
    i.created_at,
    (i.created_at + INTERVAL '1 minute' * 
      CASE 
        WHEN i.description ILIKE '%critical%' THEN 240
        WHEN i.description ILIKE '%major%' THEN 480
        ELSE 1440
      END)::TIMESTAMPTZ as sla_deadline,
    CASE
      WHEN EXTRACT(EPOCH FROM (
        (i.created_at + INTERVAL '1 minute' * 
          CASE 
            WHEN i.description ILIKE '%critical%' THEN 240
            WHEN i.description ILIKE '%major%' THEN 480
            ELSE 1440
          END) - NOW()
      )) / 60 < 0 THEN 'BREACHED'
      WHEN EXTRACT(EPOCH FROM (
        (i.created_at + INTERVAL '1 minute' * 
          CASE 
            WHEN i.description ILIKE '%critical%' THEN 240
            WHEN i.description ILIKE '%major%' THEN 480
            ELSE 1440
          END) - NOW()
      )) / 60 <= 72 THEN 'CRITICAL' -- 30% of 240 minutes for critical
      ELSE 'AT_RISK'
    END as alert_level,
    s.name as location,
    (u.name || ' ' || u.surname) as assigned_to,
    i.status::TEXT as current_status
  FROM incidents i
  LEFT JOIN sites s ON i.site_id = s.id
  LEFT JOIN technicians t ON i.technician_id = t.id
  LEFT JOIN users u ON t.user_id = u.id
  WHERE i.resolved_at IS NULL
    AND i.created_at >= NOW() - INTERVAL '90 days'
),
critical_tasks AS (
  SELECT
    t.id,
    'TASK'::text as item_type,
    CASE 
      WHEN t.task_type::TEXT = 'routine-maintenance' THEN 'ROUTINE'
      ELSE 'CORRECTIVE'
    END as severity,
    t.created_at,
    (t.created_at + INTERVAL '1 minute' * 
      CASE 
        WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
        ELSE 2880
      END)::TIMESTAMPTZ as sla_deadline,
    CASE
      WHEN EXTRACT(EPOCH FROM (
        (t.created_at + INTERVAL '1 minute' * 
          CASE 
            WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
            ELSE 2880
          END) - NOW()
      )) / 60 < 0 THEN 'BREACHED'
      WHEN EXTRACT(EPOCH FROM (
        (t.created_at + INTERVAL '1 minute' * 
          CASE 
            WHEN t.task_type::TEXT = 'routine-maintenance' THEN 4320
            ELSE 2880
          END) - NOW()
      )) / 60 <= 1296 THEN 'CRITICAL' -- 30% of 4320 minutes
      ELSE 'AT_RISK'
    END as alert_level,
    s.name as location,
    (u.name || ' ' || u.surname) as assigned_to,
    t.status::TEXT as current_status
  FROM tasks t
  LEFT JOIN sites s ON t.site_id = s.id
  LEFT JOIN technicians tc ON t.technician_id = tc.id
  LEFT JOIN users u ON tc.user_id = u.id
  WHERE t.completed_at IS NULL
    AND t.created_at >= NOW() - INTERVAL '90 days'
)
SELECT
  id,
  item_type,
  severity,
  created_at,
  sla_deadline,
  alert_level,
  location,
  assigned_to,
  current_status,
  CASE alert_level
    WHEN 'BREACHED' THEN 1
    WHEN 'CRITICAL' THEN 2
    WHEN 'AT_RISK' THEN 3
  END as priority_order
FROM (
  SELECT * FROM critical_incidents
  UNION ALL
  SELECT * FROM critical_tasks
) combined
WHERE alert_level IN ('BREACHED', 'CRITICAL')
ORDER BY priority_order ASC, sla_deadline ASC;

-- ================================
-- Create Indexes for Performance
-- ================================
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_resolved_at ON incidents(resolved_at);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_site_id ON incidents(site_id);
CREATE INDEX IF NOT EXISTS idx_incidents_technician_id ON incidents(technician_id);

CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_completed_at ON tasks(completed_at);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_site_id ON tasks(site_id);
CREATE INDEX IF NOT EXISTS idx_tasks_technician_id ON tasks(technician_id);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);

CREATE INDEX IF NOT EXISTS idx_access_requests_created_at ON access_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_access_requests_approved_at ON access_requests(approved_at);
CREATE INDEX IF NOT EXISTS idx_access_requests_status ON access_requests(status);
CREATE INDEX IF NOT EXISTS idx_access_requests_site_id ON access_requests(site_id);
CREATE INDEX IF NOT EXISTS idx_access_requests_technician_id ON access_requests(technician_id);

CREATE INDEX IF NOT EXISTS idx_sites_region ON sites(region);

-- ================================
-- View Usage Documentation
-- ================================
/*

DASHBOARD VIEWS USAGE GUIDE:

1. v_executive_sla_overview
   - Executive dashboard KPI summary
   - Metrics: Total items, compliance %, at-risk count, breached count
   - Refresh: Every 5 minutes
   - Query: SELECT * FROM v_executive_sla_overview;

2. v_incident_sla_monitoring
   - Incident detail view with SLA tracking
   - Filters: WHERE severity = 'CRITICAL', WHERE region = 'GAUTENG'
   - Sort: ORDER BY sla_deadline ASC
   - Refresh: Real-time

3. v_task_performance_compliance
   - Task tracking and compliance metrics
   - Filters: WHERE task_status = 'PENDING', WHERE sla_status = 'CRITICAL'
   - Aggregations: GROUP BY task_category, region
   - Refresh: Real-time

4. v_site_risk_reliability
   - Site-level risk assessment
   - Filters: WHERE risk_level = 'HIGH', WHERE region = 'GAUTENG'
   - Sort: ORDER BY incident_count DESC
   - Refresh: Every 15 minutes

5. v_technician_performance
   - Aggregate performance (non-punitive)
   - Filters: WHERE workload_level = 'HIGH', WHERE performance_level = 'EXCELLENT'
   - Support: Identifies training needs, workload balancing opportunities
   - Refresh: Daily

6. v_access_request_sla_impact
   - Access request approval tracking
   - Filters: WHERE sla_status = 'BREACHED', WHERE request_type = 'TASK_DEPENDENT'
   - Impact: Critical for incident/task resolution timelines
   - Refresh: Real-time

7. v_regional_sla_analytics
   - Regional performance comparison
   - Aggregations: GROUP BY region
   - Trend tracking: Identifies regional patterns
   - Refresh: Every 30 minutes

8. v_sla_trend_analysis
   - Historical SLA trends (90-day window)
   - Time series data for charts
   - Trend detection: Identifies deteriorating compliance
   - Refresh: Daily

9. v_sla_alerts_escalation
   - Real-time alert generation
   - Prioritizes: BREACHED > CRITICAL > AT_RISK
   - Integration: Send to alerting systems (email, SMS, Slack)
   - Refresh: Every 1 minute

*/
