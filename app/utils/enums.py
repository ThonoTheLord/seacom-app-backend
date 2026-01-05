from enum import StrEnum


class UserRole(StrEnum):
    """"""
    ADMIN = "admin"
    MANAGER = "manager"
    TECHNICIAN = "technician"
    NOC = "noc"


class UserStatus(StrEnum):
    """"""
    ACTIVE = "active"
    DISABLED = "disabled"


class TaskType(StrEnum):
    RHS = "remote-hand-support"
    ROUTINE_MAINTENANCE = "routine-maintenance"
