
export type AttendanceMasterStatus =
  | "active"
  | "archived";
export type WeekdayName =
  | "Monday"
  | "Tuesday"
  | "Wednesday"
  | "Thursday"
  | "Friday"
  | "Saturday"
  | "Sunday";
export type AttendanceTeam = {
  id: number;
  name: string;
  description: string | null;
  status: AttendanceMasterStatus;
  created_by_id: number;
  created_at: string;
  updated_at: string;
};
export type AttendanceTeamCreate = {
  name: string;
  description: string | null;
  status: AttendanceMasterStatus;
};
export type AttendanceTeamUpdate =
  Partial<AttendanceTeamCreate>;
export type AttendanceShift = {
  id: number;
  name: string;
  description: string | null;
  status: AttendanceMasterStatus;
  created_by_id: number;
  created_at: string;
  updated_at: string;
};
export type AttendanceShiftCreate = {
  name: string;
  description: string | null;
  status: AttendanceMasterStatus;
};
export type AttendanceShiftUpdate =
  Partial<AttendanceShiftCreate>;
export type AttendanceEmployee = {
  id: number;
  employee_code: string;
  full_name: string;
  designation: string;
  team_id: number;
  shift_id: number;
  weekly_holidays: WeekdayName[];
  is_active: boolean;
  created_by_id: number;
  created_at: string;
  updated_at: string;
};
export type AttendanceEmployeeCreate = {
  employee_code: string;
  full_name: string;
  designation: string;
  team_id: number;
  shift_id: number;
  weekly_holidays: WeekdayName[];
  is_active: boolean;
};
export type AttendanceEmployeeUpdate =
  Partial<AttendanceEmployeeCreate>;


export type AttendanceStatus =
  | "present"
  | "absent"
  | "on_leave"
  | "weekly_holiday";
export type DailyRosterItem = {
  employee_id: number;
  employee_code: string;
  full_name: string;
  designation: string;
  team_id: number;
  shift_id: number;
  weekly_holidays: string[];
  suggested_status: AttendanceStatus;
  saved_status: AttendanceStatus | null;
  note: string | null;
  record_id: number | null;
  approved_leave_id: number | null;
  approved_leave_type: LeaveType | null;
  approved_leave_reason: string | null;
};
export type DailyAttendanceRoster = {
  attendance_date: string;
  team_id: number;
  team_name: string;
  shift_id: number;
  shift_name: string;
  total_members: number;
  items: DailyRosterItem[];
};
export type DailyAttendanceEntry = {
  employee_id: number;
  status: AttendanceStatus;
  note: string | null;
};
export type DailyAttendanceSubmit = {
  attendance_date: string;
  team_id: number;
  shift_id: number;
  entries: DailyAttendanceEntry[];
};
export type DailyAttendanceSummary = {
  total_members: number;
  present: number;
  absent: number;
  on_leave: number;
  weekly_holiday: number;
};
export type DailyAttendanceSubmission = {
  attendance_date: string;
  team_id: number;
  team_name: string;
  shift_id: number;
  shift_name: string;
  summary: DailyAttendanceSummary;
  records: Array<{
    id: number;
    employee_id: number;
    attendance_date: string;
    team_id: number;
    shift_id: number;
    status: AttendanceStatus;
    note: string | null;
    recorded_by_id: number;
    created_at: string;
    updated_at: string;
  }>;
};


export type AttendanceHistoryItem = {
  attendance_date: string;
  team_id: number;
  team_name: string;
  shift_id: number;
  shift_name: string;
  summary: DailyAttendanceSummary;
  last_updated_at: string;
};
export type AttendanceHistoryList = {
  total_reports: number;
  items: AttendanceHistoryItem[];
};
export type AttendanceHistoryEmployee = {
  record_id: number;
  employee_id: number;
  employee_code: string;
  full_name: string;
  designation: string;
  status: AttendanceStatus;
  note: string | null;
  leave_id: number | null;
  leave_type: LeaveType | null;
  leave_reason: string | null;
  leave_from_date: string | null;
  leave_to_date: string | null;
  updated_at: string;
};
export type AttendanceHistoryReport = {
  attendance_date: string;
  team_id: number;
  team_name: string;
  shift_id: number;
  shift_name: string;
  summary: DailyAttendanceSummary;
  employees: AttendanceHistoryEmployee[];
  last_updated_at: string;
};


export type LeaveType =
  | "casual"
  | "sick"
  | "annual"
  | "other";
export type LeaveStatus =
  | "pending"
  | "approved"
  | "cancelled";
export type AttendanceLeave = {
  id: number;
  employee_id: number;
  leave_type: LeaveType;
  from_date: string;
  to_date: string;
  reason: string | null;
  status: LeaveStatus;
  created_by_id: number;
  approved_by_id: number | null;
  created_at: string;
  updated_at: string;
};
export type AttendanceLeaveCreate = {
  employee_id: number;
  leave_type: LeaveType;
  from_date: string;
  to_date: string;
  reason: string | null;
  status: LeaveStatus;
};
export type AttendanceLeaveList = {
  total: number;
  items: AttendanceLeave[];
};

export interface AttendanceAnalyticsCounts {
  total_records: number;
  working_day_records: number;
  present: number;
  absent: number;
  on_leave: number;
  weekly_holiday: number;
  attendance_rate: number;
}
export interface AttendanceAnalyticsDailyItem
  extends AttendanceAnalyticsCounts {
  attendance_date: string;
}
export interface AttendanceAnalyticsTeamItem
  extends AttendanceAnalyticsCounts {
  team_id: number;
  team_name: string;
}
export interface AttendanceAnalyticsShiftItem
  extends AttendanceAnalyticsCounts {
  shift_id: number;
  shift_name: string;
}
export interface AttendanceAnalyticsEmployeeItem
  extends AttendanceAnalyticsCounts {
  employee_id: number;
  employee_code: string;
  full_name: string;
  designation: string;
  team_id: number;
  team_name: string;
  shift_id: number;
  shift_name: string;
}
export interface AttendanceAnalyticsRead {
  date_from: string;
  date_to: string;
  team_id: number | null;
  shift_id: number | null;
  summary: AttendanceAnalyticsCounts;
  daily_trend: AttendanceAnalyticsDailyItem[];
  teams: AttendanceAnalyticsTeamItem[];
  shifts: AttendanceAnalyticsShiftItem[];
  employees: AttendanceAnalyticsEmployeeItem[];
}


export type AttendanceMonthlyDayStatus =
  | "present"
  | "absent"
  | "on_leave"
  | "weekly_holiday"
  | "not_recorded";
export interface AttendanceMonthlySummary {
  days_in_month: number;
  recorded_days: number;
  not_recorded_days: number;
  working_day_records: number;
  present: number;
  absent: number;
  on_leave: number;
  weekly_holiday: number;
  attendance_rate: number;
}
export interface AttendanceMonthlyDay {
  attendance_date: string;
  weekday: string;
  status: AttendanceMonthlyDayStatus;
  is_recorded: boolean;
  record_id: number | null;
  note: string | null;
  team_name: string;
  shift_name: string;
  leave_id: number | null;
  leave_type: string | null;
  leave_reason: string | null;
  leave_from_date: string | null;
  leave_to_date: string | null;
  updated_at: string | null;
}
export interface AttendanceEmployeeMonthlyReport {
  employee_id: number;
  employee_code: string;
  full_name: string;
  designation: string;
  team_id: number;
  team_name: string;
  shift_id: number;
  shift_name: string;
  year: number;
  month: number;
  month_label: string;
  summary: AttendanceMonthlySummary;
  days: AttendanceMonthlyDay[];
}
