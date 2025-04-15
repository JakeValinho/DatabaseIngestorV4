import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from utils.logger import log_error

# === Setup ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Prompt Templates ===

competition_prompt = """You are an expert at extracting structured competition data from messy text.

Your task is to read unstructured content about a case competition and output valid JSON for database insertion.

Important rules:
- Only output valid JSON. No preamble, no explanation.
- If the competition is free, set "registrationFee" to 0 (not null).
- For "prizeAmount", compute the total prize pool. For example: if 1st place is $500/person, 2nd is $300/person, 3rd is $100/person, and teams have 4 people, then prizeAmount = (500 + 300 + 100) * 4 = 3600.
- "websiteUrl" must be set to the one provided: "{website_url}".
- "longDescription" can be very detailed and include anything relevant.
- Use snake-case with hyphens for universityId if known (e.g., "university-of-toronto"). If the university is known but city is not, infer the city from the university's known location.
- If any field is not available, set to null.

Output format:

{
  "id": string,                   // lowercase hyphenated ID like "sfu-ibc-2025"
  "title": string,
  "organizer": string,
  "description": string,         // max 50 characters
  "longDescription": string,
  "format": "In-Person" | "Virtual" | "Hybrid",
  "prize": string,               // max 20 characters, like "$5K Prize Pool"
  "prizeAmount": number,
  "prizeInfo": string,
  "universityId": string | null,
  "isInternal": boolean,
  "eligibility": string,
  "category": string,
  "tags": [string],
  "registrationFee": number | null,
  "isFeatured": false,
  "isHostedByCaseComp": false,
  "city": string | null,
  "region": string | null,
  "websiteUrl": "{website_url}",
  "competitionImageUrl": string | null,
  "teamSizeMin": number | null,
  "teamSizeMax": number | null,
  "lastDayToRegister": string | null
}
"""


history_prompt = """You are a case competition historian extracting historical records from messy text.

Your goal is to return structured JSON entries for **past years only**. Do not include anything scheduled for the future.

Focus on:
- Past winners (teams, schools, or individuals)
- What past cases were about (e.g. companies/case topics)
- Dates when the competition was previously held
- Changes in competition format, eligibility, prizes, or size

Each entry should correspond to a specific year or edition of the competition. If an exact date is not available, use "YYYY-01-01".

Output JSON format:
[
  {
    "id": string,            // Use format "h-[comp_id]-2024", etc.
    "date": string,          // ISO format like "2024-04-12" or "2024-01-01"
    "title": string,         // Short summary like "NIBC 2024 Finals"
    "description": string    // Mention winners, format, location, or anything notable
  },
  ...
]
"""


timeline_prompt = """You are building a structured timeline of key events for a case competition.

Extract any known or inferred time-based events (past or future), including:
- Registration opens or closes
- Case drops
- Round dates (prelims, finals, etc.)
- Workshops, info sessions, result announcements
- Any scheduled event with a specific date

Use precise ISO dates (YYYY-MM-DD) where possible. If only the month or year is known, set the date to the 1st of that period.

Output JSON format:
[
  {
    "id": string,             // Unique, like "tl-[comp_id]-case-release"
    "name": string,           // "Registration Opens", "Finals", etc.
    "date": string,           // ISO 8601 date (e.g. "2024-11-30")
    "description": string     // Short note like "Teams receive final round case"
  },
  ...
]
"""

# === Core Function ===

def run_openai_json(prompt: str, input_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_text}
            ],
            temperature=0.2,
        )

        raw_output = response.choices[0].message.content.strip()

        # Find JSON boundaries
        start = raw_output.find('{') if raw_output.startswith('{') else raw_output.find('[')
        end = raw_output.rfind('}') + 1 if raw_output.startswith('{') else raw_output.rfind(']') + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON found in output")

        parsed_json = json.loads(raw_output[start:end])
        return parsed_json

    except Exception as e:
        # Determine if it's a connection or JSON error
        is_connection = "connect" in str(e).lower() or "timeout" in str(e).lower()
        log_error(f"[OpenAI Error] {'Connection failure' if is_connection else 'Response parse error'}: {e}")
        return {
            "error": f"Failed to parse JSON: {'Connection error.' if is_connection else str(e)}",
            "raw_response": raw_output if 'raw_output' in locals() else None
        }

# === Helpers to Load .txt ===

def load_text_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# === Public Inference Functions ===

def extract_competition_data_from_file(file_path: str) -> dict:
    text = load_text_file(file_path)
    return run_openai_json(competition_prompt, text)

def extract_history_data_from_file(file_path: str, comp_id: str) -> dict:
    text = load_text_file(file_path)
    result = run_openai_json(history_prompt.replace("[comp_id]", comp_id), text)
    return result

def extract_timeline_data_from_file(file_path: str, comp_id: str) -> dict:
    text = load_text_file(file_path)
    result = run_openai_json(timeline_prompt.replace("[comp_id]", comp_id), text)
    return result


# === Optional: Debug CLI usage ===
if __name__ == "__main__":
    from pprint import pprint

    path = "scrape_outputs/scrape_output-sfu-bulls-cage.txt"
    comp_id = "sfu-bulls-cage"

    print("🏁 Competition")
    pprint(extract_competition_data_from_file(path))

    print("\n📜 History")
    pprint(extract_history_data_from_file(path, comp_id))

    print("\n🕒 Timeline")
    pprint(extract_timeline_data_from_file(path, comp_id))
