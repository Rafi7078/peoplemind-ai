
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
