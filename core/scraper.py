# scraper.py

import os
import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from io import BytesIO
import instaloader
import trafilatura
from dotenv import load_dotenv
from utils.logger import log_error
import streamlit as st

# === Load environment variables ===
load_dotenv()
INSTA_USER = os.getenv("INSTA_USER")
INSTA_PASS = os.getenv("INSTA_PASS")

# === Initialize Instaloader ===
L = instaloader.Instaloader(
    download_pictures=True,
    download_videos=False,
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=''
)

# === Login if credentials provided ===
if INSTA_USER and INSTA_PASS:
    try:
        L.load_session_from_file(INSTA_USER)
    except Exception as e:
        log_error(f"[Instagram Load Session Error] {e}")
        try:
            L.login(INSTA_USER, INSTA_PASS)
            L.save_session_to_file()
        except Exception as e2:
            log_error(f"[Instagram Login Error] {e2}")


# === Scrape Functions ===

def scrape_main_website(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')
        texts = [t.strip() for t in soup.stripped_strings if t.strip()]
        page_text = '\n'.join(texts)

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
                pix = page.get_pixmap()
                img = Image.open(BytesIO(pix.tobytes()))
                text += pytesseract.image_to_string(img)

        return text

    except Exception as e:
        log_error(f"[PDF Scrape Error] {url}: {e}")
        return None


def clean_instagram_url(url):
    return url.split('?')[0].rstrip('/')


def scrape_instagram_link(insta_url):
    clean_url = clean_instagram_url(insta_url)

    if '/p/' in clean_url:
        shortcode = clean_url.split('/p/')[1].split('/')[0]
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            text = post.caption or ''

            try:
                image_url = getattr(post, "thumbnail_url", None) or getattr(post, "url", None)

                if image_url:
                    try:
                        img_resp = requests.get(image_url, timeout=10)
                        img_resp.raise_for_status()
                        img = Image.open(BytesIO(img_resp.content))
                        ocr_text = pytesseract.image_to_string(img)
                        text += '\n' + ocr_text.strip()
                    except Exception as e:
                        log_error(f"[Instagram OCR Fallback Error] {image_url}: {e}")
                else:
                    log_error(f"[Instagram Image Missing] No valid image URL found for {insta_url}")

            except Exception as e:
                log_error(f"[Instagram Thumbnail OCR Error] {post.thumbnail_url}: {e}")

            return text

        except Exception as e:
            log_error(f"[Instagram Post Scrape Error] {insta_url}: {e}")
            return None

    else:
        log_error(f"[Instagram Profile Skipped] {insta_url}")
        return None


def scrape_generic_with_fallback(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(downloaded)
            if result:
                return result
    except Exception as e:
        log_error(f"[Trafilatura Error] {url}: {e}")

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        texts = [t.strip() for t in soup.stripped_strings if t.strip()]
        return '\n'.join(texts)
    except Exception as e:
        log_error(f"[Fallback Generic Scrape Error] {url}: {e}")
        return None


def scrape_links(links, save_to_txt=False, comp_name=None, output_dir="scrape_outputs"):
    all_text = []
    total = len(links)

    if total == 0:
        return None

    progress = None
    try:
        progress = st.progress(0)
    except:
        pass

    for i, link in enumerate(links):
        url = link.get('url')
        category = link.get('category')

        try:
            if category == "Main Website":
                text = scrape_main_website(url)
            elif category == "PDF Document":
                text = scrape_pdf(url)
            elif category == "Instagram Post or Profile":
                text = scrape_instagram_link(url)
            elif any(domain in url for domain in ["wallstreetoasis", "reddit", "forum"]):
                text = scrape_generic_with_fallback(url)
            else:
                text = scrape_generic_with_fallback(url)

            if text:
                all_text.append(text)

        except Exception as e:
            log_error(f"[Scrape Link Error] {url}: {e}")

        if progress:
            progress.progress((i + 1) / total)

    if progress:
        progress.empty()

    combined_text = '\n\n'.join(all_text) if all_text else None

    if save_to_txt and combined_text:
        os.makedirs(output_dir, exist_ok=True)
        if comp_name:
            safe_name = ''.join(c for c in comp_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"scrape_output-{safe_name}.txt"
        else:
            filename = "scrape_output.txt"

        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(combined_text)

    return combined_text
