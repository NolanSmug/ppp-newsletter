from email_fetcher import get_latest_unread_email
from html_builder import extract_assets, generate_newsletter_page


def main():
    msg, date_str = get_latest_unread_email()
    if not msg:
        return

    raw_html = None
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            raw_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            break

    if raw_html:
        image_map = extract_assets(msg, date_str)
        generate_newsletter_page(raw_html, image_map, date_str)
        print("Successfully generated index.html and updated the archive.")
    else:
        print("No HTML content found in the email.")


if __name__ == "__main__":
    main()
