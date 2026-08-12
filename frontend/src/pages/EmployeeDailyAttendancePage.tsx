import axios from "axios";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  loadAttendanceAccountRoster,
  loadDailyAttendanceAccess,
  submitAttendanceAccountRoster,
} from "../features/attendance/employeeApi";
import type {
  AttendanceAccountRoster,
  DailyAttendanceAccess,
} from "../features/attendance/employeeApi";
import type {
  AttendanceStatus,
} from "../features/attendance/types";
type AttendanceEntry = {
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
function todayValue(): string {
  const now = new Date();
  const localDate = new Date(
    now.getTime()
    - now.getTimezoneOffset() * 60_000,
  );
  return localDate
    .toISOString()
    .slice(0, 10);
}
function statusClass(
  status: AttendanceStatus,
): string {
  switch (status) {
    case "present":
      return "bg-emerald-100 text-emerald-700";
    case "absent":
      return "bg-red-100 text-red-700";
    case "on_leave":
      return "bg-amber-100 text-amber-700";
    case "weekly_holiday":
      return "bg-sky-100 text-sky-700";
  }
}
function formatStatus(
  status: AttendanceStatus,
): string {
  return (
    statusOptions.find(
      (option) =>
        option.value === status,
    )?.label ?? status
  );
}
function formatLeaveType(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}
function formatAuditDateTime(
  value: string,
): string {
  const normalizedValue =
    value.endsWith("Z")
    || /[+-]\d{2}:\d{2}$/.test(value)
      ? value
      : `${value}Z`;
  return new Date(
    normalizedValue,
  ).toLocaleString();
}
function getApiErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }
  if (!error.response) {
    return (
      "Backend server is not reachable. "
      + "Confirm that FastAPI is running."
    );
  }
  const detail =
    error.response.data?.detail;
  if (
    typeof detail === "string"
    && detail.trim()
  ) {
    return detail;
  }
  return fallback;
}
export function EmployeeDailyAttendancePage() {
  const [
    access,
    setAccess,
  ] = useState<
    DailyAttendanceAccess | null
  >(null);
  const [
    attendanceDate,
    setAttendanceDate,
  ] = useState(
    todayValue,
  );
  const [
    selectedShiftId,
    setSelectedShiftId,
  ] = useState("");
  const [
    selectedSubmitterId,
    setSelectedSubmitterId,
  ] = useState("");
  const [
    roster,
    setRoster,
  ] = useState<
    AttendanceAccountRoster | null
  >(null);
  const [
    entries,
    setEntries,
  ] = useState<
    Record<number, AttendanceEntry>
  >({});
  const [
    isInitialLoading,
    setIsInitialLoading,
  ] = useState(true);
  const [
    isRosterLoading,
    setIsRosterLoading,
  ] = useState(false);
  const [
    isSaving,
    setIsSaving,
  ] = useState(false);
  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");
  const [
    activityMessage,
    setActivityMessage,
  ] = useState("");
  function hydrateRoster(
    result: AttendanceAccountRoster,
  ): void {
    const nextEntries: Record<
      number,
      AttendanceEntry
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
          ?? employee.suggested_status,
        note:
          employee.note
          ?? "",
      };
    }
    setRoster(result);
    setEntries(nextEntries);
    if (
      result.submission_audit
        ?.submitted_by_employee_id
    ) {
      setSelectedSubmitterId(
        String(
          result.submission_audit
            .submitted_by_employee_id,
        ),
      );
    } else {
      setSelectedSubmitterId("");
    }
  }
  useEffect(() => {
    document.title =
      "Daily Attendance | PeopleMind AI";
    let isActive = true;
    async function bootstrap():
    Promise<void> {
      try {
        const result =
          await loadDailyAttendanceAccess();
        if (!isActive) {
          return;
        }
        if (
          result.role !== "attendance"
          || result.team_id === null
        ) {
          setErrorMessage(
            "This account does not have "
            + "attendance access.",
          );
          return;
        }
        setAccess(result);
        let initialShiftId = "";
        if (
          result.scope_type
          === "team_shift"
          && result.shift_id !== null
        ) {
          initialShiftId =
            String(result.shift_id);
        } else if (
          result.allowed_shifts.length
          === 1
        ) {
          initialShiftId =
            String(
              result.allowed_shifts[0].id,
            );
        }
        setSelectedShiftId(
          initialShiftId,
        );
        if (initialShiftId) {
          const rosterResult =
            await loadAttendanceAccountRoster(
              todayValue(),
              result.team_id,
              Number(initialShiftId),
            );
          if (!isActive) {
            return;
          }
          hydrateRoster(
            rosterResult,
          );
        }
      } catch (error) {
        if (!isActive) {
          return;
        }
        setErrorMessage(
          getApiErrorMessage(
            error,
            "Could not load attendance access.",
          ),
        );
      } finally {
        if (isActive) {
          setIsInitialLoading(false);
        }
      }
    }
    void bootstrap();
    return () => {
      isActive = false;
    };
  }, []);
  const isLocked = useMemo(
    () =>
      roster?.items.some(
        (employee) =>
          employee.saved_status
          !== null,
      ) ?? false,
    [roster],
  );
  const selectedShiftName =
    access?.allowed_shifts.find(
      (shift) =>
        String(shift.id)
        === selectedShiftId,
    )?.name
    ?? access?.shift_name
    ?? "";
  const summary = useMemo(() => {
    const result = {
      total_members:
        roster?.items.length ?? 0,
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
        ]?.status
        ?? employee.saved_status
        ?? employee.suggested_status;
      result[status] += 1;
    }
    return result;
  }, [
    entries,
    roster,
  ]);
  async function handleLoadRoster():
  Promise<void> {
    if (
      !access
      || access.team_id === null
      || !selectedShiftId
    ) {
      setErrorMessage(
        "Select a shift before loading "
        + "the roster.",
      );
      return;
    }
    setErrorMessage("");
    setActivityMessage("");
    setIsRosterLoading(true);
    try {
      const result =
        await loadAttendanceAccountRoster(
          attendanceDate,
          access.team_id,
          Number(selectedShiftId),
        );
      hydrateRoster(result);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not load the attendance roster.",
        ),
      );
    } finally {
      setIsRosterLoading(false);
    }
  }
  function updateStatus(
    employeeId: number,
    status: AttendanceStatus,
  ): void {
    if (isLocked) {
      return;
    }
    setEntries(
      (current) => ({
        ...current,
        [employeeId]: {
          status,
          note:
            current[
              employeeId
            ]?.note ?? "",
        },
      }),
    );
  }
  function updateNote(
    employeeId: number,
    note: string,
  ): void {
    if (isLocked) {
      return;
    }
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
    if (
      !roster
      || isLocked
    ) {
      return;
    }
    const nextEntries: Record<
      number,
      AttendanceEntry
    > = {};
    for (
      const employee
      of roster.items
    ) {
      nextEntries[
        employee.employee_id
      ] = {
        status:
          employee.suggested_status,
        note:
          entries[
            employee.employee_id
          ]?.note ?? "",
      };
    }
    setEntries(nextEntries);
  }
  function markWorkingMembersPresent():
  void {
    if (
      !roster
      || isLocked
    ) {
      return;
    }
    const nextEntries: Record<
      number,
      AttendanceEntry
    > = {};
    for (
      const employee
      of roster.items
    ) {
      const keepSuggestion =
        employee.suggested_status
        === "weekly_holiday"
        || employee.suggested_status
        === "on_leave";
      nextEntries[
        employee.employee_id
      ] = {
        status:
          keepSuggestion
            ? employee.suggested_status
            : "present",
        note:
          entries[
            employee.employee_id
          ]?.note ?? "",
      };
    }
    setEntries(nextEntries);
  }
  async function handleSubmit():
  Promise<void> {
    if (
      !access
      || access.team_id === null
      || !selectedShiftId
      || !selectedSubmitterId
      || !roster
      || isLocked
    ) {
      return;
    }
    setErrorMessage("");
    setActivityMessage("");
    setIsSaving(true);
    try {
      const result =
        await submitAttendanceAccountRoster(
          {
            attendance_date:
              roster.attendance_date,
            team_id:
              access.team_id,
            shift_id:
              Number(
                selectedShiftId,
              ),
            submitted_by_employee_id:
              Number(
                selectedSubmitterId,
              ),
            entries:
              roster.items.map(
                (employee) => {
                  const entry =
                    entries[
                      employee.employee_id
                    ];
                  const cleanNote =
                    entry?.note.trim()
                    ?? "";
                  return {
                    employee_id:
                      employee.employee_id,
                    status:
                      entry?.status
                      ?? employee
                        .suggested_status,
                    note:
                      cleanNote
                        ? cleanNote
                        : null,
                  };
                },
              ),
          },
        );
      setActivityMessage(
        "Attendance submitted successfully. "
        + `Present ${result.summary.present}, `
        + `Absent ${result.summary.absent}, `
        + `On Leave ${result.summary.on_leave}, `
        + "Weekly Holiday "
        + `${result.summary.weekly_holiday}.`,
      );
      const refreshed =
        await loadAttendanceAccountRoster(
          roster.attendance_date,
          access.team_id,
          Number(selectedShiftId),
        );
      hydrateRoster(refreshed);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not submit attendance.",
        ),
      );
    } finally {
      setIsSaving(false);
    }
  }
  if (isInitialLoading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="font-semibold text-slate-700">
            Loading attendance access...
          </p>
        </div>
      </main>
    );
  }
  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <section className="overflow-hidden rounded-3xl bg-slate-950 px-8 py-9 text-white shadow-xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">
          Attendance workspace
        </p>
        <h1 className="mt-4 text-3xl font-bold md:text-5xl">
          Daily Attendance
        </h1>
        <p className="mt-5 max-w-3xl leading-7 text-slate-300">
          Record attendance only for the
          team and shift assigned to this
          account. After submission, employee
          editing is locked and HR/Admin can
          make corrections.
        </p>
        {access ? (
          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-full bg-emerald-400/15 px-4 py-2 text-sm font-semibold text-emerald-300">
              Team: {access.team_name}
            </span>
            {access.scope_type
            === "team_shift" ? (
              <span className="rounded-full bg-sky-400/15 px-4 py-2 text-sm font-semibold text-sky-300">
                Shift: {access.shift_name}
              </span>
            ) : (
              <span className="rounded-full bg-sky-400/15 px-4 py-2 text-sm font-semibold text-sky-300">
                Team-level shift access
              </span>
            )}
            <span className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-slate-200">
              Attendance Account
            </span>
          </div>
        ) : null}
      </section>
      {errorMessage ? (
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {errorMessage}
        </div>
      ) : null}
      {activityMessage ? (
        <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-semibold text-emerald-700">
          {activityMessage}
        </div>
      ) : null}
      {access ? (
        <section className="mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
          <div className="grid gap-4 md:grid-cols-3">
            <label>
              <span className="text-sm font-semibold text-slate-700">
                Attendance Date
              </span>
              <input
                className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                onChange={(event) => {
                  setAttendanceDate(
                    event.target.value,
                  );
                  setRoster(null);
                  setEntries({});
                  setSelectedSubmitterId("");
                  setActivityMessage("");
                }}
                type="date"
                value={attendanceDate}
              />
            </label>
            <div>
              <p className="text-sm font-semibold text-slate-700">
                Assigned Team
              </p>
              <div className="mt-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-semibold text-slate-800">
                {access.team_name}
              </div>
            </div>
            {access.scope_type
            === "team_shift" ? (
              <div>
                <p className="text-sm font-semibold text-slate-700">
                  Assigned Shift
                </p>
                <div className="mt-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-semibold text-slate-800">
                  {access.shift_name}
                </div>
              </div>
            ) : (
              <label>
                <span className="text-sm font-semibold text-slate-700">
                  Shift
                </span>
                <select
                  className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                  onChange={(event) => {
                    setSelectedShiftId(
                      event.target.value,
                    );
                    setRoster(null);
                    setEntries({});
                    setActivityMessage("");
                  }}
                  value={
                    selectedShiftId
                  }
                >
                  <option value="">
                    Select shift
                  </option>
                  {access.allowed_shifts.map(
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
            )}
          </div>
          <button
            className="mt-5 rounded-xl bg-slate-950 px-6 py-3 font-semibold text-white disabled:opacity-50"
            disabled={
              isRosterLoading
              || !selectedShiftId
            }
            onClick={() => {
              void handleLoadRoster();
            }}
            type="button"
          >
            {isRosterLoading
              ? "Loading roster..."
              : "Load roster"}
          </button>
        </section>
      ) : null}
      {roster ? (
        <>
          {!isLocked
          && roster.items.length > 0 ? (
            <section className="mt-7 rounded-3xl border border-violet-200 bg-violet-50 p-6 shadow-sm">
              <div className="max-w-xl">
                <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
                  Submission audit
                </p>
                <h2 className="mt-2 text-xl font-bold text-slate-950">
                  Who is submitting attendance?
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Select the employee who is
                  physically submitting this
                  roster using the shared
                  attendance account.
                </p>
                <label className="mt-5 block">
                  <span className="text-sm font-bold text-slate-700">
                    Submitted By
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-violet-300 bg-white px-4 py-3 font-semibold text-slate-800"
                    onChange={(event) => {
                      setSelectedSubmitterId(
                        event.target.value,
                      );
                    }}
                    value={
                      selectedSubmitterId
                    }
                  >
                    <option value="">
                      Select employee
                    </option>
                    {roster.items.map(
                      (employee) => (
                        <option
                          key={
                            employee.employee_id
                          }
                          value={
                            employee.employee_id
                          }
                        >
                          {employee.employee_code}
                          {" - "}
                          {employee.full_name}
                        </option>
                      ),
                    )}
                  </select>
                </label>
              </div>
            </section>
          ) : null}
          {isLocked
          && roster.submission_audit ? (
            <section className="mt-7 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
                Submission audit
              </p>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Submitted By
                  </p>
                  <p className="mt-2 font-bold text-slate-900">
                    {roster.submission_audit
                      .submitted_by_employee_code
                      ? `${roster.submission_audit.submitted_by_employee_code} - ${roster.submission_audit.submitted_by_employee_name}`
                      : "HR/Admin"}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Account Used
                  </p>
                  <p className="mt-2 font-semibold text-slate-800">
                    {
                      roster.submission_audit
                        .submitted_account_email
                    }
                  </p>
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Submitted At
                  </p>
                  <p className="mt-2 font-semibold text-slate-800">
                    {formatAuditDateTime(
                      roster.submission_audit
                        .submitted_at,
                    )}
                  </p>
                </div>
              </div>
            </section>
          ) : null}
          {isLocked ? (
            <div className="mt-7 rounded-2xl border border-amber-200 bg-amber-50 px-6 py-5">
              <p className="font-bold text-amber-800">
                Attendance already submitted
              </p>
              <p className="mt-1 text-sm leading-6 text-amber-700">
                This roster is read-only for
                attendance accounts. HR/Admin
                can make corrections.
              </p>
            </div>
          ) : null}
          <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {[
              {
                label: "Team members",
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
                label: "Weekly Holiday",
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
          <section className="mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-950">
                  {roster.team_name}
                  {" | "}
                  {selectedShiftName}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {roster.attendance_date}
                  {" | "}
                  {roster.total_members}
                  {" "}member(s)
                </p>
              </div>
              {!isLocked ? (
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
                    Mark Working Present
                  </button>
                </div>
              ) : null}
            </div>
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
                          employee.employee_id
                        ];
                      const currentStatus =
                        entry?.status
                        ?? employee.saved_status
                        ?? employee
                          .suggested_status;
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
                              {formatStatus(
                                employee
                                  .suggested_status,
                              )}
                            </span>
                            {employee.approved_leave_id ? (
                              <div className="mt-2 max-w-64">
                                <p className="text-xs font-semibold text-amber-700">
                                  Approved{" "}
                                  {employee.approved_leave_type
                                    ? formatLeaveType(
                                        employee
                                          .approved_leave_type,
                                      )
                                    : "Leave"}
                                </p>
                                {employee.approved_leave_reason ? (
                                  <p className="mt-1 text-xs leading-5 text-slate-500">
                                    {
                                      employee
                                        .approved_leave_reason
                                    }
                                  </p>
                                ) : null}
                              </div>
                            ) : null}
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4">
                            {isLocked ? (
                              <span
                                className={[
                                  "inline-flex rounded-full px-3 py-1.5 text-sm font-bold",
                                  statusClass(
                                    currentStatus,
                                  ),
                                ].join(" ")}
                              >
                                {formatStatus(
                                  currentStatus,
                                )}
                              </span>
                            ) : (
                              <select
                                className="min-w-44 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold"
                                disabled={
                                  isSaving
                                }
                                onChange={(
                                  event,
                                ) => {
                                  updateStatus(
                                    employee
                                      .employee_id,
                                    event.target.value as AttendanceStatus,
                                  );
                                }}
                                value={
                                  currentStatus
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
                                      {
                                        option.label
                                      }
                                    </option>
                                  ),
                                )}
                              </select>
                            )}
                            {employee.saved_status ? (
                              <p className="mt-2 text-xs font-semibold text-violet-600">
                                Submitted
                              </p>
                            ) : null}
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4">
                            {isLocked ? (
                              <p className="min-w-56 text-sm leading-6 text-slate-600">
                                {entry?.note
                                  || "-"}
                              </p>
                            ) : (
                              <input
                                className="min-w-56 rounded-xl border border-slate-300 px-3 py-2 text-sm"
                                disabled={
                                  isSaving
                                }
                                maxLength={500}
                                onChange={(
                                  event,
                                ) => {
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
                            )}
                          </td>
                        </tr>
                      );
                    },
                  )}
                </tbody>
              </table>
            </div>
            {roster.items.length > 0 ? (
              <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-6">
                {isLocked ? (
                  <p className="text-sm font-semibold leading-6 text-amber-700">
                    Read-only after submission.
                    Contact HR/Admin for correction.
                  </p>
                ) : (
                  <>
                    <p className="max-w-2xl text-sm leading-6 text-slate-500">
                      Review the complete roster
                      before submitting. This
                      attendance account can submit
                      the selected roster only once.
                    </p>
                    <button
                      className="rounded-xl bg-emerald-600 px-6 py-3 font-bold text-white disabled:opacity-50"
                      disabled={
                        isSaving
                        || !selectedSubmitterId
                      }
                      onClick={() => {
                        void handleSubmit();
                      }}
                      type="button"
                    >
                      {isSaving
                        ? "Submitting..."
                        : "Submit Attendance"}
                    </button>
                  </>
                )}
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </main>
  );
}
