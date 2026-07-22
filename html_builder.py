import os
import glob
from bs4 import BeautifulSoup

# TODO: add docstrings to functions for documentation


def clean_email_html(raw_html, image_map, is_archive=False):
    soup = BeautifulSoup(raw_html, "html.parser")

    # Injects CSS stylesheet into the HTML <head>
    css_path = "../style.css" if is_archive else "style.css"
    stylesheet_tag = soup.new_tag("link", rel="stylesheet", href=css_path)

    if soup.head:
        soup.head.append(stylesheet_tag)
    elif soup.html:
        head_tag = soup.new_tag("head")
        head_tag.append(stylesheet_tag)
        soup.html.insert(0, head_tag)

    # Remove forwarding and signature blocks
    for div in soup.find_all("div", class_=["gmail_attr", "gmail_signature"]):
        div.decompose()

    # Swap cid (Content-ID) tags for local image paths
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("cid:"):
            cid = src.replace("cid:", "").strip("<>")
            if cid in image_map:
                prefix = "../" if is_archive else ""
                img["src"] = f"{prefix}images/{image_map[cid]}"

    return soup


def extract_assets(msg, date_str):
    image_map = {}
    os.makedirs("images", exist_ok=True)

    for part in msg.walk():
        if part.get_content_maintype() == "image":
            cid = part.get("Content-ID")
            if cid:
                cid = cid.strip("<>")
                ext = part.get_content_subtype() or "png"
                filename = f"{date_str}-{cid}.{ext}"
                filepath = os.path.join("images", filename)

                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))

                image_map[cid] = filename

    return image_map


def generate_newsletter_page(raw_html, image_map, date_str):
    os.makedirs("archive", exist_ok=True)

    # Generate and save the archive version
    archive_soup = clean_email_html(raw_html, image_map, is_archive=True)
    back_nav = BeautifulSoup(
        '<div class="archive-nav"><a href="../index.html">&#8592; Back to latest newsletter</a></div>',
        "html.parser",
    )

    if archive_soup.body:
        archive_soup.body.insert(0, back_nav)

    with open(f"archive/{date_str}.html", "w", encoding="utf-8") as f:
        f.write(str(archive_soup))

    # Prune files older than 5 newsletters
    archives = sorted(glob.glob("archive/*.html"), reverse=True)
    for old_file in archives[5:]:
        old_date = os.path.basename(old_file).replace(".html", "")
        for old_img in glob.glob(f"images/{old_date}-*"):
            os.remove(old_img)
        os.remove(old_file)

    # Generate main index.html
    archives = sorted(glob.glob("archive/*.html"), reverse=True)
    links = [
        f'<a href="archive/{os.path.basename(arch)}">{os.path.basename(arch).replace(".html", "")}</a>'
        for arch in archives[1:]
    ]
    menu_links = " | ".join(links) if links else "<em>No previous newsletters yet.</em>"
    menu_html = f'<div class="archive-menu"><strong>Previous Newsletters:</strong><br>{menu_links}</div>'

    index_soup = clean_email_html(raw_html, image_map, is_archive=False)
    menu_soup = BeautifulSoup(menu_html, "html.parser")

    if index_soup.body:
        index_soup.body.insert(0, menu_soup)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(str(index_soup))
