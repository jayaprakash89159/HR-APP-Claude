from io import BytesIO
from decimal import Decimal

from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph


def generate_payslip_pdf(payslip):
    """Generate a stored PDF for a payslip without making the file public."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    period = payslip.payroll_period
    employee = payslip.employee
    rows = [
        ['WorkSphere HR', 'PAYSLIP'],
        ['Employee', employee.get_full_name()],
        ['Employee code', employee.employee_code],
        ['Department', employee.department.name if employee.department_id else '-'],
        ['Designation', employee.designation.name if employee.designation_id else '-'],
        ['Period', f'{period.year}-{period.month:02d}'],
        ['Payslip number', payslip.payslip_number],
    ]
    story = [Paragraph('WorkSphere HR', styles['Title']), Paragraph('Monthly Salary Payslip', styles['Heading2']), Spacer(1, 6 * mm)]
    info = Table(rows, colWidths=[48 * mm, 125 * mm])
    info.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#d1d5db')),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#eff6ff')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info)
    story.append(Spacer(1, 8 * mm))

    earnings = [
        ['Earnings', 'Amount'],
        ['Basic', _money(payslip.basic)],
        ['HRA', _money(payslip.hra)],
        ['Special allowance', _money(payslip.special_allowance)],
        ['Medical allowance', _money(payslip.medical_allowance)],
        ['Conveyance', _money(payslip.conveyance_allowance)],
        ['Gross earnings', _money(payslip.gross_earnings)],
    ]
    deductions = [
        ['Deductions', 'Amount'],
        ['LOP', _money(payslip.lop_amount)],
        ['PF', _money(payslip.pf_employee)],
        ['ESI', _money(payslip.esi_employee)],
        ['Professional tax', _money(payslip.professional_tax)],
        ['TDS', _money(payslip.tds)],
        ['Total deductions', _money(payslip.total_deductions)],
    ]
    for data in (earnings, deductions):
        table = Table(data, colWidths=[48 * mm, 45 * mm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#d1d5db')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.extend([table, Spacer(1, 6 * mm)])

    attendance = [
        ['Attendance summary', 'Days'],
        ['Working days', str(payslip.total_working_days)],
        ['Present', str(payslip.days_present)],
        ['Approved leave', str(payslip.days_on_leave)],
        ['Absent', str(payslip.days_absent)],
        ['LOP', str(payslip.days_lop)],
        ['Overtime hours', str(payslip.overtime_hours)],
    ]
    table = Table(attendance, colWidths=[48 * mm, 45 * mm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#d1d5db')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 8 * mm), Paragraph(f'Net salary: Rs. {_money(payslip.net_salary)}', styles['Heading2'])])
    document.build(story)
    content = buffer.getvalue()
    payslip.payslip_pdf.save(f'{payslip.payslip_number}.pdf', ContentFile(content), save=False)
    payslip.save(update_fields=['payslip_pdf', 'updated_at'])
    return content


def _money(value: Decimal) -> str:
    return f'{Decimal(value):,.2f}'
