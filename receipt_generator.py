from fpdf import FPDF
import os
from datetime import datetime

def create_pdf_receipt(client_name, files, price=0, tax=0, discount=0):
    os.makedirs("receipts", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    receipt_num = datetime.now().strftime("R-%Y%m%d-%H%M%S")
    safe_name = client_name.replace(' ', '_')
    receipt_path = f"receipts/{safe_name}_{date_str}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(10, 10, 10)
    pdf.set_font("Helvetica", size=10)

    # Logo (top left)
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=10, h=20)

    # Receipt number (top right)
    pdf.set_xy(150, 10)
    pdf.set_font("Helvetica", size=9, style='B')
    pdf.cell(0, 10, f"Receipt #: {receipt_num}", ln=True)

    # Business Name
    pdf.set_xy(10, 35)
    pdf.set_font("Helvetica", size=14, style='B')
    pdf.cell(0, 10, "Digital Product Organizer", ln=True)

    # Line under header
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.4)
    pdf.line(10, 48, 200, 48)

    # Client Info
    pdf.set_y(52)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, f"Client: {client_name}", ln=True)
    pdf.cell(0, 8, f"Date: {timestamp}", ln=True)

    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Files
    pdf.ln(4)
    pdf.set_font("Helvetica", size=10, style='B')
    pdf.cell(0, 8, "Files Sent:", ln=True)

    pdf.set_font("Helvetica", size=10)
    for file_path in files:
        filename = os.path.basename(file_path)
        pdf.cell(0, 6, f"- {filename}", ln=True)

    # Totals
    pdf.ln(4)
    pdf.set_font("Helvetica", size=10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.cell(0, 8, f"Price: ${price:.2f}", ln=True)
    pdf.cell(0, 8, f"Tax: ${tax:.2f}", ln=True)
    pdf.cell(0, 8, f"Discount: -${discount:.2f}", ln=True)

    total = price + tax - discount
    pdf.set_font("Helvetica", size=11, style='B')
    pdf.cell(0, 10, f"Total: ${total:.2f}", ln=True)

    # Footer spacing (no email or contact info)
    pdf.set_y(-30)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.set_font("Helvetica", size=8)
    pdf.ln(2)
    pdf.cell(0, 6, "Thank you for your purchase!", ln=True, align='C')

    pdf.output(receipt_path)
    return receipt_path
