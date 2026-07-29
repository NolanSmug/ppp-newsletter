from email_fetcher import get_latest_unread_email
from html_builder import extract_and_save_assets, generate_website


def extract_html_payload(msg):
    """Finds and decodes the primary HTML text part of the email message"""

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            return part.get_payload(decode=True).decode("utf-8", errors="ignore")

    return None


def main():
    msg, date_str = get_latest_unread_email()
    if not msg:
        return

    raw_html = extract_html_payload(msg)
    if raw_html:
        image_map = extract_and_save_assets(msg, date_str)
        generate_website(raw_html, image_map, date_str)
        print("Successfully generated index.html and updated the archive")
    else:
        print("No HTML content found in the email")


if __name__ == "__main__":
    main()
