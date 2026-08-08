import axios from "axios";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  createAttendanceLeave,
  loadAttendanceLeaves,
  updateAttendanceLeave,
} from "./api";
import type {
  AttendanceLeave,
  AttendanceLeaveList,
  LeaveStatus,
  LeaveType,
} from "./types";
type EmployeeOption = {
  id: number;
  employee_code: string;
  full_name: string;
  designation: string;
  team_id: number;
  shift_id: number;
  is_active: boolean;
};
type Props = {
  employees: EmployeeOption[];
};
const leaveTypes: Array<{
  value: LeaveType;
  label: string;
}> = [
  {
    value: "casual",
    label: "Casual Leave",
  },
  {
    value: "sick",
    label: "Sick Leave",
  },
  {
    value: "annual",
    label: "Annual Leave",
  },
  {
    value: "other",
    label: "Other",
  },
];
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
function formatLeaveType(
  value: LeaveType,
): string {
  return (
    leaveTypes.find(
      (item) => item.value === value,
    )?.label
    ?? value
  );
}
function formatStatus(
  value: LeaveStatus,
): string {
  if (value === "approved") {
    return "Approved";
  }
  if (value === "cancelled") {
    return "Cancelled";
  }
  return "Pending";
}
function statusClass(
  value: LeaveStatus,
): string {
  if (value === "approved") {
    return (
      "bg-emerald-100 text-emerald-700"
    );
  }
  if (value === "cancelled") {
    return (
      "bg-slate-200 text-slate-600"
    );
  }
  return (
    "bg-amber-100 text-amber-700"
  );
}
export function LeaveManagementPanel({
  employees,
}: Props) {
  const [
    employeeId,
    setEmployeeId,
  ] = useState("");
  const [
    leaveType,
    setLeaveType,
  ] = useState<LeaveType>(
    "casual",
  );
  const [
    fromDate,
    setFromDate,
  ] = useState("");
  const [
    toDate,
    setToDate,
  ] = useState("");
  const [
    reason,
    setReason,
  ] = useState("");
  const [
    createStatus,
    setCreateStatus,
  ] = useState<LeaveStatus>(
    "pending",
  );
  const [
    filterEmployeeId,
    setFilterEmployeeId,
  ] = useState("");
  const [
    filterStatus,
    setFilterStatus,
  ] = useState("");
  const [
    dateFrom,
    setDateFrom,
  ] = useState("");
  const [
    dateTo,
    setDateTo,
  ] = useState("");
  const [
    leaves,
    setLeaves,
  ] = useState<
    AttendanceLeaveList | null
  >(null);
  const [
    isLoading,
    setIsLoading,
  ] = useState(true);
  const [
    isSaving,
    setIsSaving,
  ] = useState(false);
  const [
    actionLeaveId,
    setActionLeaveId,
  ] = useState<number | null>(
    null,
  );
  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );
  const [
    successMessage,
    setSuccessMessage,
  ] = useState<string | null>(
    null,
  );
  const activeEmployees =
    useMemo(
      () =>
        employees
          .filter(
            (employee) =>
              employee.is_active,
          )
          .sort(
            (first, second) =>
              first.employee_code.localeCompare(
                second.employee_code,
              ),
          ),
      [employees],
    );
  const employeeById =
    useMemo(
      () =>
        new Map(
          employees.map(
            (employee) => [
              employee.id,
              employee,
            ],
          ),
        ),
      [employees],
    );
  async function refreshLeaves():
    Promise<void> {
    setErrorMessage(null);
    setIsLoading(true);
    try {
      const result =
        await loadAttendanceLeaves(
          {
            employeeId:
              filterEmployeeId
              ? Number(
                  filterEmployeeId,
                )
              : undefined,
            status:
              filterStatus
              ? (filterStatus as LeaveStatus)
              : undefined,
            dateFrom:
              dateFrom || undefined,
            dateTo:
              dateTo || undefined,
          },
        );
      setLeaves(result);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not load leave records.",
        ),
      );
    } finally {
      setIsLoading(false);
    }
  }
  useEffect(
    () => {
      let isActive = true;
      void loadAttendanceLeaves()
        .then((result) => {
          if (isActive) {
            setLeaves(result);
          }
        })
        .catch((error) => {
          if (isActive) {
            setErrorMessage(
              getApiErrorMessage(
                error,
                "Could not load leave records.",
              ),
            );
          }
        })
        .finally(() => {
          if (isActive) {
            setIsLoading(false);
          }
        });
      return () => {
        isActive = false;
      };
    },
    [],
  );
  async function handleCreate():
    Promise<void> {
    setErrorMessage(null);
    setSuccessMessage(null);
    if (!employeeId) {
      setErrorMessage(
        "Select an employee.",
      );
      return;
    }
    if (!fromDate || !toDate) {
      setErrorMessage(
        "Select both From Date and To Date.",
      );
      return;
    }
    setIsSaving(true);
    try {
      await createAttendanceLeave(
        {
          employee_id:
            Number(employeeId),
          leave_type: leaveType,
          from_date: fromDate,
          to_date: toDate,
          reason:
            reason.trim()
            || null,
          status: createStatus,
        },
      );
      setSuccessMessage(
        "Leave record created successfully.",
      );
      setEmployeeId("");
      setLeaveType("casual");
      setFromDate("");
      setToDate("");
      setReason("");
      setCreateStatus("pending");
      await refreshLeaves();
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not create leave record.",
        ),
      );
    } finally {
      setIsSaving(false);
    }
  }
  async function changeStatus(
    leave: AttendanceLeave,
    status: LeaveStatus,
  ): Promise<void> {
    setErrorMessage(null);
    setSuccessMessage(null);
    setActionLeaveId(leave.id);
    try {
      await updateAttendanceLeave(
        leave.id,
        {
          status,
        },
      );
      setSuccessMessage(
        status === "approved"
          ? "Leave approved."
          : "Leave cancelled.",
      );
      await refreshLeaves();
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not update leave status.",
        ),
      );
    } finally {
      setActionLeaveId(null);
    }
  }
  function clearFilters(): void {
    setFilterEmployeeId("");
    setFilterStatus("");
    setDateFrom("");
    setDateTo("");
  }
  return (
    <section className="mt-8">
      <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-600">
          Leave management
        </p>
        <h2 className="mt-2 text-2xl font-bold text-slate-950">
          Create Leave Record
        </h2>
        <p className="mt-2 max-w-3xl leading-6 text-slate-600">
          Approved leave automatically
          affects Daily Attendance
          suggestions for its active date
          range.
        </p>
        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Employee
            </span>
            <select
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setEmployeeId(
                  event.target.value,
                );
              }}
              value={employeeId}
            >
              <option value="">
                Select employee
              </option>
              {activeEmployees.map(
                (employee) => (
                  <option
                    key={employee.id}
                    value={employee.id}
                  >
                    {employee.employee_code}
                    {" | "}
                    {employee.full_name}
                  </option>
                ),
              )}
            </select>
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Leave Type
            </span>
            <select
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setLeaveType(
                  (event.target.value as LeaveType),
                );
              }}
              value={leaveType}
            >
              {leaveTypes.map(
                (item) => (
                  <option
                    key={item.value}
                    value={item.value}
                  >
                    {item.label}
                  </option>
                ),
              )}
            </select>
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Initial Status
            </span>
            <select
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setCreateStatus(
                  (event.target.value as LeaveStatus),
                );
              }}
              value={createStatus}
            >
              <option value="pending">
                Pending
              </option>
              <option value="approved">
                Approved
              </option>
            </select>
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              From Date
            </span>
            <input
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setFromDate(
                  event.target.value,
                );
              }}
              type="date"
              value={fromDate}
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              To Date
            </span>
            <input
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setToDate(
                  event.target.value,
                );
              }}
              type="date"
              value={toDate}
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Reason
            </span>
            <input
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              maxLength={500}
              onChange={(event) => {
                setReason(
                  event.target.value,
                );
              }}
              placeholder="Optional reason"
              value={reason}
            />
          </label>
        </div>
        <button
          className="mt-5 rounded-xl bg-amber-600 px-6 py-3 font-semibold text-white disabled:opacity-50"
          disabled={isSaving}
          onClick={() => {
            void handleCreate();
          }}
          type="button"
        >
          {isSaving
            ? "Saving leave..."
            : "Create leave"}
        </button>
      </article>
      {errorMessage ? (
        <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {errorMessage}
        </div>
      ) : null}
      {successMessage ? (
        <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-semibold text-emerald-700">
          {successMessage}
        </div>
      ) : null}
      <article className="mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <h2 className="text-xl font-bold text-slate-950">
          Leave Records
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          {leaves?.total ?? 0}
          {" "}record(s)
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <select
            className="rounded-xl border border-slate-300 bg-white px-4 py-3"
            onChange={(event) => {
              setFilterEmployeeId(
                event.target.value,
              );
            }}
            value={filterEmployeeId}
          >
            <option value="">
              All employees
            </option>
            {employees.map(
              (employee) => (
                <option
                  key={employee.id}
                  value={employee.id}
                >
                  {employee.employee_code}
                  {" | "}
                  {employee.full_name}
                </option>
              ),
            )}
          </select>
          <select
            className="rounded-xl border border-slate-300 bg-white px-4 py-3"
            onChange={(event) => {
              setFilterStatus(
                event.target.value,
              );
            }}
            value={filterStatus}
          >
            <option value="">
              All statuses
            </option>
            <option value="pending">
              Pending
            </option>
            <option value="approved">
              Approved
            </option>
            <option value="cancelled">
              Cancelled
            </option>
          </select>
          <input
            className="rounded-xl border border-slate-300 bg-white px-4 py-3"
            onChange={(event) => {
              setDateFrom(
                event.target.value,
              );
            }}
            type="date"
            value={dateFrom}
          />
          <input
            className="rounded-xl border border-slate-300 bg-white px-4 py-3"
            onChange={(event) => {
              setDateTo(
                event.target.value,
              );
            }}
            type="date"
            value={dateTo}
          />
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            className="rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
            disabled={isLoading}
            onClick={() => {
              void refreshLeaves();
            }}
            type="button"
          >
            Apply filters
          </button>
          <button
            className="rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700"
            onClick={clearFilters}
            type="button"
          >
            Clear filters
          </button>
        </div>
        {isLoading && !leaves ? (
          <div className="mt-6 rounded-2xl bg-slate-50 p-8 text-center text-slate-500">
            Loading leave records...
          </div>
        ) : leaves?.items.length ? (
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-0">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="border-b border-slate-200 px-4 py-3">
                    Employee
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Leave
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Dates
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Status
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Reason
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {leaves.items.map(
                  (leave) => {
                    const employee =
                      employeeById.get(
                        leave.employee_id,
                      );
                    return (
                      <tr
                        key={leave.id}
                        className="align-top"
                      >
                        <td className="border-b border-slate-100 px-4 py-4">
                          <p className="font-bold text-slate-900">
                            {employee?.full_name
                              ?? `Employee #${leave.employee_id}`}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            {employee?.employee_code
                              ?? "-"}
                          </p>
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 text-sm font-semibold text-slate-700">
                          {formatLeaveType(
                            leave.leave_type,
                          )}
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 text-sm text-slate-600">
                          {leave.from_date}
                          {" to "}
                          {leave.to_date}
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4">
                          <span
                            className={[
                              "inline-flex rounded-full px-2.5 py-1 text-xs font-bold",
                              statusClass(
                                leave.status,
                              ),
                            ].join(" ")}
                          >
                            {formatStatus(
                              leave.status,
                            )}
                          </span>
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 text-sm text-slate-600">
                          {leave.reason || "-"}
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4">
                          <div className="flex flex-wrap gap-2">
                            {leave.status
                              === "pending" ? (
                              <button
                                className="rounded-lg border border-emerald-300 px-3 py-2 text-xs font-semibold text-emerald-700 disabled:opacity-50"
                                disabled={
                                  actionLeaveId
                                  === leave.id
                                }
                                onClick={() => {
                                  void changeStatus(
                                    leave,
                                    "approved",
                                  );
                                }}
                                type="button"
                              >
                                Approve
                              </button>
                            ) : null}
                            {leave.status
                              !== "cancelled" ? (
                              <button
                                className="rounded-lg border border-red-300 px-3 py-2 text-xs font-semibold text-red-700 disabled:opacity-50"
                                disabled={
                                  actionLeaveId
                                  === leave.id
                                }
                                onClick={() => {
                                  void changeStatus(
                                    leave,
                                    "cancelled",
                                  );
                                }}
                                type="button"
                              >
                                Cancel
                              </button>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    );
                  },
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
            No leave records found.
          </div>
        )}
      </article>
    </section>
  );
}
