"""
SLA Breach Checker Service

This service checks for incidents that are approaching or have breached their SLA
and sends notifications to the assigned technicians.

SLA Thresholds (configurable):
- Critical Priority: 1 hour response time
- High Priority: 4 hours response time  
- Medium Priority: 8 hours response time
- Low Priority: 24 hours response time

Warning is sent when 75% of SLA time has elapsed without the incident being started.
"""

from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Tuple
from sqlmodel import Session, select
from sqlalchemy import and_

from app.utils.enums import IncidentStatus, NotificationPriority
from app.utils.funcs import utcnow
from app.models import Incident, User, Notification


# SLA thresholds in hours based on priority (extracted from description)
SLA_THRESHOLDS = {
    "critical": 1,    # 1 hour
    "high": 4,        # 4 hours
    "medium": 8,      # 8 hours
    "low": 24,        # 24 hours
    "default": 8,     # Default if no priority found
}

# Warning threshold - notify when this percentage of SLA time has elapsed
WARNING_THRESHOLD = 0.75  # 75%


def extract_priority_from_description(description: str) -> str:
    """Extract priority level from incident description format: [PRIORITY] description"""
    if not description:
        return "default"
    
    description_upper = description.upper()
    if description_upper.startswith("[CRITICAL]"):
        return "critical"
    elif description_upper.startswith("[HIGH]"):
        return "high"
    elif description_upper.startswith("[MEDIUM]"):
        return "medium"
    elif description_upper.startswith("[LOW]"):
        return "low"
    
    return "default"


def get_sla_deadline(incident: Incident) -> datetime:
    """Calculate the SLA deadline for an incident based on its priority."""
    priority = extract_priority_from_description(incident.description)
    sla_hours = SLA_THRESHOLDS.get(priority, SLA_THRESHOLDS["default"])
    return incident.start_time + timedelta(hours=sla_hours)


def get_warning_time(incident: Incident) -> datetime:
    """Calculate when to send a warning notification (75% of SLA time elapsed)."""
    priority = extract_priority_from_description(incident.description)
    sla_hours = SLA_THRESHOLDS.get(priority, SLA_THRESHOLDS["default"])
    warning_hours = sla_hours * WARNING_THRESHOLD
    return incident.start_time + timedelta(hours=warning_hours)


def check_sla_breaches(session: Session) -> Tuple[List[dict], List[dict]]:
    """
    Check for incidents approaching SLA breach and those that have already breached.
    
    Returns:
        Tuple of (warnings, breaches) where each is a list of incident info dicts
    """
    from app.services.notification import _NotificationService
    from app.services.webhook import WebhookService
    import asyncio
    notification_service = _NotificationService()
    
    now = utcnow()
    warnings = []
    breaches = []
    
    # Get all open incidents (not started or resolved)
    statement = select(Incident).where(
        and_(
            Incident.status == IncidentStatus.OPEN,
            Incident.deleted_at.is_(None)
        )
    )
    open_incidents = session.exec(statement).all()
    
    for incident in open_incidents:
        priority = extract_priority_from_description(incident.description)
        sla_deadline = get_sla_deadline(incident)
        warning_time = get_warning_time(incident)
        
        site_name = incident.site.name if incident.site else "Unknown Site"
        tech_name = f"{incident.technician.user.name} {incident.technician.user.surname}" if incident.technician else "Unknown"
        
        # Check if SLA has been breached
        if now >= sla_deadline:
            breach_data = {
                "incident_id": str(incident.id),
                "site_name": site_name,
                "technician_name": tech_name,
                "priority": priority,
                "sla_deadline": sla_deadline.isoformat(),
                "time_overdue": str(now - sla_deadline),
                "event_type": "sla_breach",
                "timestamp": now.isoformat()
            }
            breaches.append(breach_data)
            
            # Send breach notification to technician
            if incident.technician and incident.technician.user_id:
                notification_service.create_notification_for_user(
                    user_id=incident.technician.user_id,
                    title=f"⚠️ SLA BREACHED: {site_name}",
                    message=f"URGENT: The incident at {site_name} has BREACHED its {priority.upper()} priority SLA. Please attend immediately or escalate.",
                    priority=NotificationPriority.CRITICAL,
                    session=session
                )
            
            # Send webhook for breach
            import threading
            def send_webhook_async():
                import asyncio
                asyncio.run(WebhookService.send_webhook("sla_breach", breach_data))
            thread = threading.Thread(target=send_webhook_async)
            thread.daemon = True
            thread.start()
        
        # Check if approaching SLA breach (warning zone)
        elif now >= warning_time:
            time_remaining = sla_deadline - now
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            
            warning_data = {
                "incident_id": str(incident.id),
                "site_name": site_name,
                "technician_name": tech_name,
                "priority": priority,
                "sla_deadline": sla_deadline.isoformat(),
                "time_remaining_minutes": minutes_remaining,
                "event_type": "sla_warning",
                "timestamp": now.isoformat()
            }
            warnings.append(warning_data)
            
            # Send warning notification to technician
            if incident.technician and incident.technician.user_id:
                if minutes_remaining < 60:
                    time_str = f"{minutes_remaining} minutes"
                else:
                    hours = minutes_remaining // 60
                    mins = minutes_remaining % 60
                    time_str = f"{hours}h {mins}m"
                
                notification_service.create_notification_for_user(
                    user_id=incident.technician.user_id,
                    title=f"⏰ SLA Warning: {site_name}",
                    message=f"Incident at {site_name} ({priority.upper()} priority) will breach SLA in {time_str}. Please start work on this incident immediately.",
                    priority=NotificationPriority.HIGH,
                    session=session
                )
            
            # Send webhook for warning
            import threading
            def send_webhook_async():
                import asyncio
                asyncio.run(WebhookService.send_webhook("sla_warning", warning_data))
            thread = threading.Thread(target=send_webhook_async)
            thread.daemon = True
            thread.start()
    
    return warnings, breaches


def get_sla_status_for_incident(incident: Incident) -> dict:
    """Get the SLA status for a single incident."""
    now = utcnow()
    priority = extract_priority_from_description(incident.description)
    sla_deadline = get_sla_deadline(incident)
    warning_time = get_warning_time(incident)
    
    if incident.status == IncidentStatus.RESOLVED:
        status = "resolved"
        resolved_within_sla = incident.resolved_at <= sla_deadline if incident.resolved_at else False
    elif now >= sla_deadline:
        status = "breached"
        resolved_within_sla = False
    elif now >= warning_time:
        status = "warning"
        resolved_within_sla = None
    else:
        status = "ok"
        resolved_within_sla = None
    
    time_remaining = sla_deadline - now
    
    return {
        "priority": priority,
        "sla_hours": SLA_THRESHOLDS.get(priority, SLA_THRESHOLDS["default"]),
        "sla_deadline": sla_deadline.isoformat(),
        "status": status,
        "time_remaining_seconds": max(0, int(time_remaining.total_seconds())),
        "resolved_within_sla": resolved_within_sla
    }
