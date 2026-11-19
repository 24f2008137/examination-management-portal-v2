"""Outgoing notifications used by the Celery jobs.

Email is sent to MailHog (a local fake SMTP server):
    SMTP server          : 127.0.0.1:1025
    Inbox in the browser : http://localhost:8025
"""
import json
import logging
import os
import smtplib
import urllib.request
from email.message import EmailMessage

log = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# --- MailHog settings (change these two lines if MailHog runs elsewhere) ---
SMTP_HOST = 'localhost'
SMTP_PORT = 1025
MAIL_FROM = 'emp-noreply@example.com'


def send_email(to, subject, html_body, text_body=None, attachments=None):
    if not to:
        return False

    msg = EmailMessage()
    msg['From'] = MAIL_FROM
    msg['To'] = to if isinstance(to, str) else ', '.join(to)
    msg['Subject'] = subject
    msg.set_content(text_body or 'Please view this message in an HTML-capable mail client.')
    msg.add_alternative(html_body, subtype='html')

    for filename, data, mimetype in attachments or []:
        maintype, _, subtype = mimetype.partition('/')
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.send_message(msg)
        return True
    except Exception:
        log.exception('Could not send email to %s. Is MailHog running on %s:%s?',
                      to, SMTP_HOST, SMTP_PORT)
        return False


def send_gchat(text):
    url = os.environ.get('GCHAT_WEBHOOK_URL')
    if not url:
        return False
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({'text': text}).encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=10).read()
        return True
    except Exception:
        log.exception('Google Chat webhook failed')
        return False