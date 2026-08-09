from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_LEFT,
    TA_RIGHT,
)
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
from backend.app.schemas.attendance_history import (
    AttendanceHistoryReportRead,
)
def _format_date(value) -> str:
    return value.strftime(
        "%d %b %Y"
    )
def _format_status(
    value: str,
) -> str:
    return (
        value.replace(
            "_",
            " ",
        )
        .title()
    )
def _format_leave_type(
    value: str,
) -> str:
    labels = {
        "casual": "Casual Leave",
        "sick": "Sick Leave",
        "annual": "Annual Leave",
        "other": "Other Leave",
    }
    return labels.get(
        value,
        value.replace(
            "_",
            " ",
        ).title(),
    )
def _status_colors(
    status: str,
):
    mapping = {
        "present": (
            colors.HexColor(
                "#D1FAE5"
            ),
            colors.HexColor(
                "#047857"
            ),
        ),
        "absent": (
            colors.HexColor(
                "#FEE2E2"
            ),
            colors.HexColor(
                "#B91C1C"
            ),
        ),
        "on_leave": (
            colors.HexColor(
                "#FEF3C7"
            ),
            colors.HexColor(
                "#B45309"
            ),
        ),
        "weekly_holiday": (
            colors.HexColor(
                "#E0F2FE"
            ),
            colors.HexColor(
                "#0369A1"
            ),
        ),
    }
    return mapping.get(
        status,
        (
            colors.HexColor(
                "#F1F5F9"
            ),
            colors.HexColor(
                "#334155"
            ),
        ),
    )
def build_attendance_report_pdf(
    report: AttendanceHistoryReportRead,
) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=11 * mm,
        bottomMargin=16 * mm,
        title=(
            "Attendance Report - "
            f"{report.team_name} - "
            f"{report.attendance_date.isoformat()}"
        ),
        author="PeopleMind AI",
        subject="Attendance Report",
    )
    styles = getSampleStyleSheet()
    eyebrow_style = ParagraphStyle(
        "AttendanceEyebrow",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor(
            "#7C3AED"
        ),
        spaceAfter=3,
    )
    title_style = ParagraphStyle(
        "AttendanceTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=20,
        textColor=colors.HexColor(
            "#0F172A"
        ),
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "AttendanceSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor(
            "#475569"
        ),
    )
    updated_style = ParagraphStyle(
        "AttendanceUpdated",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        alignment=TA_RIGHT,
        textColor=colors.HexColor(
            "#64748B"
        ),
    )
    summary_label_style = ParagraphStyle(
        "AttendanceSummaryLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.8,
        leading=8,
        textColor=colors.HexColor(
            "#475569"
        ),
    )
    summary_value_style = ParagraphStyle(
        "AttendanceSummaryValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=19,
        textColor=colors.HexColor(
            "#0F172A"
        ),
        spaceBefore=4,
    )
    cell_style = ParagraphStyle(
        "AttendanceCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10,
        textColor=colors.HexColor(
            "#334155"
        ),
    )
    employee_style = ParagraphStyle(
        "AttendanceEmployee",
        parent=cell_style,
        fontName="Helvetica",
    )
    header_cell_style = ParagraphStyle(
        "AttendanceTableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.7,
        leading=8,
        textColor=colors.HexColor(
            "#475569"
        ),
        alignment=TA_LEFT,
    )
    story = []
    header_table = Table(
        [
            [
                [
                    Paragraph(
                        "GROUP ATTENDANCE REPORT",
                        eyebrow_style,
                    ),
                    Paragraph(
                        (
                            f"{escape(report.team_name)}"
                            " | "
                            f"{escape(report.shift_name)}"
                        ),
                        title_style,
                    ),
                    Paragraph(
                        (
                            f"{_format_date(report.attendance_date)}"
                            " | "
                            f"{report.summary.total_members} "
                            "member(s)"
                        ),
                        subtitle_style,
                    ),
                ],
                Paragraph(
                    (
                        "Last updated<br/>"
                        "<b>"
                        + escape(
                            report.last_updated_at
                            .strftime(
                                "%d %b %Y, %I:%M %p"
                            )
                        )
                        + "</b>"
                    ),
                    updated_style,
                ),
            ]
        ],
        colWidths=[
            132 * mm,
            43 * mm,
        ],
    )
    header_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    1.2,
                    colors.HexColor(
                        "#E2E8F0"
                    ),
                ),
            ]
        )
    )
    story.append(
        header_table
    )
    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )
    summary_items = [
        (
            "TEAM MEMBERS",
            report.summary.total_members,
        ),
        (
            "PRESENT",
            report.summary.present,
        ),
        (
            "ABSENT",
            report.summary.absent,
        ),
        (
            "ON LEAVE",
            report.summary.on_leave,
        ),
        (
            "WEEKLY HOLIDAY",
            report.summary.weekly_holiday,
        ),
    ]
    summary_cells = []
    for label, value in summary_items:
        summary_cells.append(
            [
                Paragraph(
                    label,
                    summary_label_style,
                ),
                Paragraph(
                    str(value),
                    summary_value_style,
                ),
            ]
        )
    summary_table = Table(
        [
            summary_cells
        ],
        colWidths=[
            35 * mm
            for _ in summary_cells
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
                        "#F8FAFC"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor(
                        "#DBE3EE"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#E2E8F0"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
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
            4 * mm,
        )
    )
    table_data = [
        [
            Paragraph(
                "EMPLOYEE",
                header_cell_style,
            ),
            Paragraph(
                "DESIGNATION",
                header_cell_style,
            ),
            Paragraph(
                "STATUS",
                header_cell_style,
            ),
            Paragraph(
                "LEAVE DETAILS",
                header_cell_style,
            ),
            Paragraph(
                "NOTE",
                header_cell_style,
            ),
        ]
    ]
    for employee in report.employees:
        employee_text = (
            "<b>"
            + escape(
                employee.full_name
            )
            + "</b>"
            + "<br/>"
            + "<font size='6.5' color='#64748B'>"
            + escape(
                employee.employee_code
            )
            + "</font>"
        )
        leave_details = "-"
        if employee.leave_type:
            leave_parts = [
                "<b>"
                + escape(
                    _format_leave_type(
                        employee.leave_type
                    )
                )
                + "</b>"
            ]
            if (
                employee.leave_from_date
                is not None
                and employee.leave_to_date
                is not None
            ):
                leave_parts.append(
                    (
                        _format_date(
                            employee.leave_from_date
                        )
                        + " to "
                        + _format_date(
                            employee.leave_to_date
                        )
                    )
                )
            if employee.leave_reason:
                leave_parts.append(
                    (
                        "Reason: "
                        + escape(
                            employee.leave_reason
                        )
                    )
                )
            leave_details = (
                "<br/>".join(
                    leave_parts
                )
            )
        table_data.append(
            [
                Paragraph(
                    employee_text,
                    employee_style,
                ),
                Paragraph(
                    escape(
                        employee.designation
                    ),
                    cell_style,
                ),
                Paragraph(
                    escape(
                        _format_status(
                            employee.status
                        )
                    ),
                    cell_style,
                ),
                Paragraph(
                    leave_details,
                    cell_style,
                ),
                Paragraph(
                    (
                        escape(
                            employee.note
                        )
                        if employee.note
                        else "-"
                    ),
                    cell_style,
                ),
            ]
        )
    employee_table = LongTable(
        table_data,
        repeatRows=1,
        colWidths=[
            34 * mm,
            49 * mm,
            26 * mm,
            43 * mm,
            23 * mm,
        ],
    )
    table_style_commands = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor(
                "#F8FAFC"
            ),
        ),
        (
            "LINEBELOW",
            (0, 0),
            (-1, 0),
            0.8,
            colors.HexColor(
                "#CBD5E1"
            ),
        ),
        (
            "LINEBELOW",
            (0, 1),
            (-1, -1),
            0.35,
            colors.HexColor(
                "#E2E8F0"
            ),
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            5,
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
    for row_index, employee in enumerate(
        report.employees,
        start=1,
    ):
        background, text_color = (
            _status_colors(
                employee.status
            )
        )
        table_style_commands.extend(
            [
                (
                    "BACKGROUND",
                    (2, row_index),
                    (2, row_index),
                    background,
                ),
                (
                    "TEXTCOLOR",
                    (2, row_index),
                    (2, row_index),
                    text_color,
                ),
            ]
        )
    employee_table.setStyle(
        TableStyle(
            table_style_commands
        )
    )
    story.append(
        employee_table
    )
    def draw_footer(
        canvas,
        doc,
    ) -> None:
        canvas.saveState()
        canvas.setTitle(
            (
                "Attendance Report - "
                f"{report.team_name} - "
                f"{report.attendance_date.isoformat()}"
            )
        )
        canvas.setAuthor(
            "PeopleMind AI"
        )
        canvas.setStrokeColor(
            colors.HexColor(
                "#E2E8F0"
            )
        )
        canvas.setLineWidth(
            0.5
        )
        canvas.line(
            document.leftMargin,
            11 * mm,
            A4[0]
            - document.rightMargin,
            11 * mm,
        )
        canvas.setFont(
            "Helvetica",
            7,
        )
        canvas.setFillColor(
            colors.HexColor(
                "#64748B"
            )
        )
        canvas.drawString(
            document.leftMargin,
            7 * mm,
            (
                "PeopleMind AI"
                " | Attendance Management"
            ),
        )
        canvas.drawRightString(
            A4[0]
            - document.rightMargin,
            7 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()
    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )
    pdf_bytes = (
        buffer.getvalue()
    )
    buffer.close()
    return pdf_bytes
