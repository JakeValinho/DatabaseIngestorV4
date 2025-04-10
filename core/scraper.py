# scraper.py

import os
import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from io import BytesIO
import instaloader
from dotenv import load_dotenv
from utils.logger import log_error

# === Load environment variables ===
load_dotenv()
INSTA_USER = os.getenv("INSTA_USER")
INSTA_PASS = os.getenv("INSTA_PASS")

# === Initialize Instaloader (only if needed) ===
L = instaloader.Instaloader(
    download_pictures=True,
    download_videos=False,
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=''
)

# === Try to Login ===
if INSTA_USER and INSTA_PASS:
    try:
        L.login(INSTA_USER, INSTA_PASS)
    except Exception as e:
        log_error(f"[Instagram Login Error] {e}")

# === Scrape Functions ===

def scrape_main_website(url):
    """Scrape main website text and OCR images."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        texts = [t.strip() for t in soup.stripped_strings if t.strip()]
        page_text = '\n'.join(texts)

        # OCR images
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            img_src = img_tag.get('src')
            if not img_src:
                continue
            img_url = requests.compat.urljoin(url, img_src)

            try:
                img_resp = requests.get(img_url, timeout=10)
                img_resp.raise_for_status()
                img = Image.open(BytesIO(img_resp.content))
                ocr_text = pytesseract.image_to_string(img)
                page_text += '\n' + ocr_text.strip()
            except Exception as e:
                log_error(f"[Image OCR Error] {img_url}: {e}")

        return page_text

    except Exception as e:
        log_error(f"[Website Scrape Error] {url}: {e}")
        return None


def scrape_pdf(url):
    """Scrape text from a PDF, fallback to OCR if needed."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        pdf_bytes = BytesIO(resp.content)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        text = ''
        for page in doc:
            page_text = page.get_text()
            if page_text.strip():
                text += page_text
            else:
                # OCR fallback for image-only PDFs
                pix = page.get_pixmap()
                img = Image.open(BytesIO(pix.tobytes()))
                text += pytesseract.image_to_string(img)

        return text

    except Exception as e:
        log_error(f"[PDF Scrape Error] {url}: {e}")
        return None


def clean_instagram_url(url):
    """Standardize Instagram URLs."""
    return url.split('?')[0].rstrip('/')


def scrape_instagram_link(insta_url):
    """Scrape Instagram: handle posts and ignore profiles (for now)."""
    clean_url = clean_instagram_url(insta_url)

    if '/p/' in clean_url:
        # It's a post
        shortcode = clean_url.split('/p/')[1].split('/')[0]
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            text = post.caption or ''

            # OCR image from post
            try:
                img_resp = requests.get(post.url, timeout=10)
                img_resp.raise_for_status()
                img = Image.open(BytesIO(img_resp.content))
                ocr_text = pytesseract.image_to_string(img)
                text += '\n' + ocr_text.strip()
            except Exception as e:
                log_error(f"[Instagram Post Image OCR Error] {post.url}: {e}")

            return text

        except Exception as e:
            log_error(f"[Instagram Post Scrape Error] {insta_url}: {e}")
            return None

    else:
        # It's a profile - skip for now
        log_error(f"[Instagram Profile Skipped] {insta_url}")
        return None


def scrape_other_generic(url):
    """Generic page scraper for forums, ticket sites, etc."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')
        texts = [t.strip() for t in soup.stripped_strings if t.strip()]
        return '\n'.join(texts)

    except Exception as e:
        log_error(f"[Generic Scrape Error] {url}: {e}")
        return None


def scrape_links(links):
    """
    Scrape multiple links based on their category.

    Args:
        links (list of dict): [{url, category}]

    Returns:
        str: Combined scraped text
    """
    all_text = []

    for link in links:
        url = link.get('url')
        category = link.get('category')

        try:
            if category == "Main Website":
                text = scrape_main_website(url)
            elif category == "PDF Document":
                text = scrape_pdf(url)
            elif category == "Instagram Post or Profile":
                text = scrape_instagram_link(url)
            else:
                text = scrape_other_generic(url)

            if text:
                all_text.append(text)

        except Exception as e:
            log_error(f"[Scrape Link Error] {url}: {e}")

    return '\n\n'.join(all_text) if all_text else None
