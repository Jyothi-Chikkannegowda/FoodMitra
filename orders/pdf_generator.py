from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io

def generate_receipt_pdf(order, payment):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    orange = colors.HexColor('#ff6b35')
    dark = colors.HexColor('#2c2c2a')
    light_gray = colors.HexColor('#f5f5f5')
    green = colors.HexColor('#1D9E75')

    normal_center = ParagraphStyle('nc', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)
    section_title_style = ParagraphStyle('st', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=orange, spaceAfter=6)
    success_style = ParagraphStyle('ss', parent=styles['Normal'], fontSize=13, fontName='Helvetica-Bold', textColor=green, alignment=TA_CENTER)

    # HEADER using table to avoid overlap
    elements.append(Spacer(1, 10))
    # Header table with 2 separate rows
    header_data = [
    [Paragraph('<font name="Helvetica-Bold" size="26" color="#ff6b35">FoodMitra</font>', 
               ParagraphStyle('b', parent=styles['Normal'], alignment=TA_CENTER))],
    [Spacer(1, 8)],
    [Paragraph('<font name="Helvetica" size="11" color="#888888">Home Cooked Food Sharing Network</font>', 
               ParagraphStyle('t', parent=styles['Normal'], alignment=TA_CENTER))],
]
    header_table = Table(header_data, colWidths=[480])
    header_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('PADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width='100%', thickness=2, color=orange))
    elements.append(Spacer(1, 12))

    # RECEIPT TITLE
    elements.append(Paragraph(
        '<font name="Helvetica-Bold" size="13" color="#1D9E75">Payment Successful!</font>',
        ParagraphStyle('ps', parent=styles['Normal'], alignment=TA_CENTER, spaceAfter=6)
    ))
    elements.append(Paragraph(
        '<font name="Helvetica-Bold" size="16" color="#2c2c2a">ORDER RECEIPT</font>',
        ParagraphStyle('or', parent=styles['Normal'], alignment=TA_CENTER, spaceAfter=10)
    ))
    elements.append(Spacer(1, 10))

    # ORDER INFO TABLE
    order_data = [
        ['Order ID', f'#{order.id}'],
        ['Payment ID', payment.transaction_id],
        ['Payment Status', 'SUCCESS'],
        ['Order Date', order.order_time.strftime('%d %B %Y, %I:%M %p')],
        ['Delivery Type', 'Home Delivery' if order.delivery_type == 'delivery' else 'Self Pickup'],
    ]
    order_table = Table(order_data, colWidths=[180, 300])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e8e8e8')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, light_gray]),
        ('TEXTCOLOR', (1, 2), (1, 2), green),
        ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 14))

    # FOOD DETAILS
    elements.append(Paragraph('FOOD DETAILS', section_title_style))
    food_data = [
        ['Food Item', 'Quantity', 'Price per plate', 'Subtotal'],
        [
            order.menu_item.food_name,
            str(order.quantity),
            f'Rs.{float(order.menu_item.price):.2f}',
            f'Rs.{float(order.menu_item.price) * int(order.quantity):.2f}'
        ],
    ]
    food_table = Table(food_data, colWidths=[200, 80, 100, 100])
    food_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e8e8e8')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(food_table)
    elements.append(Spacer(1, 14))

    # BILL BREAKDOWN
    elements.append(Paragraph('BILL BREAKDOWN', section_title_style))
    food_subtotal = float(order.menu_item.price) * int(order.quantity)
    delivery_charge = 20 if order.delivery_type == 'delivery' else 0
    platform_fee = 2
    gst = round((food_subtotal + delivery_charge + platform_fee) * 0.05, 2)

    bill_data = [
        ['Item Total', f'Rs.{food_subtotal:.2f}'],
        ['Delivery Charge', f'Rs.{delivery_charge}' if delivery_charge > 0 else 'FREE'],
        ['Platform Fee', f'Rs.{platform_fee}'],
        ['GST (5%)', f'Rs.{gst}'],
        ['TOTAL AMOUNT', f'Rs.{float(payment.amount):.2f}'],
    ]
    bill_table = Table(bill_data, colWidths=[380, 100])
    bill_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e8e8e8')),
        ('BACKGROUND', (0, -1), (-1, -1), orange),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, orange),
    ]))
    elements.append(bill_table)
    elements.append(Spacer(1, 14))

    # COOK DETAILS
    elements.append(Paragraph('COOK DETAILS', section_title_style))
    cook_data = [
        ['Cook Name', f'{order.cook.user.first_name} {order.cook.user.last_name}'],
        ['Speciality', order.cook.speciality or 'Home Cooking'],
        ['Address', order.cook.home_address],
        ['Verified', 'Yes' if order.cook.is_verified else 'Pending'],
    ]
    cook_table = Table(cook_data, colWidths=[180, 300])
    cook_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e8e8e8')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, light_gray]),
    ]))
    elements.append(cook_table)
    elements.append(Spacer(1, 14))

    # CUSTOMER DETAILS
    elements.append(Paragraph('CUSTOMER DETAILS', section_title_style))
    customer_data = [
        ['Name', f'{order.customer.first_name} {order.customer.last_name}'],
        ['Email', order.customer.email],
        ['Order Status', order.status.upper()],
    ]
    customer_table = Table(customer_data, colWidths=[180, 300])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e8e8e8')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, light_gray]),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # FOOTER
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e8e8e8')))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        'Thank you for ordering from FoodMitra! Enjoy your home cooked meal.',
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#888888'))
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        '2026 FoodMitra - Home Cooked Food Sharing Network | Made with love in India',
        ParagraphStyle('footer2', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#aaaaaa'))
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer