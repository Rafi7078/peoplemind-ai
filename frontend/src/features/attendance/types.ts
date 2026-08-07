
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
