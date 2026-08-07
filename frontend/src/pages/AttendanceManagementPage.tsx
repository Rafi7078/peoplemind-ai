
import axios from "axios";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";
import {
  createAttendanceEmployee,
  createAttendanceShift,
  createAttendanceTeam,
  deleteAttendanceEmployee,
  deleteAttendanceShift,
  deleteAttendanceTeam,
  listAttendanceEmployees,
  listAttendanceShifts,
  listAttendanceTeams,
  updateAttendanceEmployee,
  updateAttendanceShift,
  updateAttendanceTeam,
} from "../features/attendance/api";
import type {
  AttendanceEmployee,
  AttendanceEmployeeCreate,
  AttendanceMasterStatus,
  AttendanceShift,
  AttendanceShiftCreate,
  AttendanceTeam,
  AttendanceTeamCreate,
  WeekdayName,
} from "../features/attendance/types";
type ActiveSection =
  | "overview"
  | "teams"
  | "shifts"
  | "employees";
const weekdays: WeekdayName[] = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
const emptyTeamForm:
  AttendanceTeamCreate = {
    name: "",
    description: null,
    status: "active",
  };
const emptyShiftForm:
  AttendanceShiftCreate = {
    name: "",
    description: null,
    status: "active",
  };
const emptyEmployeeForm:
  AttendanceEmployeeCreate = {
    employee_code: "",
    full_name: "",
    designation: "",
    team_id: 0,
    shift_id: 0,
    weekly_holidays: [],
    is_active: true,
  };
function getApiErrorMessage(
  error: unknown,
  fallbackMessage: string,
): string {
  if (
    axios.isAxiosError(error)
  ) {
    const detail =
      error.response?.data?.detail;
    if (
      typeof detail === "string"
      && detail.trim()
    ) {
      return detail;
    }
  }
  return fallbackMessage;
}
function displayStatus(
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
function masterStatusClass(
  status: AttendanceMasterStatus,
): string {
  return status === "active"
    ? "bg-emerald-100 text-emerald-700"
    : "bg-slate-200 text-slate-700";
}
function employeeStatusClass(
  isActive: boolean,
): string {
  return isActive
    ? "bg-emerald-100 text-emerald-700"
    : "bg-slate-200 text-slate-700";
}
export function AttendanceManagementPage() {
  const [
    activeSection,
    setActiveSection,
  ] = useState<ActiveSection>(
    "overview",
  );
  const [
    teams,
    setTeams,
  ] = useState<AttendanceTeam[]>([]);
  const [
    shifts,
    setShifts,
  ] = useState<AttendanceShift[]>([]);
  const [
    employees,
    setEmployees,
  ] = useState<
    AttendanceEmployee[]
  >([]);
  const [
    teamForm,
    setTeamForm,
  ] = useState<AttendanceTeamCreate>({
    ...emptyTeamForm,
  });
  const [
    shiftForm,
    setShiftForm,
  ] = useState<AttendanceShiftCreate>({
    ...emptyShiftForm,
  });
  const [
    employeeForm,
    setEmployeeForm,
  ] = useState<AttendanceEmployeeCreate>({
    ...emptyEmployeeForm,
  });
  const [
    editingTeamId,
    setEditingTeamId,
  ] = useState<number | null>(
    null,
  );
  const [
    editingShiftId,
    setEditingShiftId,
  ] = useState<number | null>(
    null,
  );
  const [
    editingEmployeeId,
    setEditingEmployeeId,
  ] = useState<number | null>(
    null,
  );
  const [
    selectedTeamFilter,
    setSelectedTeamFilter,
  ] = useState("all");
  const [
    selectedShiftFilter,
    setSelectedShiftFilter,
  ] = useState("all");
  const [
    selectedActiveFilter,
    setSelectedActiveFilter,
  ] = useState("active");
  const [
    isLoading,
    setIsLoading,
  ] = useState(true);
  const [
    busyAction,
    setBusyAction,
  ] = useState<string | null>(
    null,
  );
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
  useEffect(() => {
    document.title =
      "Attendance Management | PeopleMind AI";
    let isActive = true;
    Promise.all([
      listAttendanceTeams(),
      listAttendanceShifts(),
      listAttendanceEmployees(),
    ])
      .then(
        ([
          teamResult,
          shiftResult,
          employeeResult,
        ]) => {
          if (!isActive) {
            return;
          }
          setTeams(teamResult);
          setShifts(shiftResult);
          setEmployees(
            employeeResult,
          );
        },
      )
      .catch(
        (error: unknown) => {
          if (!isActive) {
            return;
          }
          setErrorMessage(
            getApiErrorMessage(
              error,
              "Could not load attendance management data.",
            ),
          );
        },
      )
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });
    return () => {
      isActive = false;
    };
  }, []);
  const teamNameById = useMemo(
    () =>
      new Map(
        teams.map(
          (team) => [
            team.id,
            team.name,
          ],
        ),
      ),
    [teams],
  );
  const shiftNameById = useMemo(
    () =>
      new Map(
        shifts.map(
          (shift) => [
            shift.id,
            shift.name,
          ],
        ),
      ),
    [shifts],
  );
  const filteredEmployees =
    useMemo(
      () =>
        employees.filter(
          (employee) => {
            if (
              selectedTeamFilter
              !== "all"
              && employee.team_id
              !== Number(
                selectedTeamFilter,
              )
            ) {
              return false;
            }
            if (
              selectedShiftFilter
              !== "all"
              && employee.shift_id
              !== Number(
                selectedShiftFilter,
              )
            ) {
              return false;
            }
            if (
              selectedActiveFilter
              === "active"
              && !employee.is_active
            ) {
              return false;
            }
            if (
              selectedActiveFilter
              === "inactive"
              && employee.is_active
            ) {
              return false;
            }
            return true;
          },
        ),
      [
        employees,
        selectedTeamFilter,
        selectedShiftFilter,
        selectedActiveFilter,
      ],
    );
  const activeEmployeeCount =
    employees.filter(
      (employee) =>
        employee.is_active,
    ).length;
  const activeTeamCount =
    teams.filter(
      (team) =>
        team.status === "active",
    ).length;
  const activeShiftCount =
    shifts.filter(
      (shift) =>
        shift.status === "active",
    ).length;
  function clearMessages(): void {
    setErrorMessage(null);
    setActivityMessage(null);
  }
  function beginTeamEdit(
    team: AttendanceTeam,
  ): void {
    clearMessages();
    setEditingTeamId(
      team.id,
    );
    setTeamForm({
      name: team.name,
      description:
        team.description,
      status: team.status,
    });
  }
  function cancelTeamEdit(): void {
    setEditingTeamId(null);
    setTeamForm({
      ...emptyTeamForm,
    });
  }
  async function handleSaveTeam(
    event:
      FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    clearMessages();
    const payload:
      AttendanceTeamCreate = {
        name:
          teamForm.name.trim(),
        description:
          teamForm.description
            ?.trim()
          || null,
        status:
          teamForm.status,
      };
    setBusyAction(
      editingTeamId === null
        ? "create-team"
        : `edit-team-${editingTeamId}`,
    );
    try {
      if (
        editingTeamId === null
      ) {
        const created =
          await createAttendanceTeam(
            payload,
          );
        setTeams(
          (current) =>
            [...current, created]
              .sort(
                (a, b) =>
                  a.name.localeCompare(
                    b.name,
                  ),
              ),
        );
        setActivityMessage(
          "Team created successfully.",
        );
      } else {
        const updated =
          await updateAttendanceTeam(
            editingTeamId,
            payload,
          );
        setTeams(
          (current) =>
            current.map(
              (team) =>
                team.id
                === updated.id
                  ? updated
                  : team,
            ),
        );
        setActivityMessage(
          "Team updated successfully.",
        );
      }
      cancelTeamEdit();
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not save the team.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleArchiveTeam(
    team: AttendanceTeam,
  ): Promise<void> {
    clearMessages();
    setBusyAction(
      `archive-team-${team.id}`,
    );
    try {
      const updated =
        await updateAttendanceTeam(
          team.id,
          {
            status:
              team.status === "active"
                ? "archived"
                : "active",
          },
        );
      setTeams(
        (current) =>
          current.map(
            (item) =>
              item.id === updated.id
                ? updated
                : item,
          ),
      );
      setActivityMessage(
        updated.status === "archived"
          ? "Team archived successfully."
          : "Team restored successfully.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not update team status.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleDeleteTeam(
    team: AttendanceTeam,
  ): Promise<void> {
    const confirmed =
      window.confirm(
        `Permanently delete "${team.name}"?\n\n` +
        "The team can only be deleted when no employees are assigned to it.",
      );
    if (!confirmed) {
      return;
    }
    clearMessages();
    setBusyAction(
      `delete-team-${team.id}`,
    );
    try {
      await deleteAttendanceTeam(
        team.id,
      );
      setTeams(
        (current) =>
          current.filter(
            (item) =>
              item.id !== team.id,
          ),
      );
      setActivityMessage(
        "Team permanently deleted.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not delete the team.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  function beginShiftEdit(
    shift: AttendanceShift,
  ): void {
    clearMessages();
    setEditingShiftId(
      shift.id,
    );
    setShiftForm({
      name: shift.name,
      description:
        shift.description,
      status: shift.status,
    });
  }
  function cancelShiftEdit(): void {
    setEditingShiftId(null);
    setShiftForm({
      ...emptyShiftForm,
    });
  }
  async function handleSaveShift(
    event:
      FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    clearMessages();
    const payload:
      AttendanceShiftCreate = {
        name:
          shiftForm.name.trim(),
        description:
          shiftForm.description
            ?.trim()
          || null,
        status:
          shiftForm.status,
      };
    setBusyAction(
      editingShiftId === null
        ? "create-shift"
        : `edit-shift-${editingShiftId}`,
    );
    try {
      if (
        editingShiftId === null
      ) {
        const created =
          await createAttendanceShift(
            payload,
          );
        setShifts(
          (current) =>
            [...current, created]
              .sort(
                (a, b) =>
                  a.name.localeCompare(
                    b.name,
                  ),
              ),
        );
        setActivityMessage(
          "Shift created successfully.",
        );
      } else {
        const updated =
          await updateAttendanceShift(
            editingShiftId,
            payload,
          );
        setShifts(
          (current) =>
            current.map(
              (shift) =>
                shift.id
                === updated.id
                  ? updated
                  : shift,
            ),
        );
        setActivityMessage(
          "Shift updated successfully.",
        );
      }
      cancelShiftEdit();
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not save the shift.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleArchiveShift(
    shift: AttendanceShift,
  ): Promise<void> {
    clearMessages();
    setBusyAction(
      `archive-shift-${shift.id}`,
    );
    try {
      const updated =
        await updateAttendanceShift(
          shift.id,
          {
            status:
              shift.status === "active"
                ? "archived"
                : "active",
          },
        );
      setShifts(
        (current) =>
          current.map(
            (item) =>
              item.id === updated.id
                ? updated
                : item,
          ),
      );
      setActivityMessage(
        updated.status === "archived"
          ? "Shift archived successfully."
          : "Shift restored successfully.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not update shift status.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleDeleteShift(
    shift: AttendanceShift,
  ): Promise<void> {
    const confirmed =
      window.confirm(
        `Permanently delete "${shift.name}"?\n\n` +
        "The shift can only be deleted when no employees are assigned to it.",
      );
    if (!confirmed) {
      return;
    }
    clearMessages();
    setBusyAction(
      `delete-shift-${shift.id}`,
    );
    try {
      await deleteAttendanceShift(
        shift.id,
      );
      setShifts(
        (current) =>
          current.filter(
            (item) =>
              item.id !== shift.id,
          ),
      );
      setActivityMessage(
        "Shift permanently deleted.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not delete the shift.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  function beginEmployeeEdit(
    employee: AttendanceEmployee,
  ): void {
    clearMessages();
    setEditingEmployeeId(
      employee.id,
    );
    setEmployeeForm({
      employee_code:
        employee.employee_code,
      full_name:
        employee.full_name,
      designation:
        employee.designation,
      team_id:
        employee.team_id,
      shift_id:
        employee.shift_id,
      weekly_holidays: [
        ...employee.weekly_holidays,
      ],
      is_active:
        employee.is_active,
    });
    window.scrollTo({
      top: 300,
      behavior: "smooth",
    });
  }
  function cancelEmployeeEdit(): void {
    setEditingEmployeeId(null);
    setEmployeeForm({
      ...emptyEmployeeForm,
      weekly_holidays: [],
    });
  }
  function toggleWeeklyHoliday(
    day: WeekdayName,
  ): void {
    setEmployeeForm(
      (current) => {
        const exists =
          current.weekly_holidays
            .includes(day);
        return {
          ...current,
          weekly_holidays:
            exists
              ? current.weekly_holidays
                  .filter(
                    (item) =>
                      item !== day,
                  )
              : [
                  ...current
                    .weekly_holidays,
                  day,
                ],
        };
      },
    );
  }
  async function handleSaveEmployee(
    event:
      FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    clearMessages();
    if (
      employeeForm.team_id <= 0
    ) {
      setErrorMessage(
        "Select an employee team.",
      );
      return;
    }
    if (
      employeeForm.shift_id <= 0
    ) {
      setErrorMessage(
        "Select an employee shift.",
      );
      return;
    }
    const payload:
      AttendanceEmployeeCreate = {
        employee_code:
          employeeForm
            .employee_code
            .trim(),
        full_name:
          employeeForm
            .full_name
            .trim(),
        designation:
          employeeForm
            .designation
            .trim(),
        team_id:
          employeeForm.team_id,
        shift_id:
          employeeForm.shift_id,
        weekly_holidays:
          employeeForm
            .weekly_holidays,
        is_active:
          employeeForm.is_active,
      };
    setBusyAction(
      editingEmployeeId === null
        ? "create-employee"
        : (
            `edit-employee-` +
            `${editingEmployeeId}`
          ),
    );
    try {
      if (
        editingEmployeeId === null
      ) {
        const created =
          await createAttendanceEmployee(
            payload,
          );
        setEmployees(
          (current) =>
            [...current, created]
              .sort(
                (a, b) =>
                  a.employee_code
                    .localeCompare(
                      b.employee_code,
                    ),
              ),
        );
        setActivityMessage(
          "Employee created successfully.",
        );
      } else {
        const updated =
          await updateAttendanceEmployee(
            editingEmployeeId,
            payload,
          );
        setEmployees(
          (current) =>
            current.map(
              (employee) =>
                employee.id
                === updated.id
                  ? updated
                  : employee,
            ),
        );
        setActivityMessage(
          "Employee updated successfully.",
        );
      }
      cancelEmployeeEdit();
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not save the employee.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleToggleEmployeeActive(
    employee: AttendanceEmployee,
  ): Promise<void> {
    clearMessages();
    setBusyAction(
      `employee-status-${employee.id}`,
    );
    try {
      const updated =
        await updateAttendanceEmployee(
          employee.id,
          {
            is_active:
              !employee.is_active,
          },
        );
      setEmployees(
        (current) =>
          current.map(
            (item) =>
              item.id === updated.id
                ? updated
                : item,
          ),
      );
      setActivityMessage(
        updated.is_active
          ? "Employee reactivated successfully."
          : "Employee deactivated. Attendance history can remain preserved in future attendance records.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not update employee status.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  async function handleDeleteEmployee(
    employee: AttendanceEmployee,
  ): Promise<void> {
    const confirmed =
      window.confirm(
        `Permanently delete "${employee.full_name}"?\n\n` +
        "For employees who leave the organization, Deactivate is safer. " +
        "Permanent delete should only be used for incorrect or unnecessary records.",
      );
    if (!confirmed) {
      return;
    }
    clearMessages();
    setBusyAction(
      `delete-employee-${employee.id}`,
    );
    try {
      await deleteAttendanceEmployee(
        employee.id,
      );
      setEmployees(
        (current) =>
          current.filter(
            (item) =>
              item.id !== employee.id,
          ),
      );
      if (
        editingEmployeeId
        === employee.id
      ) {
        cancelEmployeeEdit();
      }
      setActivityMessage(
        "Employee permanently deleted.",
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not delete the employee.",
        ),
      );
    } finally {
      setBusyAction(null);
    }
  }
  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="font-semibold text-slate-700">
            Loading Attendance Management...
          </p>
        </div>
      </main>
    );
  }
  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <section className="overflow-hidden rounded-3xl bg-slate-950 px-8 py-9 text-white shadow-xl">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-emerald-400">
          Dynamic workforce attendance foundation
        </p>
        <h1 className="mt-4 text-3xl font-bold md:text-5xl">
          Attendance Management
        </h1>
        <p className="mt-5 max-w-3xl leading-7 text-slate-300">
          Manage teams, shifts and employees before
          recording team-wise daily attendance.
          Nothing is hard-coded to a specific team.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <span className="rounded-full bg-emerald-400/15 px-4 py-2 text-sm font-semibold text-emerald-300">
            {activeEmployeeCount} active employee(s)
          </span>
          <span className="rounded-full bg-sky-400/15 px-4 py-2 text-sm font-semibold text-sky-300">
            {activeTeamCount} active team(s)
          </span>
          <span className="rounded-full bg-violet-400/15 px-4 py-2 text-sm font-semibold text-violet-300">
            {activeShiftCount} active shift(s)
          </span>
          <span className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-slate-200">
            Daily attendance comes next
          </span>
        </div>
      </section>
      <section className="mt-7 flex flex-wrap gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
        {(
          [
            {
              key: "overview",
              label: "Overview",
            },
            {
              key: "teams",
              label: "Teams",
            },
            {
              key: "shifts",
              label: "Shifts",
            },
            {
              key: "employees",
              label: "Employees",
            },
          ] as const
        ).map((section) => (
          <button
            className={[
              "rounded-xl px-5 py-3 text-sm font-semibold transition",
              activeSection
              === section.key
                ? "bg-slate-950 text-white"
                : "text-slate-600 hover:bg-slate-100",
            ].join(" ")}
            key={section.key}
            onClick={() => {
              clearMessages();
              setActiveSection(
                section.key,
              );
            }}
            type="button"
          >
            {section.label}
          </button>
        ))}
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
      {activeSection === "overview" ? (
        <section className="mt-8">
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            {[
              {
                label:
                  "Total employees",
                value:
                  employees.length,
              },
              {
                label:
                  "Active employees",
                value:
                  activeEmployeeCount,
              },
              {
                label:
                  "Teams",
                value:
                  teams.length,
              },
              {
                label:
                  "Shifts",
                value:
                  shifts.length,
              },
            ].map((item) => (
              <article
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                key={item.label}
              >
                <p className="text-sm font-semibold text-slate-500">
                  {item.label}
                </p>
                <p className="mt-3 text-4xl font-bold text-slate-950">
                  {item.value}
                </p>
              </article>
            ))}
          </div>
          <article className="mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              Attendance workflow
            </h2>
            <p className="mt-2 max-w-3xl leading-7 text-slate-600">
              Create teams and shifts first. Then add
              employees with their weekly holidays.
              The next milestone will use this roster
              to generate team and shift based daily
              attendance automatically.
            </p>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              {[
                {
                  step: "01",
                  title:
                    "Create Teams",
                  detail:
                    "Labelmaster, CVAT, QA, DevOps or any future team.",
                },
                {
                  step: "02",
                  title:
                    "Create Shifts",
                  detail:
                    "Early Morning, Morning, Evening, Night or any future shift.",
                },
                {
                  step: "03",
                  title:
                    "Add Employees",
                  detail:
                    "Assign team, shift and weekly holidays for every employee.",
                },
              ].map((item) => (
                <div
                  className="rounded-2xl bg-slate-50 p-5"
                  key={item.step}
                >
                  <p className="text-sm font-black text-emerald-600">
                    {item.step}
                  </p>
                  <h3 className="mt-2 font-bold text-slate-900">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    {item.detail}
                  </p>
                </div>
              ))}
            </div>
          </article>
        </section>
      ) : null}
      {activeSection === "teams" ? (
        <section className="mt-8 grid gap-7 lg:grid-cols-[0.8fr_1.2fr]">
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              {editingTeamId === null
                ? "Create team"
                : "Edit team"}
            </h2>
            <form
              className="mt-7 space-y-5"
              onSubmit={
                handleSaveTeam
              }
            >
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Team name
                </span>
                <input
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                  onChange={(event) => {
                    setTeamForm(
                      (current) => ({
                        ...current,
                        name:
                          event.target
                            .value,
                      }),
                    );
                  }}
                  placeholder="Example: Labelmaster"
                  required
                  value={teamForm.name}
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Description
                </span>
                <textarea
                  className="mt-2 min-h-28 w-full resize-y rounded-xl border border-slate-300 px-4 py-3"
                  onChange={(event) => {
                    setTeamForm(
                      (current) => ({
                        ...current,
                        description:
                          event.target
                            .value,
                      }),
                    );
                  }}
                  placeholder="Optional team description"
                  value={
                    teamForm.description
                    ?? ""
                  }
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Status
                </span>
                <select
                  className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                  onChange={(event) => {
                    setTeamForm(
                      (current) => ({
                        ...current,
                        status:
                          (((event.target.value as AttendanceMasterStatus))),
                      }),
                    );
                  }}
                  value={teamForm.status}
                >
                  <option value="active">
                    Active
                  </option>
                  <option value="archived">
                    Archived
                  </option>
                </select>
              </label>
              <div className="flex gap-3">
                <button
                  className="flex-1 rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-50"
                  disabled={
                    busyAction !== null
                  }
                  type="submit"
                >
                  {editingTeamId === null
                    ? "Create team"
                    : "Save changes"}
                </button>
                {editingTeamId !== null ? (
                  <button
                    className="rounded-xl border border-slate-300 px-5 py-3 font-semibold text-slate-700"
                    onClick={
                      cancelTeamEdit
                    }
                    type="button"
                  >
                    Cancel
                  </button>
                ) : null}
              </div>
            </form>
          </article>
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              Teams
            </h2>
            <p className="mt-1 text-slate-500">
              {teams.length} team(s) configured
            </p>
            <div className="mt-6 space-y-4">
              {teams.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                  No team has been created yet.
                </div>
              ) : null}
              {teams.map(
                (team) => {
                  const memberCount =
                    employees.filter(
                      (employee) =>
                        employee.team_id
                        === team.id,
                    ).length;
                  return (
                    <article
                      className="rounded-2xl border border-slate-200 p-5"
                      key={team.id}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <h3 className="text-lg font-bold text-slate-900">
                            {team.name}
                          </h3>
                          <p className="mt-1 text-sm text-slate-500">
                            {memberCount} employee(s)
                          </p>
                        </div>
                        <span
                          className={[
                            "rounded-full px-3 py-1 text-xs font-bold",
                            masterStatusClass(
                              team.status,
                            ),
                          ].join(" ")}
                        >
                          {displayStatus(
                            team.status,
                          )}
                        </span>
                      </div>
                      {team.description ? (
                        <p className="mt-3 leading-6 text-slate-600">
                          {team.description}
                        </p>
                      ) : null}
                      <div className="mt-5 flex flex-wrap gap-2">
                        <button
                          className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700"
                          onClick={() => {
                            beginTeamEdit(
                              team,
                            );
                          }}
                          type="button"
                        >
                          Edit
                        </button>
                        <button
                          className="rounded-lg border border-amber-300 px-3 py-2 text-sm font-semibold text-amber-700"
                          onClick={() => {
                            void handleArchiveTeam(
                              team,
                            );
                          }}
                          type="button"
                        >
                          {team.status
                          === "active"
                            ? "Archive"
                            : "Restore"}
                        </button>
                        <button
                          className="rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold text-red-700"
                          onClick={() => {
                            void handleDeleteTeam(
                              team,
                            );
                          }}
                          type="button"
                        >
                          Delete
                        </button>
                      </div>
                    </article>
                  );
                },
              )}
            </div>
          </article>
        </section>
      ) : null}
      {activeSection === "shifts" ? (
        <section className="mt-8 grid gap-7 lg:grid-cols-[0.8fr_1.2fr]">
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              {editingShiftId === null
                ? "Create shift"
                : "Edit shift"}
            </h2>
            <form
              className="mt-7 space-y-5"
              onSubmit={
                handleSaveShift
              }
            >
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Shift name
                </span>
                <input
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                  onChange={(event) => {
                    setShiftForm(
                      (current) => ({
                        ...current,
                        name:
                          event.target
                            .value,
                      }),
                    );
                  }}
                  placeholder="Example: Morning"
                  required
                  value={shiftForm.name}
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Description
                </span>
                <textarea
                  className="mt-2 min-h-28 w-full resize-y rounded-xl border border-slate-300 px-4 py-3"
                  onChange={(event) => {
                    setShiftForm(
                      (current) => ({
                        ...current,
                        description:
                          event.target
                            .value,
                      }),
                    );
                  }}
                  placeholder="Optional shift description"
                  value={
                    shiftForm.description
                    ?? ""
                  }
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">
                  Status
                </span>
                <select
                  className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                  onChange={(event) => {
                    setShiftForm(
                      (current) => ({
                        ...current,
                        status:
                          (((event.target.value as AttendanceMasterStatus))),
                      }),
                    );
                  }}
                  value={
                    shiftForm.status
                  }
                >
                  <option value="active">
                    Active
                  </option>
                  <option value="archived">
                    Archived
                  </option>
                </select>
              </label>
              <div className="flex gap-3">
                <button
                  className="flex-1 rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-50"
                  disabled={
                    busyAction !== null
                  }
                  type="submit"
                >
                  {editingShiftId === null
                    ? "Create shift"
                    : "Save changes"}
                </button>
                {editingShiftId !== null ? (
                  <button
                    className="rounded-xl border border-slate-300 px-5 py-3 font-semibold text-slate-700"
                    onClick={
                      cancelShiftEdit
                    }
                    type="button"
                  >
                    Cancel
                  </button>
                ) : null}
              </div>
            </form>
          </article>
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              Shifts
            </h2>
            <p className="mt-1 text-slate-500">
              {shifts.length} shift(s) configured
            </p>
            <div className="mt-6 space-y-4">
              {shifts.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                  No shift has been created yet.
                </div>
              ) : null}
              {shifts.map(
                (shift) => {
                  const memberCount =
                    employees.filter(
                      (employee) =>
                        employee.shift_id
                        === shift.id,
                    ).length;
                  return (
                    <article
                      className="rounded-2xl border border-slate-200 p-5"
                      key={shift.id}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <h3 className="text-lg font-bold text-slate-900">
                            {shift.name}
                          </h3>
                          <p className="mt-1 text-sm text-slate-500">
                            {memberCount} employee(s)
                          </p>
                        </div>
                        <span
                          className={[
                            "rounded-full px-3 py-1 text-xs font-bold",
                            masterStatusClass(
                              shift.status,
                            ),
                          ].join(" ")}
                        >
                          {displayStatus(
                            shift.status,
                          )}
                        </span>
                      </div>
                      {shift.description ? (
                        <p className="mt-3 leading-6 text-slate-600">
                          {shift.description}
                        </p>
                      ) : null}
                      <div className="mt-5 flex flex-wrap gap-2">
                        <button
                          className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700"
                          onClick={() => {
                            beginShiftEdit(
                              shift,
                            );
                          }}
                          type="button"
                        >
                          Edit
                        </button>
                        <button
                          className="rounded-lg border border-amber-300 px-3 py-2 text-sm font-semibold text-amber-700"
                          onClick={() => {
                            void handleArchiveShift(
                              shift,
                            );
                          }}
                          type="button"
                        >
                          {shift.status
                          === "active"
                            ? "Archive"
                            : "Restore"}
                        </button>
                        <button
                          className="rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold text-red-700"
                          onClick={() => {
                            void handleDeleteShift(
                              shift,
                            );
                          }}
                          type="button"
                        >
                          Delete
                        </button>
                      </div>
                    </article>
                  );
                },
              )}
            </div>
          </article>
        </section>
      ) : null}
      {activeSection === "employees" ? (
        <section className="mt-8">
          <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              {editingEmployeeId === null
                ? "Add employee"
                : "Edit employee"}
            </h2>
            <p className="mt-2 text-slate-600">
              Employee attendance status will be
              recorded separately in the next
              milestone.
            </p>
            {teams.length === 0
            || shifts.length === 0 ? (
              <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
                Create at least one team and one
                shift before adding employees.
              </div>
            ) : null}
            <form
              className="mt-7"
              onSubmit={
                handleSaveEmployee
              }
            >
              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Employee ID
                  </span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                    onChange={(event) => {
                      setEmployeeForm(
                        (current) => ({
                          ...current,
                          employee_code:
                            event.target
                              .value,
                        }),
                      );
                    }}
                    placeholder="EMP001"
                    required
                    value={
                      employeeForm
                        .employee_code
                    }
                  />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Full name
                  </span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                    onChange={(event) => {
                      setEmployeeForm(
                        (current) => ({
                          ...current,
                          full_name:
                            event.target
                              .value,
                        }),
                      );
                    }}
                    required
                    value={
                      employeeForm
                        .full_name
                    }
                  />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Designation
                  </span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3"
                    onChange={(event) => {
                      setEmployeeForm(
                        (current) => ({
                          ...current,
                          designation:
                            event.target
                              .value,
                        }),
                      );
                    }}
                    placeholder="Data Annotation Analyst"
                    required
                    value={
                      employeeForm
                        .designation
                    }
                  />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Team
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                    onChange={(event) => {
                      setEmployeeForm(
                        (current) => ({
                          ...current,
                          team_id:
                            Number(
                              event.target
                                .value,
                            ),
                        }),
                      );
                    }}
                    required
                    value={
                      employeeForm.team_id
                      || ""
                    }
                  >
                    <option value="">
                      Select team
                    </option>
                    {teams
                      .filter(
                        (team) =>
                          team.status
                          === "active"
                          || team.id
                          === employeeForm
                            .team_id,
                      )
                      .map(
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
                      setEmployeeForm(
                        (current) => ({
                          ...current,
                          shift_id:
                            Number(
                              event.target
                                .value,
                            ),
                        }),
                      );
                    }}
                    required
                    value={
                      employeeForm.shift_id
                      || ""
                    }
                  >
                    <option value="">
                      Select shift
                    </option>
                    {shifts
                      .filter(
                        (shift) =>
                          shift.status
                          === "active"
                          || shift.id
                          === employeeForm
                            .shift_id,
                      )
                      .map(
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
                <label>
                  <span className="text-sm font-semibold text-slate-700">
                    Employee status
                  </span>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
                    onChange={(event) => {
                      setEmployeeForm(
                        (current) => ({
                          ...current,
                          is_active:
                            event.target
                              .value
                            === "active",
                        }),
                      );
                    }}
                    value={
                      employeeForm
                        .is_active
                        ? "active"
                        : "inactive"
                    }
                  >
                    <option value="active">
                      Active
                    </option>
                    <option value="inactive">
                      Inactive
                    </option>
                  </select>
                </label>
              </div>
              <fieldset className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <legend className="px-2 text-sm font-bold text-slate-800">
                  Weekly holidays
                </legend>
                <div className="mt-2 flex flex-wrap gap-3">
                  {weekdays.map(
                    (day) => (
                      <label
                        className={[
                          "flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2 text-sm font-semibold",
                          employeeForm
                            .weekly_holidays
                            .includes(day)
                            ? "border-rose-300 bg-rose-50 text-rose-700"
                            : "border-slate-200 bg-white text-slate-600",
                        ].join(" ")}
                        key={day}
                      >
                        <input
                          checked={
                            employeeForm
                              .weekly_holidays
                              .includes(day)
                          }
                          onChange={() => {
                            toggleWeeklyHoliday(
                              day,
                            );
                          }}
                          type="checkbox"
                        />
                        {day}
                      </label>
                    ),
                  )}
                </div>
              </fieldset>
              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  className="rounded-xl bg-slate-950 px-6 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={
                    busyAction !== null
                    || teams.length === 0
                    || shifts.length === 0
                  }
                  type="submit"
                >
                  {editingEmployeeId
                  === null
                    ? "Add employee"
                    : "Save employee changes"}
                </button>
                {editingEmployeeId
                !== null ? (
                  <button
                    className="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-slate-700"
                    onClick={
                      cancelEmployeeEdit
                    }
                    type="button"
                  >
                    Cancel
                  </button>
                ) : null}
              </div>
            </form>
          </article>
          <article className="mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <div className="flex flex-wrap items-end justify-between gap-5">
              <div>
                <h2 className="text-2xl font-bold text-slate-950">
                  Employees
                </h2>
                <p className="mt-1 text-slate-500">
                  {filteredEmployees.length}
                  {" "}employee(s) in this view
                </p>
              </div>
              <div className="grid w-full gap-3 md:w-auto md:grid-cols-3">
                <select
                  className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm"
                  onChange={(event) => {
                    setSelectedTeamFilter(
                      event.target.value,
                    );
                  }}
                  value={
                    selectedTeamFilter
                  }
                >
                  <option value="all">
                    All teams
                  </option>
                  {teams.map(
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
                <select
                  className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm"
                  onChange={(event) => {
                    setSelectedShiftFilter(
                      event.target.value,
                    );
                  }}
                  value={
                    selectedShiftFilter
                  }
                >
                  <option value="all">
                    All shifts
                  </option>
                  {shifts.map(
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
                <select
                  className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm"
                  onChange={(event) => {
                    setSelectedActiveFilter(
                      event.target.value,
                    );
                  }}
                  value={
                    selectedActiveFilter
                  }
                >
                  <option value="active">
                    Active employees
                  </option>
                  <option value="inactive">
                    Inactive employees
                  </option>
                  <option value="all">
                    All employees
                  </option>
                </select>
              </div>
            </div>
            {filteredEmployees.length
            === 0 ? (
              <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
                No employee matches the selected filters.
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
                        Designation
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Team
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Shift
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Weekly holiday
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Status
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEmployees.map(
                      (employee) => (
                        <tr
                          className="align-top"
                          key={employee.id}
                        >
                          <td className="border-b border-slate-100 px-4 py-4">
                            <p className="font-bold text-slate-900">
                              {employee.full_name}
                            </p>
                            <p className="mt-1 text-xs font-semibold text-slate-400">
                              {employee.employee_code}
                            </p>
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4 text-sm text-slate-600">
                            {employee.designation}
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4 text-sm font-semibold text-slate-700">
                            {teamNameById.get(
                              employee.team_id,
                            )
                            ?? "Unknown team"}
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4 text-sm font-semibold text-slate-700">
                            {shiftNameById.get(
                              employee.shift_id,
                            )
                            ?? "Unknown shift"}
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4">
                            <div className="flex max-w-52 flex-wrap gap-1">
                              {employee
                                .weekly_holidays
                                .length > 0
                                ? employee
                                    .weekly_holidays
                                    .map(
                                      (day) => (
                                        <span
                                          className="rounded-full bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-600"
                                          key={day}
                                        >
                                          {day}
                                        </span>
                                      ),
                                    )
                                : (
                                    <span className="text-sm text-slate-400">
                                      None
                                    </span>
                                  )}
                            </div>
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4">
                            <span
                              className={[
                                "rounded-full px-2.5 py-1 text-xs font-bold",
                                employeeStatusClass(
                                  employee.is_active,
                                ),
                              ].join(" ")}
                            >
                              {employee.is_active
                                ? "Active"
                                : "Inactive"}
                            </span>
                          </td>
                          <td className="border-b border-slate-100 px-4 py-4">
                            <div className="flex min-w-52 flex-wrap gap-2">
                              <button
                                className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700"
                                onClick={() => {
                                  beginEmployeeEdit(
                                    employee,
                                  );
                                }}
                                type="button"
                              >
                                Edit
                              </button>
                              <button
                                className="rounded-lg border border-amber-300 px-3 py-2 text-xs font-semibold text-amber-700"
                                onClick={() => {
                                  void handleToggleEmployeeActive(
                                    employee,
                                  );
                                }}
                                type="button"
                              >
                                {employee.is_active
                                  ? "Deactivate"
                                  : "Reactivate"}
                              </button>
                              <button
                                className="rounded-lg border border-red-300 px-3 py-2 text-xs font-semibold text-red-700"
                                onClick={() => {
                                  void handleDeleteEmployee(
                                    employee,
                                  );
                                }}
                                type="button"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        </section>
      ) : null}
    </main>
  );
}
