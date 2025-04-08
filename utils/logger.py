# utils/logger.py

import os
from datetime import datetime

# === Setup a logs directory ===
LOG_DIR = "logs"
LOG_FILE = "scrape_errors.log"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

def log_error(message: str):
    """Log an error message with a timestamp to the scrape_errors.log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
