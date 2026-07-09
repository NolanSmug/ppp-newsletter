import os
import imaplib
import email

def get_unread_emails(mail):
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()

    print(f"DEBUG: Found {len(email_ids)} total unread emails in inbox.")

    for e_id in reversed(email_ids):
        status, data = mail.fetch(e_id, '(BODY[HEADER.FIELDS (FROM)])')
        
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                from_header = str(msg.get("From", ""))
                
                print(f"DEBUG: Checking unread email ID {e_id.decode()} from sender: {from_header}")
                
                if "@pingpongnyc.org" in from_header.lower() or "nolangcyr@gmail.com" in from_header.lower():
                    return [e_id] 
                    
    return []

def parse_email_and_save(msg):
    html_content = None
    inline_images = {}
    os.makedirs("images", exist_ok=True)

    for part in msg.walk():
        content_type = part.get_content_type()

        if content_type == "text/html":
            html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        elif part.get_content_maintype() == "image":
            cid = part.get("Content-ID") # get the content-id of the image for unique identification
            if cid:
                cid = cid.strip("<>") 
                ext = part.get_content_subtype() or "png"
                filename = f"{cid}.{ext}" 
                filepath = os.path.join("images", filename)
                
                # Save the image file locally to images/
                with open(filepath, "wb") as img_file:
                    img_file.write(part.get_payload(decode=True))
                
                # Store the relative path for the HTML replacement/insertion
                inline_images[cid] = f"images/{filename}"

    if html_content:
        for cid, filepath in inline_images.items():
            html_content = html_content.replace(f"cid:{cid}", filepath)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Successfully generated index.html and saved images into images/")

def main():
    username = os.environ.get("EMAIL_USER")
    app_password = os.environ.get("APP_PASSWORD")

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, app_password)
    mail.select("inbox")

    email_ids = get_unread_emails(mail)

    if email_ids:
        latest_id = email_ids[-1]
        status, data = mail.fetch(latest_id, "(RFC822)")

        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                parse_email_and_save(msg)
    else:
        print("No new unread emails found.")

    mail.logout()

if __name__ == "__main__":
    main()