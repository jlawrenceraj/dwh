import smtplib
import mimetypes
from email.message import EmailMessage
from pathlib import Path


def send_email(smtp_config, from_addr, to_addrs, subject, body, attachments=None):
    """Send an email with optional attachments.

    smtp_config: dict with keys host, port, username, password, use_tls, use_ssl
    to_addrs: list of recipient emails
    attachments: list of file paths
    """
    if attachments is None:
        attachments = []

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs) if isinstance(to_addrs, (list, tuple)) else to_addrs
    msg.set_content(body)

    for path in attachments:
        p = Path(path)
        if not p.exists():
            continue
        ctype, encoding = mimetypes.guess_type(str(p))
        if ctype is None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with p.open('rb') as f:
            data = f.read()
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=p.name)

    host = smtp_config.get('host')
    port = smtp_config.get('port')
    username = smtp_config.get('username')
    password = smtp_config.get('password')
    use_tls = smtp_config.get('use_tls', False)
    use_ssl = smtp_config.get('use_ssl', False)

    if use_ssl:
        server = smtplib.SMTP_SSL(host, port)
    else:
        server = smtplib.SMTP(host, port)
    try:
        server.ehlo()
        if use_tls and not use_ssl:
            server.starttls()
            server.ehlo()
        if username:
            server.login(username, password)
        server.send_message(msg)
    finally:
        server.quit()
