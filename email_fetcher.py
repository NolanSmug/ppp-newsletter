import os
import imaplib
import email
from email.utils import parsedate_to_datetime


def connect_to_mailbox():
    """Establishes an IMAP connection to Gmail and selects the inbox"""

    username = os.environ.get("EMAIL_USER")
    app_password = os.environ.get("APP_PASSWORD")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, app_password)
    mail.select("inbox")

    return mail


def get_allowed_senders():
    """Retrieves and formats the list of allowed sender emails from Github pipeline injected secret variables"""

    raw_senders = os.environ.get("ALLOWED_SENDERS", "")
    return [s.strip(" \"'\n\r") for s in raw_senders.lower().split(",") if s.strip()]


def is_sender_allowed(mail, email_id, allowed_senders):
    """Checks if the email's From header matches any of the allowed senders"""

    status, header_data = mail.fetch(email_id, "(BODY[HEADER.FIELDS (FROM)])")

    for response_part in header_data:
        if isinstance(response_part, tuple):
            header_msg = email.message_from_bytes(response_part[1])
            from_header = str(header_msg.get("From", "")).lower()
            if any(sender in from_header for sender in allowed_senders):
                return True

    return False


def fetch_email_message(mail, email_id):
    """Downloads the full email payload and gets its date"""

    status, full_data = mail.fetch(email_id, "(RFC822)")

    for full_part in full_data:
        if isinstance(full_part, tuple):
            message = email.message_from_bytes(full_part[1])
            dt = parsedate_to_datetime(message.get("Date"))
            return message, dt.strftime("%Y-%m-%d")

    return None, None


def get_latest_unread_email():
    """Retrieves the most recent unread email from an allowed sender"""

    mail = connect_to_mailbox()
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split() if messages[0] else []

    if not email_ids:
        print("DEBUG: 0 unread emails found in inbox")
        mail.logout()
        return None, None

    allowed_senders = get_allowed_senders()

    # The list of ALLOWED_SENDERS is accessible on the GitHub repository:
    # Settings > Secrets and Variables > Actions: Repository secrets > ALLOWED_SENDERS
    for email_id in reversed(email_ids):
        if is_sender_allowed(mail, email_id, allowed_senders):
            message, date_str = fetch_email_message(mail, email_id)
            mail.logout()
            return message, date_str

    print("DEBUG: Unread emails exist, but none matched the allowed senders list")
    mail.logout()

    return None, None
