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
            
            os.makedirs("images", exist_ok=True)

            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_maintype() == "image":
                    cid = part.get("Content-ID") # get the content-id of the image for unique identification
                    if cid:
                        cid = cid.strip("<>") 

                        ext = part.get_content_subtype()
                        filename = part.get_filename() or f"{cid}.{ext}"
                        filepath = os.path.join("images", filename)
                        
                        # Save the image file locally to images/
                        with open(filepath, "wb") as img_file:
                            img_file.write(part.get_payload(decode=True))
                        
                        # Store the relative path for the HTML replacement
                        inline_images[cid] = f"images/{filename}"

            if html_content:
                for cid, filepath in inline_images.items():
                    html_content = html_content.replace(f"cid:{cid}", filepath)

                with open("index.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("Successfully generated index.html and saved images")
            
else:
    print("No new unread emails found.")

mail.logout()