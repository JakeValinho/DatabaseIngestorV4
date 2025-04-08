import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": SERPER_API_KEY
}
