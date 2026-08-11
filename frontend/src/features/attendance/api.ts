
import {
  apiClient,
} from "../../api/client";
import type {
  AttendanceEmployee,
  AttendanceEmployeeCreate,
  AttendanceEmployeeUpdate,
  AttendanceShift,
  AttendanceShiftCreate,
  AttendanceShiftUpdate,
  AttendanceTeam,
  AttendanceTeamCreate,
  AttendanceTeamUpdate,
} from "./types";
export async function listAttendanceTeams():
  Promise<AttendanceTeam[]> {
  const response =
    await apiClient.get<
      AttendanceTeam[]
    >(
      "/api/attendance/teams",
    );
  return response.data;
}
export async function createAttendanceTeam(
  payload: AttendanceTeamCreate,
): Promise<AttendanceTeam> {
  const response =
    await apiClient.post<
      AttendanceTeam
    >(
      "/api/attendance/teams",
      payload,
    );
  return response.data;
}
export async function updateAttendanceTeam(
  teamId: number,
  payload: AttendanceTeamUpdate,
): Promise<AttendanceTeam> {
  const response =
    await apiClient.patch<
      AttendanceTeam
    >(
      `/api/attendance/teams/${teamId}`,
      payload,
    );
  return response.data;
}
export async function deleteAttendanceTeam(
  teamId: number,
): Promise<void> {
  await apiClient.delete(
    `/api/attendance/teams/${teamId}`,
  );
}
export async function listAttendanceShifts():
  Promise<AttendanceShift[]> {
  const response =
    await apiClient.get<
      AttendanceShift[]
    >(
      "/api/attendance/shifts",
    );
  return response.data;
}
export async function createAttendanceShift(
  payload: AttendanceShiftCreate,
): Promise<AttendanceShift> {
  const response =
    await apiClient.post<
      AttendanceShift
    >(
      "/api/attendance/shifts",
      payload,
    );
  return response.data;
}
export async function updateAttendanceShift(
  shiftId: number,
  payload: AttendanceShiftUpdate,
): Promise<AttendanceShift> {
  const response =
    await apiClient.patch<
      AttendanceShift
    >(
      `/api/attendance/shifts/${shiftId}`,
      payload,
    );
  return response.data;
}
export async function deleteAttendanceShift(
  shiftId: number,
): Promise<void> {
  await apiClient.delete(
    `/api/attendance/shifts/${shiftId}`,
  );
}
export async function listAttendanceEmployees():
  Promise<AttendanceEmployee[]> {
  const response =
    await apiClient.get<
      AttendanceEmployee[]
    >(
      "/api/attendance/employees",
    );
  return response.data;
}
export async function createAttendanceEmployee(
  payload: AttendanceEmployeeCreate,
): Promise<AttendanceEmployee> {
  const response =
    await apiClient.post<
      AttendanceEmployee
    >(
      "/api/attendance/employees",
      payload,
    );
  return response.data;
}
export async function updateAttendanceEmployee(
  employeeId: number,
  payload: AttendanceEmployeeUpdate,
): Promise<AttendanceEmployee> {
  const response =
    await apiClient.patch<
      AttendanceEmployee
    >(
      `/api/attendance/employees/${employeeId}`,
      payload,
    );
  return response.data;
}
export async function deleteAttendanceEmployee(
  employeeId: number,
): Promise<void> {
  await apiClient.delete(
    `/api/attendance/employees/${employeeId}`,
  );
}


export async function loadDailyAttendanceRoster(
  attendanceDate: string,
  teamId: number,
  shiftId: number,
): Promise<
  import("./types").DailyAttendanceRoster
> {
  const response =
    await apiClient.get<
      import("./types").DailyAttendanceRoster
    >(
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
export async function submitDailyAttendance(
  payload:
    import("./types").DailyAttendanceSubmit,
): Promise<
  import("./types").DailyAttendanceSubmission
> {
  const response =
    await apiClient.post<
      import("./types").DailyAttendanceSubmission
    >(
      "/api/attendance/daily",
      payload,
    );
  return response.data;
}


export async function loadAttendanceHistory(
  filters?: {
    dateFrom?: string;
    dateTo?: string;
    teamId?: number;
    shiftId?: number;
  },
): Promise<
  import("./types").AttendanceHistoryList
> {
  const response =
    await apiClient.get<
      import("./types").AttendanceHistoryList
    >(
      "/api/attendance/history",
      {
        params: {
          date_from:
            filters?.dateFrom
            || undefined,
          date_to:
            filters?.dateTo
            || undefined,
          team_id:
            filters?.teamId
            || undefined,
          shift_id:
            filters?.shiftId
            || undefined,
        },
      },
    );
  return response.data;
}
export async function loadAttendanceHistoryReport(
  attendanceDate: string,
  teamId: number,
  shiftId: number,
): Promise<
  import("./types").AttendanceHistoryReport
> {
  const response =
    await apiClient.get<
      import("./types").AttendanceHistoryReport
    >(
      "/api/attendance/history/report",
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


export async function loadAttendanceLeaves(
  filters?: {
    employeeId?: number;
    status?: import("./types").LeaveStatus;
    dateFrom?: string;
    dateTo?: string;
  },
): Promise<
  import("./types").AttendanceLeaveList
> {
  const response =
    await apiClient.get<
      import("./types").AttendanceLeaveList
    >(
      "/api/attendance/leaves",
      {
        params: {
          employee_id:
            filters?.employeeId
            || undefined,
          status:
            filters?.status
            || undefined,
          date_from:
            filters?.dateFrom
            || undefined,
          date_to:
            filters?.dateTo
            || undefined,
        },
      },
    );
  return response.data;
}
export async function createAttendanceLeave(
  payload:
    import("./types").AttendanceLeaveCreate,
): Promise<
  import("./types").AttendanceLeave
> {
  const response =
    await apiClient.post<
      import("./types").AttendanceLeave
    >(
      "/api/attendance/leaves",
      payload,
    );
  return response.data;
}
export async function updateAttendanceLeave(
  leaveId: number,
  payload: Partial<{
    leave_type:
      import("./types").LeaveType;
    from_date: string;
    to_date: string;
    reason: string | null;
    status:
      import("./types").LeaveStatus;
  }>,
): Promise<
  import("./types").AttendanceLeave
> {
  const response =
    await apiClient.patch<
      import("./types").AttendanceLeave
    >(
      `/api/attendance/leaves/${leaveId}`,
      payload,
    );
  return response.data;
}


export async function downloadAttendanceHistoryCsv(
  attendanceDate: string,
  teamId: number,
  shiftId: number,
): Promise<Blob> {
  const response =
    await apiClient.get<Blob>(
      "/api/attendance/history/report.csv",
      {
        params: {
          attendance_date:
            attendanceDate,
          team_id: teamId,
          shift_id: shiftId,
        },
        responseType: "blob",
      },
    );
  return response.data;
}

export async function downloadAttendanceHistoryPdf(
  attendanceDate: string,
  teamId: number,
  shiftId: number,
): Promise<Blob> {
  const response =
    await apiClient.get<Blob>(
      "/api/attendance/history/report.pdf",
      {
        params: {
          attendance_date:
            attendanceDate,
          team_id: teamId,
          shift_id: shiftId,
        },
        responseType: "blob",
      },
    );
  return response.data;
}

export async function loadAttendanceAnalytics(
  dateFrom: string,
  dateTo: string,
  teamId?: number,
  shiftId?: number,
): Promise<
  import("./types").AttendanceAnalyticsRead
> {
  const response =
    await apiClient.get<
      import("./types").AttendanceAnalyticsRead
    >(
      "/api/attendance/analytics",
      {
        params: {
          date_from: dateFrom,
          date_to: dateTo,
          team_id: teamId,
          shift_id: shiftId,
        },
      },
    );
  return response.data;
}


export async function loadEmployeeMonthlyReport(
  employeeId: number,
  year: number,
  month: number,
): Promise<
  import("./types").AttendanceEmployeeMonthlyReport
> {
  const response =
    await apiClient.get<
      import("./types").AttendanceEmployeeMonthlyReport
    >(
      `/api/attendance/employees/${employeeId}/monthly-report`,
      {
        params: {
          year,
          month,
        },
      },
    );
  return response.data;
}


export async function downloadEmployeeMonthlyCsv(
  employeeId: number,
  year: number,
  month: number,
): Promise<Blob> {
  const response =
    await apiClient.get<Blob>(
      `/api/attendance/employees/${employeeId}/monthly-report.csv`,
      {
        params: {
          year,
          month,
        },
        responseType: "blob",
      },
    );
  return response.data;
}
export async function downloadEmployeeMonthlyPdf(
  employeeId: number,
  year: number,
  month: number,
): Promise<Blob> {
  const response =
    await apiClient.get<Blob>(
      `/api/attendance/employees/${employeeId}/monthly-report.pdf`,
      {
        params: {
          year,
          month,
        },
        responseType: "blob",
      },
    );
  return response.data;
}
