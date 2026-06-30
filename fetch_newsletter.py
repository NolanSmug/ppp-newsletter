import os
import imaplib
import email
import base64

USERNAME = os.environ.get("EMAIL_USER")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(USERNAME, APP_PASSWORD)
mail.select("inbox")

status, messages = mail.search(None, "UNSEEN") # search only for UNSEEN (unread) emails
email_ids = messages[0].split()

if email_ids:
    latest_id = email_ids[-1]
    status, data = mail.fetch(latest_id, "(RFC822)")

    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            
            html_content = None
            inline_images = {}

            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_maintype() == "image":
                    cid = part.get("Content-ID")
                    if cid:
                        cid = cid.strip("<>") 
                        image_data = part.get_payload(decode=True)
                        base64_str = base64.b64encode(image_data).decode('utf-8')
                        inline_images[cid] = f"data:{content_type};base64,{base64_str}"

            if html_content:
                for cid, b64_data in inline_images.items():
                    html_content = html_content.replace(f"cid:{cid}", b64_data)

                with open("index.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("Successfully generated index.html")
else:
    print("No new unread emails found.")

mail.logout()