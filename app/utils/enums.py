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


class Region(StrEnum):
    GAUTENG = "gauteng"
    MPUMALANGA = "mpumalanga"
    KZN = "kwazulu-natal"
    EASTERN_CAPE = "eastern-cape"
    NORTHERN_CAPE = "northern-cape"
    WESTERN_CAPE = "western-cape"
    FREE_STATE = "free-state"
