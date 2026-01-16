import { SLAStatus, AlertLevel, RiskLevel, PerformanceLevel } from "@/services/management-dashboard";

// ============================================================
// Color Utilities
// ============================================================

export const getSLAStatusColor = (status: SLAStatus): string => {
  const colorMap: Record<SLAStatus, string> = {
    [SLAStatus.WITHIN_SLA]: "bg-green-100 text-green-800 border-green-300",
    [SLAStatus.AT_RISK]: "bg-yellow-100 text-yellow-800 border-yellow-300",
    [SLAStatus.CRITICAL]: "bg-orange-100 text-orange-800 border-orange-300",
    [SLAStatus.BREACHED]: "bg-red-100 text-red-800 border-red-300",
  };
  return colorMap[status] || "bg-gray-100 text-gray-800";
};

export const getAlertLevelColor = (level: AlertLevel): string => {
  const colorMap: Record<AlertLevel, string> = {
    [AlertLevel.BREACHED]: "bg-red-100 text-red-800",
    [AlertLevel.CRITICAL]: "bg-orange-100 text-orange-800",
    [AlertLevel.AT_RISK]: "bg-yellow-100 text-yellow-800",
  };
  return colorMap[level] || "bg-gray-100 text-gray-800";
};

export const getRiskLevelColor = (level: RiskLevel): string => {
  const colorMap: Record<RiskLevel, string> = {
    [RiskLevel.HIGH]: "bg-red-100 text-red-800",
    [RiskLevel.MEDIUM]: "bg-yellow-100 text-yellow-800",
    [RiskLevel.LOW]: "bg-green-100 text-green-800",
  };
  return colorMap[level] || "bg-gray-100 text-gray-800";
};

export const getPerformanceLevelColor = (level: PerformanceLevel): string => {
  const colorMap: Record<PerformanceLevel, string> = {
    [PerformanceLevel.EXCELLENT]: "bg-green-100 text-green-800",
    [PerformanceLevel.GOOD]: "bg-blue-100 text-blue-800",
    [PerformanceLevel.NEEDS_SUPPORT]: "bg-yellow-100 text-yellow-800",
    [PerformanceLevel.AT_RISK]: "bg-red-100 text-red-800",
  };
  return colorMap[level] || "bg-gray-100 text-gray-800";
};

// ============================================================
// Status Badge Utilities
// ============================================================

export const getSLAStatusBadgeLabel = (status: SLAStatus): string => {
  const labelMap: Record<SLAStatus, string> = {
    [SLAStatus.WITHIN_SLA]: "✓ Within SLA",
    [SLAStatus.AT_RISK]: "⚠ At Risk",
    [SLAStatus.CRITICAL]: "🔴 Critical",
    [SLAStatus.BREACHED]: "❌ Breached",
  };
  return labelMap[status];
};

export const getAlertLevelBadgeLabel = (level: AlertLevel): string => {
  const labelMap: Record<AlertLevel, string> = {
    [AlertLevel.BREACHED]: "❌ BREACHED",
    [AlertLevel.CRITICAL]: "🔴 CRITICAL",
    [AlertLevel.AT_RISK]: "⚠️ AT RISK",
  };
  return labelMap[level];
};

// ============================================================
// Time Formatting Utilities
// ============================================================

export const formatMinutes = (minutes: number): string => {
  if (minutes < 0) return "Overdue";
  if (minutes < 60) return `${Math.round(minutes)}m`;
  if (minutes < 1440) return `${Math.round(minutes / 60)}h`;
  return `${Math.round(minutes / 1440)}d`;
};

export const formatMinutesDetailed = (minutes: number): string => {
  if (minutes < 0) {
    const absMinutes = Math.abs(minutes);
    const days = Math.floor(absMinutes / 1440);
    const hours = Math.floor((absMinutes % 1440) / 60);
    const mins = Math.floor(absMinutes % 60);

    if (days > 0) return `${days}d ${hours}h ${mins}m OVERDUE`;
    if (hours > 0) return `${hours}h ${mins}m OVERDUE`;
    return `${mins}m OVERDUE`;
  }

  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const mins = Math.floor(minutes % 60);

  if (days > 0) return `${days}d ${hours}h ${mins}m remaining`;
  if (hours > 0) return `${hours}h ${mins}m remaining`;
  return `${mins}m remaining`;
};

export const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString("en-ZA", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString("en-ZA", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

// ============================================================
// Percentage Utilities
// ============================================================

export const formatPercentage = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(1)}%`;
};

export const getSLAPercentageStatus = (percentage: number): SLAStatus => {
  if (percentage >= 100) return SLAStatus.BREACHED;
  if (percentage >= 90) return SLAStatus.CRITICAL;
  if (percentage >= 70) return SLAStatus.AT_RISK;
  return SLAStatus.WITHIN_SLA;
};

// ============================================================
// Progress Bar Utilities
// ============================================================

export const getSLAProgressBarColor = (percentage: number): string => {
  if (percentage >= 100) return "bg-red-600";
  if (percentage >= 90) return "bg-orange-600";
  if (percentage >= 70) return "bg-yellow-500";
  return "bg-green-600";
};

// ============================================================
// Compliance Calculation Utilities
// ============================================================

export const calculateCompliance = (
  compliantCount: number,
  totalCount: number
): number => {
  if (totalCount === 0) return 100;
  return (compliantCount / totalCount) * 100;
};

export const calculateAtRiskPercentage = (
  atRiskCount: number,
  totalCount: number
): number => {
  if (totalCount === 0) return 0;
  return (atRiskCount / totalCount) * 100;
};

// ============================================================
// Region Utilities
// ============================================================

export const regionDisplayName = (region: string): string => {
  const regionMap: Record<string, string> = {
    gauteng: "Gauteng",
    mpumalanga: "Mpumalanga",
    "kwazulu-natal": "KZN",
    "eastern-cape": "Eastern Cape",
    "northern-cape": "Northern Cape",
    "western-cape": "Western Cape",
    "free-state": "Free State",
    "north-west": "North West",
  };
  return regionMap[region.toLowerCase()] || region;
};

export const getAllRegions = (): Array<{ value: string; label: string }> => [
  { value: "gauteng", label: "Gauteng" },
  { value: "mpumalanga", label: "Mpumalanga" },
  { value: "kwazulu-natal", label: "KZN" },
  { value: "eastern-cape", label: "Eastern Cape" },
  { value: "northern-cape", label: "Northern Cape" },
  { value: "western-cape", label: "Western Cape" },
  { value: "free-state", label: "Free State" },
  { value: "north-west", label: "North West" },
];

// ============================================================
// Severity Utilities
// ============================================================

export const severityOrder = (severity: string): number => {
  const orderMap: Record<string, number> = {
    CRITICAL: 0,
    MAJOR: 1,
    MINOR: 2,
  };
  return orderMap[severity] ?? 999;
};

// ============================================================
// Chart Data Formatting Utilities
// ============================================================

export const formatChartData = (
  data: Array<{ date: string; value: number }>
): Array<{ date: string; value: number }> => {
  return data
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((item) => ({
      ...item,
      date: formatDate(item.date),
    }));
};

export const aggregateByRegion = <T extends { region: string; value: number }>(
  data: T[]
): Record<string, number> => {
  return data.reduce(
    (acc, item) => {
      acc[item.region] = (acc[item.region] || 0) + item.value;
      return acc;
    },
    {} as Record<string, number>
  );
};

// ============================================================
// Filter Utilities
// ============================================================

export const buildFilterQuery = (filters: Record<string, any>): string => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      params.append(key, String(value));
    }
  });
  return params.toString();
};

// ============================================================
// Alert Utilities
// ============================================================

export const getAlertIcon = (level: AlertLevel): string => {
  const iconMap: Record<AlertLevel, string> = {
    [AlertLevel.BREACHED]: "🔴",
    [AlertLevel.CRITICAL]: "⚠️",
    [AlertLevel.AT_RISK]: "⏰",
  };
  return iconMap[level];
};

export const getAlertSortOrder = (level: AlertLevel): number => {
  const orderMap: Record<AlertLevel, number> = {
    [AlertLevel.BREACHED]: 0,
    [AlertLevel.CRITICAL]: 1,
    [AlertLevel.AT_RISK]: 2,
  };
  return orderMap[level];
};

// ============================================================
// SLA Deadline Utilities
// ============================================================

export const isDeadlineSoon = (deadline: string, hours: number = 1): boolean => {
  const deadlineTime = new Date(deadline).getTime();
  const soonTime = new Date().getTime() + hours * 60 * 60 * 1000;
  return deadlineTime <= soonTime && deadlineTime > new Date().getTime();
};

export const isDeadlineBreached = (deadline: string): boolean => {
  const deadlineTime = new Date(deadline).getTime();
  return deadlineTime < new Date().getTime();
};

// ============================================================
// Export Summary Utilities
// ============================================================

export const generateSLASummary = (
  total: number,
  withinSLA: number,
  atRisk: number,
  critical: number,
  breached: number
): string => {
  const compliance = ((withinSLA / total) * 100).toFixed(1);
  return `${compliance}% compliance - ${breached} breached, ${critical} critical, ${atRisk} at-risk`;
};
