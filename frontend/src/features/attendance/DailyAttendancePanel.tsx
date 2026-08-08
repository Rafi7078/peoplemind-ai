import axios from "axios";
import {
  useMemo,
  useState,
} from "react";
import {
  loadDailyAttendanceRoster,
  submitDailyAttendance,
} from "./api";
import type {
  AttendanceShift,
  AttendanceStatus,
  AttendanceTeam,
  DailyAttendanceEntry,
  DailyAttendanceRoster,
  DailyAttendanceSummary,
} from "./types";
type Props = {
  teams: AttendanceTeam[];
  shifts: AttendanceShift[];
};
type EditableEntry = {
  status: AttendanceStatus;
  note: string;
};
const statusOptions: Array<{
  value: AttendanceStatus;
  label: string;
}> = [
  {
    value: "present",
    label: "Present",
  },
  {
    value: "absent",
    label: "Absent",
  },
  {
    value: "on_leave",
    label: "On Leave",
  },
  {
    value: "weekly_holiday",
    label: "Weekly Holiday",
  },
];
function getLocalDateString(): string {
  const now = new Date();
  const localTime = new Date(
    now.getTime()
    - now.getTimezoneOffset()
      * 60_000,
  );
  return localTime
    .toISOString()
    .slice(0, 10);
}
function getApiErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (axios.isAxiosError(error)) {
    const detail =
      error.response?.data?.detail;
    if (
      typeof detail === "string"
      && detail.trim()
    ) {
      return detail;
    }
  }
  return fallback;
}
function statusClass(
  status: AttendanceStatus,
): string {
  switch (status) {
    case "present":
      return (
        "bg-emerald-100 text-emerald-700"
      );
    case "absent":
      return (
        "bg-red-100 text-red-700"
      );
    case "on_leave":
      return (
        "bg-amber-100 text-amber-700"
      );
    case "weekly_holiday":
      return (
        "bg-sky-100 text-sky-700"
      );
  }
}
export function DailyAttendancePanel({
  teams,
  shifts,
}: Props) {
  const [
    attendanceDate,
    setAttendanceDate,
  ] = useState(
    getLocalDateString(),
  );
  const [
    teamId,
    setTeamId,
  ] = useState("");
  const [
    shiftId,
    setShiftId,
  ] = useState("");
  const [
    roster,
    setRoster,
  ] = useState<
    DailyAttendanceRoster | null
  >(null);
  const [
    entries,
    setEntries,
  ] = useState<
    Record<number, EditableEntry>
  >({});
  const [
    isLoading,
    setIsLoading,
  ] = useState(false);
  const [
    isSaving,
    setIsSaving,
  ] = useState(false);
  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );
  const [
    activityMessage,
    setActivityMessage,
  ] = useState<string | null>(
    null,
  );
  const activeTeams =
    useMemo(
      () =>
        teams.filter(
          (team) =>
            team.status === "active",
        ),
      [teams],
    );
  const activeShifts =
    useMemo(
      () =>
        shifts.filter(
          (shift) =>
            shift.status === "active",
        ),
      [shifts],
    );
  const summary =
    useMemo<
      DailyAttendanceSummary
    >(
      () => {
        const result:
          DailyAttendanceSummary = {
            total_members:
              roster?.items.length
              ?? 0,
            present: 0,
            absent: 0,
            on_leave: 0,
            weekly_holiday: 0,
          };
        if (!roster) {
          return result;
        }
        for (
          const employee
          of roster.items
        ) {
          const status =
            entries[
              employee.employee_id
            ]?.status;
          if (status) {
            result[status] += 1;
          }
        }
        return result;
      },
      [
        entries,
        roster,
      ],
    );
  function clearMessages(): void {
    setErrorMessage(null);
    setActivityMessage(null);
  }
  function clearRoster(): void {
    setRoster(null);
    setEntries({});
    clearMessages();
  }
  async function handleLoadRoster():
    Promise<void> {
    clearMessages();
    const selectedTeamId =
      Number(teamId);
    const selectedShiftId =
      Number(shiftId);
    if (!attendanceDate) {
      setErrorMessage(
        "Select an attendance date.",
      );
      return;
    }
    if (
      !Number.isFinite(
        selectedTeamId,
      )
      || selectedTeamId <= 0
    ) {
      setErrorMessage(
        "Select a team.",
      );
      return;
    }
    if (
      !Number.isFinite(
        selectedShiftId,
      )
      || selectedShiftId <= 0
    ) {
      setErrorMessage(
        "Select a shift.",
      );
      return;
    }
    setIsLoading(true);
    try {
      const result =
        await loadDailyAttendanceRoster(
          attendanceDate,
          selectedTeamId,
          selectedShiftId,
        );
      const nextEntries:
        Record<
          number,
          EditableEntry
        > = {};
      for (
        const employee
        of result.items
      ) {
        nextEntries[
          employee.employee_id
        ] = {
          status:
            employee.saved_status
            ?? employee
              .suggested_status,
          note:
            employee.note
            ?? "",
        };
      }
      setRoster(result);
      setEntries(nextEntries);
      if (
        result.total_members === 0
      ) {
        setActivityMessage(
          "No active employee is assigned to this team and shift.",
        );
      } else {
        setActivityMessage(
          `Loaded ${result.total_members} employee(s).`,
        );
      }
    } catch (error) {
      setRoster(null);
      setEntries({});
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not load the daily roster.",
        ),
      );
    } finally {
      setIsLoading(false);
    }
  }
  function updateStatus(
    employeeId: number,
    status: AttendanceStatus,
  ): void {
    setEntries(
      (current) => ({
        ...current,
        [employeeId]: {
          status,
          note:
            current[
              employeeId
            ]?.note
            ?? "",
        },
      }),
    );
  }
  function updateNote(
    employeeId: number,
    note: string,
  ): void {
    setEntries(
      (current) => ({
        ...current,
        [employeeId]: {
          status:
            current[
              employeeId
            ]?.status
            ?? "present",
          note,
        },
      }),
    );
  }
  function applySuggestedStatuses():
    void {
    if (!roster) {
      return;
    }
    const nextEntries:
      Record<
        number,
        EditableEntry
      > = {};
    for (
      const employee
      of roster.items
    ) {
      nextEntries[
        employee.employee_id
      ] = {
        status:
          employee
            .suggested_status,
        note:
          entries[
            employee.employee_id
          ]?.note
          ?? "",
      };
    }
    setEntries(nextEntries);
    setActivityMessage(
      "Suggested statuses applied.",
    );
  }
  function markWorkingMembersPresent():
    void {
    if (!roster) {
      return;
    }
    setEntries(
      (current) => {
        const next = {
          ...current,
        };
        for (
          const employee
          of roster.items
        ) {
          if (
            employee
              .suggested_status
            === "weekly_holiday"
          ) {
            continue;
          }
          next[
            employee.employee_id
          ] = {
            status: "present",
            note:
              next[
                employee.employee_id
              ]?.note
              ?? "",
          };
        }
        return next;
      },
    );
    setActivityMessage(
      "Working members marked Present. Weekly holidays were preserved.",
    );
  }
  async function handleSubmit():
    Promise<void> {
    if (
      !roster
      || roster.items.length === 0
    ) {
      return;
    }
    clearMessages();
    const submissionEntries:
      DailyAttendanceEntry[] =
        roster.items.map(
          (employee) => ({
            employee_id:
              employee.employee_id,
            status:
              entries[
                employee.employee_id
              ]?.status
              ?? employee
                .suggested_status,
            note:
              entries[
                employee.employee_id
              ]?.note.trim()
              || null,
          }),
        );
    setIsSaving(true);
    try {
      const result =
        await submitDailyAttendance(
          {
            attendance_date:
              roster
                .attendance_date,
            team_id:
              roster.team_id,
            shift_id:
              roster.shift_id,
            entries:
              submissionEntries,
          },
        );
      setActivityMessage(
        `Attendance saved. Present ${result.summary.present}, ` +
        `Absent ${result.summary.absent}, ` +
        `On Leave ${result.summary.on_leave}, ` +
        `Weekly Holiday ${result.summary.weekly_holiday}.`,
      );
      await handleLoadRoster();
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not save daily attendance.",
        ),
      );
    } finally {
      setIsSaving(false);
    }
  }
  return (
    <section className="mt-8">
      <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-emerald-600">
            Daily roster
          </p>
          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Record Daily Attendance
          </h2>
          <p className="mt-2 max-w-3xl leading-6 text-slate-600">
            Select a date, team and shift.
            Weekly holidays are suggested from
            each employee profile, but HR can
            manually override every status.
          </p>
        </div>
        <div className="mt-7 grid gap-4 md:grid-cols-3">
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Date
            </span>
            <input
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setAttendanceDate(
                  event.target.value,
                );
                clearRoster();
              }}
              type="date"
              value={attendanceDate}
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Team
            </span>
            <select
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setTeamId(
                  event.target.value,
                );
                clearRoster();
              }}
              value={teamId}
            >
              <option value="">
                Select team
              </option>
              {activeTeams.map(
                (team) => (
                  <option
                    key={team.id}
                    value={team.id}
                  >
                    {team.name}
                  </option>
                ),
              )}
            </select>
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Shift
            </span>
            <select
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setShiftId(
                  event.target.value,
                );
                clearRoster();
              }}
              value={shiftId}
            >
              <option value="">
                Select shift
              </option>
              {activeShifts.map(
                (shift) => (
                  <option
                    key={shift.id}
                    value={shift.id}
                  >
                    {shift.name}
                  </option>
                ),
              )}
            </select>
          </label>
        </div>
        <div className="mt-5">
          <button
            className="rounded-xl bg-slate-950 px-6 py-3 font-semibold text-white disabled:opacity-50"
            disabled={isLoading}
            onClick={() => {
              void handleLoadRoster();
            }}
            type="button"
          >
            {isLoading
              ? "Loading roster..."
              : "Load roster"}
          </button>
        </div>
      </article>
      {errorMessage ? (
        <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {errorMessage}
        </div>
      ) : null}
      {activityMessage ? (
        <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-semibold text-emerald-700">
          {activityMessage}
        </div>
      ) : null}
      {roster ? (
        <>
          <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {[
              {
                label:
                  "Team members",
                value:
                  summary.total_members,
              },
              {
                label: "Present",
                value:
                  summary.present,
              },
              {
                label: "Absent",
                value:
                  summary.absent,
              },
              {
                label: "On Leave",
                value:
                  summary.on_leave,
              },
              {
                label:
                  "Weekly Holiday",
                value:
                  summary.weekly_holiday,
              },
            ].map((item) => (
              <article
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                key={item.label}
              >
                <p className="text-sm font-semibold text-slate-500">
                  {item.label}
                </p>
                <p className="mt-2 text-3xl font-bold text-slate-950">
                  {item.value}
                </p>
              </article>
            ))}
          </section>
          <article className="mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-950">
                  {roster.team_name}
                  {" | "}
                  {roster.shift_name}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {roster.attendance_date}
                  {" | "}
                  {roster.total_members}
                  {" "}member(s)
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  className="rounded-xl border border-sky-300 px-4 py-2 text-sm font-semibold text-sky-700"
                  onClick={
                    applySuggestedStatuses
                  }
                  type="button"
                >
                  Apply suggestions
                </button>
                <button
                  className="rounded-xl border border-emerald-300 px-4 py-2 text-sm font-semibold text-emerald-700"
                  onClick={
                    markWorkingMembersPresent
                  }
                  type="button"
                >
                  Mark working members Present
                </button>
              </div>
            </div>
            {roster.items.length === 0 ? (
              <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                No active employee is assigned
                to this team and shift.
              </div>
            ) : (
              <div className="mt-6 overflow-x-auto">
                <table className="min-w-full border-separate border-spacing-0">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                      <th className="border-b border-slate-200 px-4 py-3">
                        Employee
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Suggested
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Attendance
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Note
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {roster.items.map(
                      (employee) => {
                        const entry =
                          entries[
                            employee
                              .employee_id
                          ];
                        return (
                          <tr
                            className="align-top"
                            key={
                              employee.employee_id
                            }
                          >
                            <td className="border-b border-slate-100 px-4 py-4">
                              <p className="font-bold text-slate-900">
                                {employee.full_name}
                              </p>
                              <p className="mt-1 text-xs text-slate-500">
                                {employee.employee_code}
                                {" | "}
                                {employee.designation}
                              </p>
                            </td>
                            <td className="border-b border-slate-100 px-4 py-4">
                              <span
                                className={[
                                  "inline-flex rounded-full px-2.5 py-1 text-xs font-bold",
                                  statusClass(
                                    employee
                                      .suggested_status,
                                  ),
                                ].join(" ")}
                              >
                                {
                                  statusOptions.find(
                                    (option) =>
                                      option.value
                                      === employee
                                        .suggested_status,
                                  )?.label
                                }
                              </span>
                            </td>
                            <td className="border-b border-slate-100 px-4 py-4">
                              <select
                                className="min-w-44 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold"
                                onChange={(event) => {
                                  updateStatus(
                                    employee
                                      .employee_id,
                                    (event.target.value as AttendanceStatus),
                                  );
                                }}
                                value={
                                  entry?.status
                                  ?? employee
                                    .suggested_status
                                }
                              >
                                {statusOptions.map(
                                  (option) => (
                                    <option
                                      key={
                                        option.value
                                      }
                                      value={
                                        option.value
                                      }
                                    >
                                      {option.label}
                                    </option>
                                  ),
                                )}
                              </select>
                              {employee.saved_status ? (
                                <p className="mt-2 text-xs font-semibold text-violet-600">
                                  Previously saved
                                </p>
                              ) : null}
                            </td>
                            <td className="border-b border-slate-100 px-4 py-4">
                              <input
                                className="min-w-56 rounded-xl border border-slate-300 px-3 py-2 text-sm"
                                maxLength={500}
                                onChange={(event) => {
                                  updateNote(
                                    employee
                                      .employee_id,
                                    event.target
                                      .value,
                                  );
                                }}
                                placeholder="Optional note"
                                value={
                                  entry?.note
                                  ?? ""
                                }
                              />
                            </td>
                          </tr>
                        );
                      },
                    )}
                  </tbody>
                </table>
              </div>
            )}
            {roster.items.length > 0 ? (
              <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-6">
                <p className="text-sm leading-6 text-slate-500">
                  Re-submitting this date updates
                  existing attendance records.
                  It does not create duplicates.
                </p>
                <button
                  className="rounded-xl bg-emerald-600 px-6 py-3 font-bold text-white disabled:opacity-50"
                  disabled={isSaving}
                  onClick={() => {
                    void handleSubmit();
                  }}
                  type="button"
                >
                  {isSaving
                    ? "Saving attendance..."
                    : "Submit attendance"}
                </button>
              </div>
            ) : null}
          </article>
        </>
      ) : null}
    </section>
  );
}
