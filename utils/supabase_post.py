from utils.supabase_client import supabase
from datetime import datetime

def insert_competition_bundle(comp_json, timeline_json, history_json):
    comp_id = comp_json.get("id")
    if not comp_id:
        return {"error": "Missing competition ID."}

    # Set up linked IDs
    timeline_id = f"tl-{comp_id}"
    history_id = f"h-{comp_id}"
    now = datetime.utcnow().isoformat()

    # === Insert Timeline and History FIRST (to satisfy FK constraints) ===
    supabase.table("timeline").upsert({
        "id": timeline_id,
        "createdat": now,
        "updatedat": now
    }).execute()

    supabase.table("history").upsert({
        "id": history_id,
        "createdat": now,
        "updatedat": now
    }).execute()

    # --- Insert into `competition` table ---
    comp_insert = {
        "id": comp_id,
        "title": comp_json.get("title"),
        "organizer": comp_json.get("organizer"),
        "description": comp_json.get("description"),
        "longdescription": comp_json.get("longDescription"),
        "format": comp_json.get("format"),
        "prize": comp_json.get("prize"),
        "prizeamount": comp_json.get("prizeAmount"),
        "prizeinfo": comp_json.get("prizeInfo"),
        "universityid": comp_json.get("universityId"),
        "isinternal": comp_json.get("isInternal"),
        "eligibility": comp_json.get("eligibility"),
        "category": comp_json.get("category"),
        "difficulty": comp_json.get("difficulty"),
        "tags": comp_json.get("tags"),
        "registrationfee": comp_json.get("registrationFee"),
        "isfeatured": comp_json.get("isFeatured", False),
        "ishostedbycasecomp": comp_json.get("isHostedByCaseComp", False),
        "city": comp_json.get("city"),
        "region": comp_json.get("region"),
        "websiteurl": comp_json.get("websiteUrl"),
        "competitionimageurl": comp_json.get("competitionImageUrl"),
        "teamsizemin": comp_json.get("teamSizeMin"),
        "teamsizemax": comp_json.get("teamSizeMax"),
        "lastdaytoregister": comp_json.get("lastDayToRegister"),
        "timelineid": timeline_id,
        "historyid": history_id,
        "isconfirmed": True,
        "createdat": now,
        "updatedat": now,
    }

    try:
        supabase.table("competition").upsert(comp_insert).execute()
    except Exception as e:
        return {"error": f"Competition insert failed: {e}"}

    # --- Insert into `timelineevent` table ---
    try:
        if timeline_json:
            events_to_insert = []
            for event in timeline_json:
                events_to_insert.append({
                    "id": event["id"],
                    "timelineid": timeline_id,
                    "name": event["name"],
                    "date": event["date"],
                    "description": event["description"],
                    "createdat": now,
                    "updatedat": now,
                })
            supabase.table("timelineevent").upsert(events_to_insert).execute()
    except Exception as e:
        return {"error": f"Timeline insert failed: {e}"}

    # --- Insert into `historyentry` table ---
    try:
        if history_json:
            entries_to_insert = []
            for entry in history_json:
                entries_to_insert.append({
                    "id": entry["id"],
                    "historyid": history_id,
                    "date": entry["date"],
                    "title": entry["title"],
                    "description": entry["description"],
                    "createdat": now,
                    "updatedat": now,
                })
            supabase.table("historyentry").upsert(entries_to_insert).execute()
    except Exception as e:
        return {"error": f"History insert failed: {e}"}

    return {"status": "success"}
