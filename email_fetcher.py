import os
import imaplib
import email
from email.utils import parsedate_to_datetime


def get_latest_unread_email():
    username = os.environ.get("EMAIL_USER")
    app_password = os.environ.get("APP_PASSWORD")

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, app_password)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split() if messages[0] else []

    if not email_ids:
        print("DEBUG: 0 unread emails found in inbox.")
        mail.logout()
        return None, None

    # The list of ALLOWED_SENDERS is accessible on the GitHub repository:
    # Settings > Secrets and Variables > Actions: Repository secrets > ALLOWED_SENDERS
    raw_senders = os.environ.get("ALLOWED_SENDERS", "")
    allowed_senders = [s.strip(" \"'\n\r") for s in raw_senders.lower().split(",") if s.strip()]

    for email_id in reversed(email_ids):
        status, header_data = mail.fetch(email_id, "(BODY[HEADER.FIELDS (FROM)])")
        for response_part in header_data:
            if isinstance(response_part, tuple):
                header_msg = email.message_from_bytes(response_part[1])
                from_header = str(header_msg.get("From", "")).lower()

                if any(sender in from_header for sender in allowed_senders):
                    status, full_data = mail.fetch(email_id, "(RFC822)")

                    for full_part in full_data:
                        if isinstance(full_part, tuple):
                            message = email.message_from_bytes(full_part[1])
                            dt = parsedate_to_datetime(message.get("Date"))
                            mail.logout()

                            return message, dt.strftime("%Y-%m-%d")

    print("DEBUG: Unread emails exist, but none matched the allowed senders list.")
    mail.logout()

    return None, None
