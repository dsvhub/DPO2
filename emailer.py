import smtplib
import os
from email.message import EmailMessage  # <-- add this line
from logger import logger
from config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT


# emailer.py
from utils import load_email_config



config = load_email_config()

EMAIL_SENDER = config.get("EMAIL_SENDER")
EMAIL_PASSWORD = config.get("EMAIL_PASSWORD")
SMTP_SERVER = config.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = config.get("SMTP_PORT", 587)




def send_files_with_receipt(to_email, client_name, file_paths, receipt_path=None, body=None):
    msg = EmailMessage()
    msg['Subject'] = f"Your Files and Receipt - {client_name}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email

    # Use provided email body or fallback
    msg.set_content(body or f"Hi {client_name},\n\nAttached are your files and receipt.\nThank you!")

    try:
        all_attachments = list(file_paths)  # copy to avoid modifying original list
        if receipt_path:
            all_attachments.append(receipt_path)

        for path in all_attachments:
            if not path:
                logger.warning("Skipping NoneType attachment path")
                continue
            with open(path, 'rb') as f:
                content = f.read()
                filename = os.path.basename(path)
                msg.add_attachment(content, maintype='application', subtype='octet-stream', filename=filename)

        logger.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")

    except Exception as e:
        logger.exception(f"Failed to send email to {to_email}: {e}")
        raise
