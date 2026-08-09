import axios from "axios";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  downloadAttendanceHistoryCsv,
  loadAttendanceHistory,
  loadAttendanceHistoryReport,
} from "./api";
import type {
  AttendanceHistoryItem,
  AttendanceHistoryList,
  AttendanceHistoryReport,
  AttendanceShift,
  AttendanceStatus,
  AttendanceTeam,
} from "./types";
type Props = {
  teams: AttendanceTeam[];
  shifts: AttendanceShift[];
};
function formatLeaveType(
  value: string,
): string {
  switch (value) {
    case "casual":
      return "Casual Leave";
    case "sick":
      return "Sick Leave";
    case "annual":
      return "Annual Leave";
    case "other":
      return "Other Leave";
    default:
      return value;
  }
}
function formatStatus(
  status: AttendanceStatus,
): string {
  switch (status) {
    case "present":
      return "Present";
    case "absent":
      return "Absent";
    case "on_leave":
      return "On Leave";
    case "weekly_holiday":
      return "Weekly Holiday";
  }
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
function formatDate(
  value: string,
): string {
  const date = new Date(
    `${value}T00:00:00`,
  );
  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(date);
}
function formatDateTime(
  value: string,
): string {
  const date = new Date(value);
  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(date);
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
export function AttendanceHistoryPanel({
  teams,
  shifts,
}: Props) {
  const [
    dateFrom,
    setDateFrom,
  ] = useState("");
  const [
    dateTo,
    setDateTo,
  ] = useState("");
  const [
    teamId,
    setTeamId,
  ] = useState("");
  const [
    shiftId,
    setShiftId,
  ] = useState("");
  const [
    history,
    setHistory,
  ] = useState<
    AttendanceHistoryList | null
  >(null);
  const [
    selectedReport,
    setSelectedReport,
  ] = useState<
    AttendanceHistoryReport | null
  >(null);
  const [
    selectedReportKey,
    setSelectedReportKey,
  ] = useState<string | null>(
    null,
  );
  const [
    isLoading,
    setIsLoading,
  ] = useState(true);
  const [
    isReportLoading,
    setIsReportLoading,
  ] = useState(false);
  const [
    isExporting,
    setIsExporting,
  ] = useState(false);
  const [
    errorMessage,
    setErrorMessage,
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
  const loadHistory =
    useCallback(
      async (): Promise<void> => {
        setErrorMessage(null);
        setIsLoading(true);
        try {
          const result =
            await loadAttendanceHistory(
              {
                dateFrom:
                  dateFrom || undefined,
                dateTo:
                  dateTo || undefined,
                teamId:
                  teamId
                  ? Number(teamId)
                  : undefined,
                shiftId:
                  shiftId
                  ? Number(shiftId)
                  : undefined,
              },
            );
          setHistory(result);
          setSelectedReport(null);
          setSelectedReportKey(null);
        } catch (error) {
          setErrorMessage(
            getApiErrorMessage(
              error,
              "Could not load attendance history.",
            ),
          );
        } finally {
          setIsLoading(false);
        }
      },
      [
        dateFrom,
        dateTo,
        teamId,
        shiftId,
      ],
    );
  useEffect(
    () => {
      let isActive = true;
      void loadAttendanceHistory()
        .then((result) => {
          if (!isActive) {
            return;
          }
          setHistory(result);
        })
        .catch((error) => {
          if (!isActive) {
            return;
          }
          setErrorMessage(
            getApiErrorMessage(
              error,
              "Could not load attendance history.",
            ),
          );
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
  async function openReport(
    item: AttendanceHistoryItem,
  ): Promise<void> {
    setErrorMessage(null);
    const key = [
      item.attendance_date,
      item.team_id,
      item.shift_id,
    ].join("-");
    setSelectedReportKey(key);
    setIsReportLoading(true);
    try {
      const report =
        await loadAttendanceHistoryReport(
          item.attendance_date,
          item.team_id,
          item.shift_id,
        );
      setSelectedReport(report);
    } catch (error) {
      setSelectedReport(null);
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not load the attendance report.",
        ),
      );
    } finally {
      setIsReportLoading(false);
    }
  }
  async function downloadCsv():
    Promise<void> {
    if (!selectedReport) {
      return;
    }
    setErrorMessage(null);
    setIsExporting(true);
    try {
      const blob =
        await downloadAttendanceHistoryCsv(
          selectedReport
            .attendance_date,
          selectedReport.team_id,
          selectedReport.shift_id,
        );
      const url =
        URL.createObjectURL(blob);
      const link =
        document.createElement("a");
      link.href = url;
      link.download = [
        "attendance",
        selectedReport
          .attendance_date,
        `team-${selectedReport.team_id}`,
        `shift-${selectedReport.shift_id}`,
      ].join("_")
        + ".csv";
      document.body.appendChild(
        link,
      );
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Could not download the CSV report.",
        ),
      );
    } finally {
      setIsExporting(false);
    }
  }
  function printReport(): void {
    const reportElement =
      document.querySelector<HTMLElement>(
        ".attendance-report-print-area",
      );
    if (!reportElement) {
      setErrorMessage(
        "Could not prepare the attendance report for printing.",
      );
      return;
    }
    const printWindow = window.open(
      "",
      "_blank",
      "width=1000,height=800",
    );
    if (!printWindow) {
      setErrorMessage(
        "The print window was blocked by the browser. Allow pop-ups and try again.",
      );
      return;
    }
    const reportClone =
      reportElement.cloneNode(
        true,
      ) as HTMLElement;
    reportClone
      .querySelectorAll(
        ".attendance-report-print-hide",
      )
      .forEach(
        (element) => {
          element.remove();
        },
      );
    printWindow.document.open();
    printWindow.document.write(`
      <!doctype html>
      <html>
        <head>
          <meta charset="utf-8" />
          <title>Attendance Report</title>
          <style>
            @page {
              size: A4 portrait;
              margin: 10mm;
            }
            * {
              box-sizing: border-box;
            }
            html,
            body {
              margin: 0;
              padding: 0;
              background: #ffffff;
              color: #0f172a;
              font-family:
                Arial,
                Helvetica,
                sans-serif;
            }
            body {
              width: 100%;
              font-size: 11px;
            }
            .attendance-report-print-area {
              width: 100%;
              margin: 0;
              padding: 0;
              border: 0;
              box-shadow: none;
            }
            .attendance-report-print-area > div:first-child {
              margin-bottom: 10px;
            }
            h1,
            h2,
            h3,
            p {
              margin-top: 0;
            }
            h2 {
              margin-bottom: 3px;
              font-size: 20px;
              line-height: 1.2;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              font-size: 10.5px;
            }
            th {
              padding: 7px 8px;
              border-bottom: 1px solid #cbd5e1;
              text-align: left;
              font-size: 9px;
            }
            td {
              padding: 7px 8px;
              border-bottom: 1px solid #e2e8f0;
              line-height: 1.25;
            }
            tr {
              break-inside: avoid;
              page-break-inside: avoid;
            }
            .grid {
              display: grid;
            }
            .sm\\:grid-cols-2,
            .md\\:grid-cols-5,
            .lg\\:grid-cols-5,
            .xl\\:grid-cols-5 {
              grid-template-columns:
                repeat(
                  5,
                  minmax(0, 1fr)
                ) !important;
            }
            .grid-cols-2 {
              grid-template-columns:
                repeat(
                  2,
                  minmax(0, 1fr)
                );
            }
            .grid-cols-5 {
              grid-template-columns:
                repeat(
                  5,
                  minmax(0, 1fr)
                );
            }
            .gap-3,
            .gap-4,
            .gap-5,
            .gap-6 {
              gap: 8px;
            }
            .rounded-2xl,
            .rounded-3xl {
              border-radius: 8px;
            }
            .border {
              border: 1px solid #e2e8f0;
            }
            .border-slate-200 {
              border-color: #e2e8f0;
            }
            .bg-slate-50 {
              background: #f8fafc;
            }
            .p-4,
            .p-5,
            .p-6,
            .p-7 {
              padding: 8px;
            }
            .mt-1 {
              margin-top: 4px;
            }
            .mt-2 {
              margin-top: 6px;
            }
            .mt-4,
            .mt-5,
            .mt-6,
            .mt-7,
            .mt-8 {
              margin-top: 10px;
            }
            .font-semibold {
              font-weight: 600;
            }
            .font-bold {
              font-weight: 700;
            }
            .text-xs {
              font-size: 9px;
            }
            .text-sm {
              font-size: 10px;
            }
            .text-lg {
              font-size: 18px;
            }
            .text-xl {
              font-size: 20px;
            }
            .text-2xl {
              font-size: 22px;
              line-height: 1.1;
            }
            .text-3xl {
              font-size: 24px;
              line-height: 1.1;
            }
            .text-slate-500 {
              color: #64748b;
            }
            .text-slate-600 {
              color: #475569;
            }
            .text-slate-700 {
              color: #334155;
            }
            .text-slate-900 {
              color: #0f172a;
            }
            .text-emerald-700 {
              color: #047857;
            }
            .text-amber-700 {
              color: #b45309;
            }
            .text-sky-700 {
              color: #0369a1;
            }
            .text-violet-600,
            .text-violet-700 {
              color: #7c3aed;
            }
            .text-right {
              text-align: right;
            }
            .flex {
              display: flex;
            }
            .items-start {
              align-items: flex-start;
            }
            .items-center {
              align-items: center;
            }
            .justify-between {
              justify-content:
                space-between;
            }
            .flex-wrap {
              flex-wrap: wrap;
            }
            .attendance-report-print-hide {
              display: none !important;
            }
          </style>
        </head>
        <body>
          ${reportClone.outerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    window.setTimeout(
      () => {
        printWindow.print();
      },
      250,
    );
  }
  function clearFilters(): void {
    setDateFrom("");
    setDateTo("");
    setTeamId("");
    setShiftId("");
    setSelectedReport(null);
    setSelectedReportKey(null);
  }
  return (
    <section className="mt-8">
      <article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Attendance archive
          </p>
          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            History & Reports
          </h2>
          <p className="mt-2 max-w-3xl leading-6 text-slate-600">
            Find saved attendance by date,
            team or shift and open the
            employee-level group report.
          </p>
        </div>
        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Date From
            </span>
            <input
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setDateFrom(
                  event.target.value,
                );
              }}
              type="date"
              value={dateFrom}
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">
              Date To
            </span>
            <input
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"
              onChange={(event) => {
                setDateTo(
                  event.target.value,
                );
              }}
              type="date"
              value={dateTo}
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
              }}
              value={teamId}
            >
              <option value="">
                All teams
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
              }}
              value={shiftId}
            >
              <option value="">
                All shifts
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
        <div className="mt-5 flex flex-wrap gap-3">
          <button
            className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"
            disabled={isLoading}
            onClick={() => {
              void loadHistory();
            }}
            type="button"
          >
            {isLoading
              ? "Loading..."
              : "Apply filters"}
          </button>
          <button
            className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700"
            onClick={
              clearFilters
            }
            type="button"
          >
            Clear filters
          </button>
        </div>
      </article>
      {errorMessage ? (
        <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {errorMessage}
        </div>
      ) : null}
      <article className="mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-slate-950">
              Saved Reports
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {history?.total_reports ?? 0}
              {" "}report(s)
            </p>
          </div>
          <button
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
            disabled={isLoading}
            onClick={() => {
              void loadHistory();
            }}
            type="button"
          >
            Refresh
          </button>
        </div>
        {isLoading && !history ? (
          <div className="mt-6 rounded-2xl bg-slate-50 p-8 text-center text-slate-500">
            Loading attendance history...
          </div>
        ) : history?.items.length ? (
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-0">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="border-b border-slate-200 px-4 py-3">
                    Report
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Present
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Absent
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    On Leave
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Weekly Holiday
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Updated
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {history.items.map(
                  (item) => {
                    const key = [
                      item.attendance_date,
                      item.team_id,
                      item.shift_id,
                    ].join("-");
                    return (
                      <tr
                        key={key}
                        className="align-top"
                      >
                        <td className="border-b border-slate-100 px-4 py-4">
                          <p className="font-bold text-slate-900">
                            {formatDate(
                              item.attendance_date,
                            )}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            {item.team_name}
                            {" | "}
                            {item.shift_name}
                            {" | "}
                            {
                              item.summary
                                .total_members
                            }
                            {" "}member(s)
                          </p>
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 font-semibold text-emerald-700">
                          {
                            item.summary
                              .present
                          }
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 font-semibold text-red-700">
                          {
                            item.summary
                              .absent
                          }
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 font-semibold text-amber-700">
                          {
                            item.summary
                              .on_leave
                          }
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 font-semibold text-sky-700">
                          {
                            item.summary
                              .weekly_holiday
                          }
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 text-sm text-slate-500">
                          {formatDateTime(
                            item.last_updated_at,
                          )}
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4">
                          <button
                            className="rounded-xl border border-violet-300 px-4 py-2 text-sm font-semibold text-violet-700 disabled:opacity-50"
                            disabled={
                              isReportLoading
                              && selectedReportKey
                                === key
                            }
                            onClick={() => {
                              void openReport(
                                item,
                              );
                            }}
                            type="button"
                          >
                            {
                              isReportLoading
                              && selectedReportKey
                                === key
                                ? "Opening..."
                                : "View Report"
                            }
                          </button>
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
            No saved attendance report
            matches these filters.
          </div>
        )}
      </article>
      {selectedReport ? (
        <article className="attendance-report-print-area mt-7 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
                Group attendance report
              </p>
              <h2 className="mt-2 text-2xl font-bold text-slate-950">
                {selectedReport.team_name}
                {" | "}
                {selectedReport.shift_name}
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                {formatDate(
                  selectedReport
                    .attendance_date,
                )}
                {" | "}
                {
                  selectedReport
                    .summary
                    .total_members
                }
                {" "}member(s)
              </p>
            </div>
            <div className="flex flex-col items-end gap-3">
              <div className="attendance-report-print-hide flex flex-wrap justify-end gap-2">
                <button
                  className="rounded-xl border border-emerald-300 px-4 py-2 text-sm font-semibold text-emerald-700 disabled:opacity-50"
                  disabled={isExporting}
                  onClick={() => {
                    void downloadCsv();
                  }}
                  type="button"
                >
                  {isExporting
                    ? "Preparing CSV..."
                    : "Download CSV"}
                </button>
                <button
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
                  onClick={printReport}
                  type="button"
                >
                  Print Report
                </button>
              </div>
              <div className="text-right text-xs text-slate-500">
                Last updated
                <div className="mt-1 font-semibold text-slate-700">
                  {formatDateTime(
                    selectedReport
                      .last_updated_at,
                  )}
                </div>
              </div>
            </div>
          </div>
          <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {[
              {
                label:
                  "Team members",
                value:
                  selectedReport
                    .summary
                    .total_members,
              },
              {
                label: "Present",
                value:
                  selectedReport
                    .summary
                    .present,
              },
              {
                label: "Absent",
                value:
                  selectedReport
                    .summary
                    .absent,
              },
              {
                label: "On Leave",
                value:
                  selectedReport
                    .summary
                    .on_leave,
              },
              {
                label:
                  "Weekly Holiday",
                value:
                  selectedReport
                    .summary
                    .weekly_holiday,
              },
            ].map((item) => (
              <div
                className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                key={item.label}
              >
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {item.label}
                </p>
                <p className="mt-2 text-2xl font-bold text-slate-950">
                  {item.value}
                </p>
              </div>
            ))}
          </section>
          <div className="mt-7 overflow-x-auto">
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
                    Status
                  </th>
                  <th className="border-b border-slate-200 px-4 py-3">
                    Note
                  </th>
                </tr>
              </thead>
              <tbody>
                {selectedReport
                  .employees
                  .map(
                    (employee) => (
                      <tr
                        key={
                          employee.record_id
                        }
                      >
                        <td className="border-b border-slate-100 px-4 py-4">
                          <p className="font-bold text-slate-900">
                            {
                              employee
                                .full_name
                            }
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            {
                              employee
                                .employee_code
                            }
                          </p>
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 text-sm text-slate-600">
                          {
                            employee
                              .designation
                          }
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4">
                          <span
                            className={[
                              "inline-flex rounded-full px-2.5 py-1 text-xs font-bold",
                              statusClass(
                                employee.status,
                              ),
                            ].join(" ")}
                          >
                            {formatStatus(
                              employee.status,
                            )}
                          </span>
                          {/* Approved leave details */}
                          {employee.leave_type ? (
                            <div className="mt-2 max-w-64 text-xs leading-5 text-slate-500">
                              <div className="font-semibold text-amber-700">
                                {formatLeaveType(
                                  employee.leave_type,
                                )}
                              </div>
                              {(
                                employee.leave_from_date
                                && employee.leave_to_date
                              ) ? (
                                <div>
                                  {formatDate(
                                    employee.leave_from_date,
                                  )}
                                  {" to "}
                                  {formatDate(
                                    employee.leave_to_date,
                                  )}
                                </div>
                              ) : null}
                              {employee.leave_reason ? (
                                <div>
                                  Reason:{" "}
                                  {
                                    employee
                                      .leave_reason
                                  }
                                </div>
                              ) : null}
                            </div>
                          ) : null}
                        </td>
                        <td className="border-b border-slate-100 px-4 py-4 text-sm text-slate-600">
                          {
                            employee.note
                            || "-"
                          }
                        </td>
                      </tr>
                    ),
                  )}
              </tbody>
            </table>
          </div>
        </article>
      ) : null}
    </section>
  );
}
