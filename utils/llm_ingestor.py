import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from utils.logger import log_error

# === Setup ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Unified Prompt Template ===

combined_prompt_template = """
You are an expert at structuring case competition data. Your task is to read unstructured information about a case competition and output valid JSON with three parts:

1. competition: core metadata
2. timeline: event-based data
3. history: past competition records

== COMPETITION RULES ==
- Output a unique lowercase hyphenated ID (e.g. "sfu-bulls-cage")
- The competition name and ID should not make any reference to a year/date. Other fields like the description may. Sometimes there will only be data for the past year's competition - this is expected and okay.
- If competition is free, set "registrationFee" to 0.
- For "prizeAmount", compute the total pool using team sizes if per-person values are mentioned. If there is no prize pool, set to 0.
- For "prize", If there is a monetary prize, take the total prize pool number and convert it to a string. It should be in the format [Currency][Number (with commas)] "Prize Pool" for example if there's a 15k USD prize pool it's "US$15,000 Prize Pool". If there is no prize mentioned, set to "Recognition Only". No matter what, this value can't exceed 20 characters.
- "websiteUrl" must match: {website_url}
- Include "timelineId": "tl-[id]" and "historyId": "h-[id]"
- If university is mentioned but city is not, infer city from university.
- Tags can be unordered.
- Use null for unknown fields.
- If only students from one university are allowed to participate, set "isInternal" to true.
- If last day to register cannot be found for some reason, as a fallback, set it equal to the date of the competition.

== HISTORY RULES ==
- Only include past years (not future events).
- Focus on: winners, past cases/topics, previous dates, changes in format/prizes/etc.
- If date is unknown but year is known, use "YYYY-01-01".
- Use ID format: "h-[comp_id]-YYYY".

== TIMELINE RULES ==
- Include dated events: registration deadlines, case drops, finals, etc.
- Use ISO format: YYYY-MM-DD
- Do not include multiple entries on same date. If there are multiple events on the same date, describe both of the events in the same entry.
- Use ID format: "tl-[comp_id]-shortname"

== FINAL OUTPUT FORMAT ==
{
  "competition": {{
    "id": string,
    "title": string,
    "organizer": string,
    "description": string, // Maximum of 50 Characters
    "longDescription": string,
    "format": "In-Person" | "Virtual" | "Hybrid",
    "prize": string, // Maximum of 20 Characters
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
    "lastDayToRegister": string | null,
    "timelineId": "tl-[id]",
    "historyId": "h-[id]"
  }},
  "timeline": [
    {{
      "id": string,
      "name": string,
      "date": string,
      "description": string
    }},
    ...
  ],
  "history": [
    {{
      "id": string,
      "date": string,
      "title": string,
      "description": string
    }},
    ...
  ]
}
"""

# === Core OpenAI Call ===

def run_openai_json(prompt: str, input_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_text}
            ],
            temperature=0.2,
        )

        raw_output = response.choices[0].message.content.strip()

        # Locate JSON boundaries
        start = raw_output.find('{') if raw_output.startswith('{') else raw_output.find('[')
        end = raw_output.rfind('}') + 1 if raw_output.startswith('{') else raw_output.rfind(']') + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON found in output")

        parsed_json = json.loads(raw_output[start:end])
        return parsed_json

    except Exception as e:
        is_connection = "connect" in str(e).lower() or "timeout" in str(e).lower()
        log_error(f"[OpenAI Error] {'Connection failure' if is_connection else 'Parse error'}: {e}")
        return {
            "error": f"Failed to parse JSON: {'Connection error.' if is_connection else str(e)}",
            "raw_response": raw_output if 'raw_output' in locals() else None
        }

# === Helpers ===

def load_text_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# === Main Function ===

def extract_all_data_from_file(file_path: str, website_url: str) -> dict:
    text = load_text_file(file_path)
    prompt = combined_prompt_template.replace("{website_url}", website_url)
    return run_openai_json(prompt, text)

# === Optional CLI Debug ===

if __name__ == "__main__":
    from pprint import pprint

    path = "scrape_outputs/scrape_output-sfu-bulls-cage.txt"
    website = "https://www.sfufinance.com/bullscage"

    result = extract_all_data_from_file(path, website)

    print("\n🏁 Competition")
    pprint(result.get("competition"))

    print("\n🕒 Timeline")
    pprint(result.get("timeline"))

    print("\n📜 History")
    pprint(result.get("history"))
