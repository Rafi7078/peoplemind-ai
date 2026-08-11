import csv
from io import (
    BytesIO,
    StringIO,
)
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from backend.app.schemas.attendance_employee_monthly import (
    AttendanceEmployeeMonthlyReportRead,
)
def _csv_safe(
    value: object | None,
) -> str:
    if value is None:
        return ""
    text = str(value)
    if (
        text
        and text[0]
        in {
            "=",
            "+",
            "-",
            "@",
        }
    ):
        return "'" + text
    return text
def _status_label(
    value: str,
) -> str:
    labels = {
        "present": "Present",
        "absent": "Absent",
        "on_leave": "On Leave",
        "weekly_holiday":
            "Weekly Holiday",
        "not_recorded":
            "Not Recorded",
    }
    return labels.get(
        value,
        value.replace(
            "_",
            " ",
        ).title(),
    )
def build_monthly_csv(
    report: AttendanceEmployeeMonthlyReportRead,
) -> bytes:
    output = StringIO(
        newline=""
    )
    writer = csv.writer(
        output
    )
    writer.writerow(
        [
            "Employee Monthly Attendance Report",
        ]
    )
    writer.writerow(
        [
            "Employee Code",
            _csv_safe(
                report.employee_code
            ),
        ]
    )
    writer.writerow(
        [
            "Employee Name",
            _csv_safe(
                report.full_name
            ),
        ]
    )
    writer.writerow(
        [
            "Designation",
            _csv_safe(
                report.designation
            ),
        ]
    )
    writer.writerow(
        [
            "Team",
            _csv_safe(
                report.team_name
            ),
        ]
    )
    writer.writerow(
        [
            "Shift",
            _csv_safe(
                report.shift_name
            ),
        ]
    )
    writer.writerow(
        [
            "Reporting Month",
            report.month_label,
        ]
    )
    writer.writerow([])
    writer.writerow(
        [
            "Attendance Rate",
            (
                f"{report.summary.attendance_rate:.2f}%"
            ),
            "Present",
            report.summary.present,
            "Absent",
            report.summary.absent,
            "On Leave",
            report.summary.on_leave,
            "Weekly Holiday",
            report.summary.weekly_holiday,
            "Not Recorded",
            report.summary.not_recorded_days,
        ]
    )
    writer.writerow([])
    writer.writerow(
        [
            "Date",
            "Weekday",
            "Status",
            "Recorded",
            "Team",
            "Shift",
            "Leave Type",
            "Leave Reason",
            "Leave From",
            "Leave To",
            "Note",
        ]
    )
    for day in report.days:
        writer.writerow(
            [
                day.attendance_date.isoformat(),
                day.weekday,
                _status_label(
                    day.status
                ),
                (
                    "Yes"
                    if day.is_recorded
                    else "No"
                ),
                _csv_safe(
                    day.team_name
                ),
                _csv_safe(
                    day.shift_name
                ),
                _csv_safe(
                    day.leave_type
                ),
                _csv_safe(
                    day.leave_reason
                ),
                (
                    day.leave_from_date
                    .isoformat()
                    if day.leave_from_date
                    is not None
                    else ""
                ),
                (
                    day.leave_to_date
                    .isoformat()
                    if day.leave_to_date
                    is not None
                    else ""
                ),
                _csv_safe(
                    day.note
                ),
            ]
        )
    return (
        "\ufeff"
        + output.getvalue()
    ).encode(
        "utf-8"
    )
def build_monthly_pdf(
    report: AttendanceEmployeeMonthlyReportRead,
) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    small = ParagraphStyle(
        "MonthlySmall",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor(
            "#475569"
        ),
    )
    cell = ParagraphStyle(
        "MonthlyCell",
        parent=small,
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor(
            "#334155"
        ),
    )
    heading = ParagraphStyle(
        "MonthlyHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=colors.HexColor(
            "#0f172a"
        ),
        spaceAfter=3,
    )
    eyebrow = ParagraphStyle(
        "MonthlyEyebrow",
        parent=small,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor(
            "#7c3aed"
        ),
    )
    summary_number = ParagraphStyle(
        "MonthlySummaryNumber",
        parent=small,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=colors.HexColor(
            "#0f172a"
        ),
        alignment=TA_CENTER,
    )
    summary_label = ParagraphStyle(
        "MonthlySummaryLabel",
        parent=small,
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor(
            "#64748b"
        ),
        alignment=TA_CENTER,
    )
    def footer(
        canvas,
        document,
    ) -> None:
        canvas.saveState()
        width, _ = A4
        canvas.setStrokeColor(
            colors.HexColor(
                "#e2e8f0"
            )
        )
        canvas.line(
            10 * mm,
            10 * mm,
            width - 10 * mm,
            10 * mm,
        )
        canvas.setFont(
            "Helvetica",
            7,
        )
        canvas.setFillColor(
            colors.HexColor(
                "#64748b"
            )
        )
        canvas.drawString(
            10 * mm,
            6 * mm,
            (
                "PeopleMind AI | "
                "Employee Attendance Report"
            ),
        )
        canvas.drawRightString(
            width - 10 * mm,
            6 * mm,
            f"Page {document.page}",
        )
        canvas.restoreState()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=11 * mm,
        bottomMargin=15 * mm,
        title=(
            f"{report.full_name} "
            f"{report.month_label} "
            "Attendance Report"
        ),
        author="PeopleMind AI",
    )
    story = []
    story.append(
        Paragraph(
            "EMPLOYEE MONTHLY ATTENDANCE REPORT",
            eyebrow,
        )
    )
    story.append(
        Paragraph(
            escape(
                report.full_name
            ),
            heading,
        )
    )
    story.append(
        Paragraph(
            escape(
                (
                    f"{report.employee_code} | "
                    f"{report.designation}"
                )
            ),
            small,
        )
    )
    story.append(
        Paragraph(
            escape(
                (
                    f"{report.team_name} | "
                    f"{report.shift_name} | "
                    f"{report.month_label}"
                )
            ),
            small,
        )
    )
    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )
    summary_data = [
        [
            [
                Paragraph(
                    "ATTENDANCE RATE",
                    summary_label,
                ),
                Paragraph(
                    (
                        f"{report.summary.attendance_rate:.1f}%"
                    ),
                    summary_number,
                ),
            ],
            [
                Paragraph(
                    "PRESENT",
                    summary_label,
                ),
                Paragraph(
                    str(
                        report.summary.present
                    ),
                    summary_number,
                ),
            ],
            [
                Paragraph(
                    "ABSENT",
                    summary_label,
                ),
                Paragraph(
                    str(
                        report.summary.absent
                    ),
                    summary_number,
                ),
            ],
            [
                Paragraph(
                    "ON LEAVE",
                    summary_label,
                ),
                Paragraph(
                    str(
                        report.summary.on_leave
                    ),
                    summary_number,
                ),
            ],
            [
                Paragraph(
                    "HOLIDAY",
                    summary_label,
                ),
                Paragraph(
                    str(
                        report.summary.weekly_holiday
                    ),
                    summary_number,
                ),
            ],
            [
                Paragraph(
                    "NOT RECORDED",
                    summary_label,
                ),
                Paragraph(
                    str(
                        report.summary.not_recorded_days
                    ),
                    summary_number,
                ),
            ],
        ]
    ]
    summary_table = Table(
        summary_data,
        colWidths=[
            30 * mm,
            30 * mm,
            30 * mm,
            30 * mm,
            30 * mm,
            30 * mm,
        ],
    )
    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#f8fafc"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor(
                        "#cbd5e1"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor(
                        "#e2e8f0"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )
    story.append(
        summary_table
    )
    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )
    story.append(
        Paragraph(
            (
                "Attendance Rate = Present / "
                "(Present + Absent + On Leave). "
                "Weekly holidays are excluded."
            ),
            small,
        )
    )
    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )
    table_data = [
        [
            Paragraph(
                "DATE",
                cell,
            ),
            Paragraph(
                "DAY",
                cell,
            ),
            Paragraph(
                "STATUS",
                cell,
            ),
            Paragraph(
                "LEAVE DETAILS",
                cell,
            ),
            Paragraph(
                "NOTE",
                cell,
            ),
        ]
    ]
    for day in report.days:
        leave_details = "-"
        if day.leave_type:
            leave_parts = [
                day.leave_type
                .replace(
                    "_",
                    " ",
                )
                .title()
            ]
            if (
                day.leave_from_date
                is not None
                and day.leave_to_date
                is not None
            ):
                leave_parts.append(
                    (
                        f"{day.leave_from_date.strftime('%d %b %Y')} "
                        f"to "
                        f"{day.leave_to_date.strftime('%d %b %Y')}"
                    )
                )
            if day.leave_reason:
                leave_parts.append(
                    day.leave_reason
                )
            leave_details = "<br/>".join(
                escape(part)
                for part in leave_parts
            )
        table_data.append(
            [
                Paragraph(
                    day.attendance_date.strftime(
                        "%d %b %Y"
                    ),
                    cell,
                ),
                Paragraph(
                    escape(
                        day.weekday
                    ),
                    cell,
                ),
                Paragraph(
                    escape(
                        _status_label(
                            day.status
                        )
                    ),
                    cell,
                ),
                Paragraph(
                    leave_details,
                    cell,
                ),
                Paragraph(
                    escape(
                        day.note or "-"
                    ),
                    cell,
                ),
            ]
        )
    attendance_table = LongTable(
        table_data,
        repeatRows=1,
        colWidths=[
            28 * mm,
            23 * mm,
            32 * mm,
            62 * mm,
            35 * mm,
        ],
    )
    attendance_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#f1f5f9"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#475569"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor(
                        "#e2e8f0"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )
    story.append(
        attendance_table
    )
    document.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )
    return buffer.getvalue()
