# scraper.py

import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from io import BytesIO
import instaloader
import os
from utils.logger import log_error

# Initialize Instaloader
L = instaloader.Instaloader(download_pictures=True, download_videos=False,
                             download_video_thumbnails=False, download_comments=False,
                             save_metadata=False, post_metadata_txt_pattern='')

def scrape_main_website(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract visible text
        texts = [t.strip() for t in soup.stripped_strings if t.strip()]
        page_text = '\n'.join(texts)

        # --- OCR images ---
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            img_url = img_tag.get('src')
            if not img_url:
                continue
            img_url = requests.compat.urljoin(url, img_url)  # Fix relative paths
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
            text += page.get_text()

        return text

    except Exception as e:
        log_error(f"[PDF Scrape Error] {url}: {e}")
        return None


def scrape_instagram_profile(insta_url):
    try:
        username = insta_url.strip('/').split('/')[-1]
        posts = []

        for post in instaloader.Profile.from_username(L.context, username).get_posts():
            caption = post.caption or ''
            posts.append(caption)

            # OCR images attached to posts
            if post.typename == 'GraphImage':
                image_url = post.url
                try:
                    img_resp = requests.get(image_url, timeout=10)
                    img_resp.raise_for_status()

                    img = Image.open(BytesIO(img_resp.content))
                    ocr_text = pytesseract.image_to_string(img)
                    posts.append(ocr_text.strip())
                except Exception as e:
                    log_error(f"[Instagram Image OCR Error] {image_url}: {e}")

            if len(posts) >= 5:
                break  # Limit to first 5 posts for now

        return '\n'.join(posts)

    except Exception as e:
        log_error(f"[Instagram Scrape Error] {insta_url}: {e}")
        return None


def scrape_other_generic(url):
    """Generic text scrape for forums, ticket hosts, etc."""
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
    Scrape content from multiple links based on their categories.
    
    Args:
        links (list): List of dictionaries containing 'url' and 'category' keys
        
    Returns:
        str: Combined text from all scraped links
    """
    all_text = []
    
    for link in links:
        url = link['url']
        category = link['category']
        
        try:
            if category == "Main Website":
                text = scrape_main_website(url)
            elif category == "PDF Document":
                text = scrape_pdf(url)
            elif category == "Instagram Post or Profile":
                text = scrape_instagram_profile(url)
            else:  # For other categories like Forum, Ticket Host, etc.
                text = scrape_other_generic(url)
                
            if text:
                all_text.append(text)
                
        except Exception as e:
            log_error(f"[Link Scrape Error] {url}: {e}")
            continue
            
    return '\n\n'.join(all_text) if all_text else None
