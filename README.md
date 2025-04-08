Scraper Flow:

1. Run Link Discovery → Get categorized URLs
2. For each link:
    If Main Website:
        → BeautifulSoup Deep Crawl (5 levels)
        → Download PDFs/images
    If News Article:
        → Newspaper3k scrape
    If Forum:
        → Trafilatura scrape
    If Instagram/Facebook:
        → Instaloader download
    If Ticket Host:
        → BeautifulSoup light scrape
3. When a PDF or image is found:
    → Download to memory
    → OCR to extract text
4. For each page:
    → Collect all extracted text into a clean format
5. Save all outputs together for LLM parsing later
