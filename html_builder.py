import os
import glob
from bs4 import BeautifulSoup


def inject_stylesheet(soup, is_archive):
    css_path = "../style.css" if is_archive else "style.css"
    stylesheet_tag = soup.new_tag("link", rel="stylesheet", href=css_path)

    if soup.head:
        soup.head.append(stylesheet_tag)
    else:
        target = soup.body if soup.body else soup
        target.insert(0, stylesheet_tag)


def remove_unwanted_elements(soup):
    """Strips forwarding blocks, signatures, and Gmail's empty padding tags from the HTML"""

    for div in soup.find_all("div", class_=["gmail_attr", "gmail_signature"]):
        div.decompose()

    for quote_div in soup.find_all("div", class_="gmail_quote"):
        prev = quote_div.previous_sibling
        while prev:
            next_prev = prev.previous_sibling
            if prev.name == "br" or (isinstance(prev, str) and not prev.strip()):
                prev.extract()
            elif prev.name:
                break
            prev = next_prev

        for child in list(quote_div.children):
            if child.name == "br" or (isinstance(child, str) and not child.strip()):
                child.extract()
            elif child.name:
                break


def update_image_paths(soup, image_map, is_archive):
    """Replaces inline CID image sources with relative paths to the local images directory"""

    prefix = "../" if is_archive else ""

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("cid:"):
            cid = src.replace("cid:", "").strip("<>")
            if cid in image_map:
                img["src"] = f"{prefix}images/{image_map[cid]}"


def build_page_soup(raw_html, image_map, is_archive):
    """Parses and cleans the raw email HTML into a BeautifulSoup object"""

    soup = BeautifulSoup(raw_html, "html.parser")

    remove_unwanted_elements(soup)
    update_image_paths(soup, image_map, is_archive)
    inject_stylesheet(soup, is_archive)

    return soup


def extract_and_save_assets(msg, date_str):
    """Downloads image attachments from the email and saves them locally"""

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


def prune_old_archives(max_files=5):
    """Deletes archive HTML and image files beyond the max_files limit"""

    archives = sorted(glob.glob("archive/*.html"), reverse=True)

    for old_file in archives[max_files:]:
        old_date = os.path.basename(old_file).replace(".html", "")
        for old_img in glob.glob(f"images/{old_date}-*"):
            os.remove(old_img)
        os.remove(old_file)


def generate_archive_file(raw_html, image_map, date_str):
    """Builds and saves the historical version of the newsletter with a back link"""

    soup = build_page_soup(raw_html, image_map, is_archive=True)
    back_nav = BeautifulSoup(
        '<div class="archive-nav"><a href="../index.html">&#8592; Back to latest newsletter</a></div>',
        "html.parser",
    )

    target = soup.body if soup.body else soup
    target.insert(0, back_nav)

    os.makedirs("archive", exist_ok=True)
    with open(f"archive/{date_str}.html", "w", encoding="utf-8") as f:
        f.write(str(soup))


def generate_index_file(raw_html, image_map):
    """Builds and saves the main index.html "home" newsletter with the previous newsletters menu"""

    soup = build_page_soup(raw_html, image_map, is_archive=False)

    archives = sorted(glob.glob("archive/*.html"), reverse=True)
    links = [
        f'<a href="archive/{os.path.basename(arch)}">{os.path.basename(arch).replace(".html", "")}</a>'
        for arch in archives[1:]
    ]
    menu_links = " | ".join(links) if links else "<em>No previous newsletters yet.</em>"
    menu_html = f'<div class="archive-menu"><strong>Previous newsletters:</strong><br>{menu_links}</div>'

    menu_soup = BeautifulSoup(menu_html, "html.parser")
    target = soup.body if soup.body else soup
    target.insert(0, menu_soup)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(str(soup))


def generate_website(raw_html, image_map, date_str):
    generate_archive_file(raw_html, image_map, date_str)
    prune_old_archives(max_files=5)
    generate_index_file(raw_html, image_map)
