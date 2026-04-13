from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from django.conf import settings
from payments.models import Invoice
import os


# Brand colours
PRIMARY = colors.HexColor('#1a3a5c')
ACCENT = colors.HexColor('#2e7d32')
LIGHT_GREY = colors.HexColor('#f5f5f5')
MID_GREY = colors.HexColor('#9e9e9e')
DARK = colors.HexColor('#212121')
WHITE = colors.white


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── HEADER BLOCK ──────────────────────────────────────────────────────────
    company_name = getattr(settings, 'COMPANY_NAME', 'Attribute Land Survey & Consultants')
    company_address = getattr(settings, 'COMPANY_ADDRESS', 'Nairobi, Kenya')
    company_phone = getattr(settings, 'COMPANY_PHONE', '+254 700 000 000')
    company_email = getattr(settings, 'COMPANY_EMAIL', 'info@attributesurvey.co.ke')

    header_data = [
        [
            Paragraph(f'<font color="#1a3a5c"><b>{company_name}</b></font>',
                      ParagraphStyle('co', fontName='Helvetica-Bold', fontSize=14, textColor=PRIMARY)),
            Paragraph('<font color="#1a3a5c"><b>INVOICE</b></font>',
                      ParagraphStyle('inv', fontName='Helvetica-Bold', fontSize=22, textColor=PRIMARY, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(f'{company_address}<br/>{company_phone}<br/>{company_email}',
                      ParagraphStyle('addr', fontName='Helvetica', fontSize=8, textColor=MID_GREY, leading=12)),
            Paragraph(
                f'<font color="#555555">Invoice No:</font> <b>INV-{invoice.invoice_number}</b><br/>'
                f'<font color="#555555">Date:</font> {invoice.created_at.strftime("%d %B %Y")}<br/>'
                f'<font color="#555555">Due Date:</font> {invoice.due_date.strftime("%d %B %Y")}<br/>'
                f'<font color="#555555">Status:</font> <b>{invoice.get_status_display().upper()}</b>',
                ParagraphStyle('meta', fontName='Helvetica', fontSize=9, alignment=TA_RIGHT, leading=14),
            ),
        ],
    ]
    header_table = Table(header_data, colWidths=[100 * mm, 80 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY))
    story.append(Spacer(1, 6 * mm))

    # ── BILL TO ───────────────────────────────────────────────────────────────
    client = invoice.client
    user = client.user
    bill_to = [
        [
            Paragraph('<b>BILL TO</b>', ParagraphStyle('bt', fontName='Helvetica-Bold', fontSize=8, textColor=MID_GREY)),
            Paragraph('<b>CLIENT ID</b>', ParagraphStyle('ci', fontName='Helvetica-Bold', fontSize=8, textColor=MID_GREY)),
        ],
        [
            Paragraph(
                f'<b>{user.get_full_name()}</b><br/>'
                f'{user.email}<br/>'
                f'{user.phone}<br/>'
                f'{user.address or ""}',
                ParagraphStyle('bto', fontName='Helvetica', fontSize=9, leading=14),
            ),
            Paragraph(
                f'<b>{client.client_id}</b><br/>'
                f'{client.company_name or "Individual"}',
                ParagraphStyle('cid', fontName='Helvetica', fontSize=9, leading=14),
            ),
        ],
    ]
    bt_table = Table(bill_to, colWidths=[100 * mm, 80 * mm])
    bt_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(bt_table)
    story.append(Spacer(1, 8 * mm))

    # ── SERVICES TABLE ────────────────────────────────────────────────────────
    col_headers = ['#', 'Description', 'Amount (KES)']
    service_name = invoice.quotation.service.name if invoice.quotation else 'Professional Services'
    location = invoice.quotation.property_location if invoice.quotation else ''

    rows = [col_headers]
    rows.append([
        '1',
        Paragraph(
            f'<b>{service_name}</b><br/>'
            f'<font color="#555555" size="8">Location: {location}</font><br/>'
            f'<font color="#555555" size="8">{invoice.description[:200]}</font>',
            ParagraphStyle('desc', fontName='Helvetica', fontSize=9, leading=13),
        ),
        f'{invoice.amount:,.2f}',
    ])

    svc_table = Table(rows, colWidths=[12 * mm, 130 * mm, 38 * mm])
    svc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(svc_table)
    story.append(Spacer(1, 4 * mm))

    # ── TOTALS ────────────────────────────────────────────────────────────────
    vat = invoice.vat_amount
    total = invoice.total_with_vat
    totals_data = [
        ['', 'Subtotal:', f'KES {invoice.amount:,.2f}'],
        ['', 'VAT (16%):', f'KES {vat:,.2f}'],
        ['', Paragraph('<b>TOTAL DUE:</b>', ParagraphStyle('td', fontName='Helvetica-Bold', fontSize=10)),
         Paragraph(f'<b>KES {total:,.2f}</b>', ParagraphStyle('ta', fontName='Helvetica-Bold', fontSize=10, alignment=TA_RIGHT))],
    ]
    if invoice.amount_paid > 0:
        totals_data.append(['', 'Amount Paid:', f'KES {invoice.amount_paid:,.2f}'])
        totals_data.append(['', Paragraph('<b>Balance Due:</b>', ParagraphStyle('bd', fontName='Helvetica-Bold', fontSize=10, textColor=colors.red)),
                            Paragraph(f'<b>KES {invoice.balance_due:,.2f}</b>',
                                      ParagraphStyle('bda', fontName='Helvetica-Bold', fontSize=10, textColor=colors.red, alignment=TA_RIGHT))])

    totals_table = Table(totals_data, colWidths=[12 * mm, 130 * mm, 38 * mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, -1), (-1, -1), 1, PRIMARY),
        ('BACKGROUND', (1, -1), (-1, -1), LIGHT_GREY),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 8 * mm))

    # ── PAYMENT INSTRUCTIONS ─────────────────────────────────────────────────
    if invoice.status != Invoice.STATUS_PAID:
        pay_style = ParagraphStyle('pay', fontName='Helvetica', fontSize=9, leading=14, borderPad=6,
                                   borderColor=colors.HexColor('#bbdefb'), borderWidth=1,
                                   backColor=colors.HexColor('#e3f2fd'))
        story.append(Paragraph(
            '<b>Payment Instructions</b><br/>'
            'M-PESA Paybill: <b>123456</b> | Account: Your Client ID<br/>'
            'Bank: <b>Equity Bank</b> | Account: <b>0123456789</b> | Branch: Nairobi CBD<br/>'
            'Please quote your invoice number as the payment reference.',
            pay_style
        ))
        story.append(Spacer(1, 6 * mm))

    if invoice.status == Invoice.STATUS_PAID:
        story.append(Paragraph(
            f'✓ PAID on {invoice.paid_at.strftime("%d %B %Y")} via {invoice.payment_method} | Ref: {invoice.payment_reference}',
            ParagraphStyle('paid', fontName='Helvetica-Bold', fontSize=10, textColor=ACCENT,
                           borderColor=ACCENT, borderWidth=1, borderPad=6, backColor=colors.HexColor('#e8f5e9')),
        ))
        story.append(Spacer(1, 6 * mm))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=1, color=MID_GREY))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f'Thank you for choosing {company_name}. This invoice was generated electronically and is valid without a signature.',
        ParagraphStyle('foot', fontName='Helvetica', fontSize=8, textColor=MID_GREY, alignment=TA_CENTER),
    ))

    doc.build(story)
    return buffer.getvalue()
