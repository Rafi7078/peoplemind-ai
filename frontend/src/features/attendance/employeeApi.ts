import { apiClient } from "../../api/client";
import type {
  AttendanceStatus,
  DailyAttendanceRoster,
  DailyAttendanceSubmission,
} from "./types";
export type AttendanceAllowedShift = {
  id: number;
  name: string;
};
export type AttendanceSubmissionAudit = {
  id: number;
  attendance_date: string;
  team_id: number;
  shift_id: number;
  submitted_by_user_id: number;
  submitted_account_email: string;
  submitted_by_employee_id:
    number | null;
  submitted_by_employee_code:
    string | null;
  submitted_by_employee_name:
    string | null;
  submitted_at: string;
  last_updated_by_user_id: number;
  last_updated_account_email:
    string;
  last_updated_at: string;
};
export type AttendanceAccountRoster =
  DailyAttendanceRoster & {
    submission_audit:
      AttendanceSubmissionAudit | null;
  };
export type DailyAttendanceAccess = {
  role: "admin" | "attendance";
  is_admin: boolean;
  team_id: number | null;
  team_name: string | null;
  shift_id: number | null;
  shift_name: string | null;
  scope_type:
    | "admin"
    | "team"
    | "team_shift";
  allowed_shifts:
    AttendanceAllowedShift[];
};
export type AttendanceAccountSubmitPayload = {
  attendance_date: string;
  team_id: number;
  shift_id: number;
  submitted_by_employee_id: number;
  entries: Array<{
    employee_id: number;
    status: AttendanceStatus;
    note: string | null;
  }>;
};
export async function loadDailyAttendanceAccess():
Promise<DailyAttendanceAccess> {
  const response =
    await apiClient.get<DailyAttendanceAccess>(
      "/api/attendance/daily/access",
    );
  return response.data;
}
export async function loadAttendanceAccountRoster(
  attendanceDate: string,
  teamId: number,
  shiftId: number,
): Promise<AttendanceAccountRoster> {
  const response =
    await apiClient.get<AttendanceAccountRoster>(
      "/api/attendance/daily/roster",
      {
        params: {
          attendance_date:
            attendanceDate,
          team_id: teamId,
          shift_id: shiftId,
        },
      },
    );
  return response.data;
}
export async function submitAttendanceAccountRoster(
  payload: AttendanceAccountSubmitPayload,
): Promise<DailyAttendanceSubmission> {
  const response =
    await apiClient.post<DailyAttendanceSubmission>(
      "/api/attendance/daily",
      payload,
    );
  return response.data;
}
