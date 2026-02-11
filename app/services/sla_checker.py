"""
SLA Breach Checker Service

This service checks incidents that are approaching or have breached their SLA
and sends notifications to assigned technicians.
"""

from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import and_
from sqlmodel import Session, select

from app.models import Incident
from app.utils.enums import IncidentStatus
from app.utils.funcs import utcnow


SLA_THRESHOLDS = {
    "critical": 1,
    "high": 4,
    "medium": 8,
    "low": 24,
    "default": 8,
}

WARNING_THRESHOLD = 0.75


def extract_priority_from_description(description: str) -> str:
    """Extract priority level from incident description format: [PRIORITY] description."""
    if not description:
        return "default"

    description_upper = description.upper()
    if description_upper.startswith("[CRITICAL]"):
        return "critical"
    if description_upper.startswith("[HIGH]"):
        return "high"
    if description_upper.startswith("[MEDIUM]"):
        return "medium"
    if description_upper.startswith("[LOW]"):
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
    Check for incidents approaching SLA breach and those already breached.

    Returns:
        Tuple of (warnings, breaches) where each is a list of incident info dicts.
    """
    from app.services.notification import _NotificationService, NotificationTemplates
    from app.services.webhook import WebhookService
    import threading

    notification_service = _NotificationService()
    now = utcnow()
    warnings: list[dict] = []
    breaches: list[dict] = []

    statement = select(Incident).where(
        and_(
            Incident.status == IncidentStatus.OPEN,
            Incident.deleted_at.is_(None),
        )
    )
    open_incidents = session.exec(statement).all()

    for incident in open_incidents:
        priority = extract_priority_from_description(incident.description)
        sla_deadline = get_sla_deadline(incident)
        warning_time = get_warning_time(incident)

        site_name = incident.site.name if incident.site else "Unknown Site"
        tech_name = (
            f"{incident.technician.user.name} {incident.technician.user.surname}"
            if incident.technician
            else "Unknown"
        )

        if now >= sla_deadline:
            breach_data = {
                "incident_id": str(incident.id),
                "site_name": site_name,
                "technician_name": tech_name,
                "priority": priority,
                "sla_deadline": sla_deadline.isoformat(),
                "time_overdue": str(now - sla_deadline),
                "event_type": "sla_breach",
                "timestamp": now.isoformat(),
            }
            breaches.append(breach_data)

            if incident.technician and incident.technician.user_id:
                notification_service.create_notification_from_template(
                    user_id=incident.technician.user_id,
                    template=NotificationTemplates.sla_breached(site_name, priority),
                    session=session,
                )

            def send_webhook_breach() -> None:
                import asyncio

                asyncio.run(WebhookService.send_webhook("sla_breach", breach_data))

            thread = threading.Thread(target=send_webhook_breach)
            thread.daemon = True
            thread.start()

        elif now >= warning_time:
            time_remaining = sla_deadline - now
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            if minutes_remaining < 60:
                time_str = f"{minutes_remaining} minutes"
            else:
                hours = minutes_remaining // 60
                mins = minutes_remaining % 60
                time_str = f"{hours}h {mins}m"

            warning_data = {
                "incident_id": str(incident.id),
                "site_name": site_name,
                "technician_name": tech_name,
                "priority": priority,
                "sla_deadline": sla_deadline.isoformat(),
                "time_remaining_minutes": minutes_remaining,
                "event_type": "sla_warning",
                "timestamp": now.isoformat(),
            }
            warnings.append(warning_data)

            if incident.technician and incident.technician.user_id:
                notification_service.create_notification_from_template(
                    user_id=incident.technician.user_id,
                    template=NotificationTemplates.sla_warning(site_name, priority, time_str),
                    session=session,
                )

            def send_webhook_warning() -> None:
                import asyncio

                asyncio.run(WebhookService.send_webhook("sla_warning", warning_data))

            thread = threading.Thread(target=send_webhook_warning)
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
        "resolved_within_sla": resolved_within_sla,
    }
