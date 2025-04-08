# core/link_discovery.py

import requests
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
HEADERS = {"Content-Type": "application/json", "X-API-KEY": SERPER_API_KEY}

# === Serper API call ===
def run_serper_search(query):
    search_url = "https://google.serper.dev/search"
    payload = {"q": query, "num": 10}
    res = requests.post(search_url, json=payload, headers=HEADERS)
    if res.status_code != 200:
        raise ValueError(f"Serper API error: {res.text}")
    return res.json().get("organic", [])

# === Helper: safely expand shortened URLs ===
def clean_url(url):
    try:
        session = requests.Session()
        resp = session.head(url, allow_redirects=True, timeout=5)
        if resp.status_code >= 400:
            resp = session.get(url, allow_redirects=True, timeout=5)
        return resp.url
    except:
        return url

# === Categorizer: smarter and stricter ===
def better_categorize_link(url, title=""):
    url = url.lower()
    title = (title or "").lower()

    # Instagram
    if "instagram.com" in url:
        return "Instagram Post or Profile"
    # LinkedIn
    if "linkedin.com" in url:
        return "LinkedIn Post or Profile"
    # Facebook
    if "facebook.com" in url:
        return "Facebook Post or Profile"
    # Forums
    if "wallstreetoasis.com" in url or "reddit.com" in url or "quora.com" in url:
        return "Forum"
    # Ticket Hosts
    if "eventbrite.com" in url or "bounce.to" in url:
        return "Ticket Host"
    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube Video"
    # PDFs
    if url.endswith(".pdf"):
        return "PDF Document"
    # News
    if any(word in url for word in ["news", "press", "article"]) or any(word in title for word in ["news", "press", "article"]):
        return "News Article"
    # Universities
    domain = urlparse(url).netloc.replace("www.", "")
    if (
        domain.endswith(".edu") or
        domain.endswith(".ac.uk") or
        domain.endswith(".edu.au") or
        domain.endswith(".ca") or
        "university" in domain or
        "college" in domain
    ):
        return "University Page"
    # Main Website Candidate
    if any(word in url for word in ["case", "competition", "challenge"]) or any(word in title for word in ["case", "competition", "challenge"]):
        return "Main Website (Candidate)"
    
    return "Other"

# === Full discovery orchestration ===
def discover_links(comp_name, starting_url, starting_category, optional_metadata={}):
    results = []
    seen = set()

    # Add manually entered link
    results.append({
        "url": starting_url,
        "category": starting_category,
        "title": "(User Provided)",
        "snippet": "(manual entry)",
        "dateDetected": None
    })
    seen.add(starting_url)

    # Prepare multiple search queries
    search_terms = [
        comp_name,
        f"{comp_name} case competition",
        f"{comp_name} registration"
    ]
    if optional_metadata.get("university"):
        search_terms.append(f"{comp_name} {optional_metadata['university']}")
    if optional_metadata.get("city"):
        search_terms.append(f"{comp_name} {optional_metadata['city']}")
    if optional_metadata.get("organizer"):
        search_terms.append(f"{comp_name} {optional_metadata['organizer']}")

    # Run Serper search for each query
    for query in search_terms:
        try:
            search_results = run_serper_search(query)
            for r in search_results:
                link = r.get("link")
                title = r.get("title") or ""
                snippet = r.get("snippet") or ""

                if not link or link in seen:
                    continue

                final_url = clean_url(link)
                if final_url in seen:
                    continue

                seen.add(final_url)
                guessed_category = better_categorize_link(final_url, title)

                results.append({
                    "url": final_url,
                    "category": guessed_category,
                    "title": title,
                    "snippet": snippet,
                    "dateDetected": r.get("date")
                })

        except Exception as e:
            print(f"[ERROR] Search failed for '{query}': {str(e)}")

    return results
