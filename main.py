import streamlit as st
import os

from core.link_discovery import discover_links
from core.scraper import scrape_links
from utils.llm_ingestor import extract_all_data_from_file
from utils.utils import sanitize_filename
from utils.supabase_post import insert_competition_bundle


# === Page setup ===
st.set_page_config(page_title="CaseComp Ingestor - Step 1 + 2 + 3")
st.title("🧠 Case Competition Ingestion")

# === Input Form ===
with st.form("discovery_form"):
    st.subheader("Enter Competition Details")
    comp_name = st.text_input("Competition Name")
    starting_url = st.text_input("Starting URL")
    starting_category = st.selectbox("Starting URL Category", [
        "Main Website", "Instagram Post or Profile", "LinkedIn Post or Profile",
        "Facebook Post or Profile", "YouTube Video", "News Article",
        "University Page", "Ticket Host", "Forum", "PDF Document", "Other"
    ])

    with st.expander("Optional Metadata"):
        organizer = st.text_input("Organizer (optional)")
        university = st.text_input("University (optional)")
        city = st.text_input("City (optional)")

    submitted = st.form_submit_button("🔍 Discover Links")

# === Session state setup ===
if "discovered_links" not in st.session_state:
    st.session_state.discovered_links = []

# === Step 1: Discover Links ===
if submitted:
    if not comp_name or not starting_url:
        st.error("Please provide at least Competition Name and Starting URL.")
        st.stop()

    metadata = {
        "organizer": organizer,
        "university": university,
        "city": city,
    }

    st.info("🔎 Searching for related links...")
    links = discover_links(comp_name, starting_url, starting_category, metadata)
    st.session_state.discovered_links = links
    st.success(f"✅ Found {len(links)} links!")

# === Step 2: Review/Edit Categories ===
if st.session_state.discovered_links:
    st.subheader("Review and Edit Link Categories")
    st.write("### Discovered Links (click ❌ to remove):")

    category_options = [
        "Main Website", "Instagram Post or Profile", "LinkedIn Post or Profile",
        "Facebook Post or Profile", "YouTube Video", "News Article",
        "University Page", "Ticket Host", "Forum", "PDF Document", "Other"
    ]

    if "to_delete" not in st.session_state:
        st.session_state.to_delete = None

    updated_links = []
    for i, entry in enumerate(st.session_state.discovered_links):
        cols = st.columns([3, 2, 2, 2, 1])
        with cols[0]:
            st.markdown(f"[{entry['url']}]({entry['url']})")
        with cols[1]:
            st.caption(entry.get("title", ""))
        with cols[2]:
            st.caption(entry.get("snippet", ""))
        with cols[3]:
            new_category = st.selectbox(
                f"Category {i}",
                options=category_options,
                index=category_options.index(entry["category"]) if entry["category"] in category_options else category_options.index("Other"),
                key=f"category_select_{i}"
            )
            entry["category"] = new_category
        with cols[4]:
            if st.button("❌", key=f"remove_{i}"):
                st.session_state.to_delete = i
                st.rerun()

        if st.session_state.to_delete != i:
            updated_links.append(entry)

    if st.session_state.to_delete is not None:
        st.session_state.discovered_links = updated_links
        st.session_state.to_delete = None
        st.rerun()

    st.markdown("---")

    # === Step 3: Scrape + Extract + Upload ===
    if st.button("✅ Confirm Categories and Run Full Ingestion"):
        st.info("⚙️ Scraping and processing...")

        try:
            if not comp_name.strip():
                st.error("Competition name is required.")
                st.stop()

            safe_name = sanitize_filename(comp_name)
            scraped_path = f"scrape_outputs/scrape_output-{safe_name}.txt"

            # Scrape and save
            scraped_text = scrape_links(
                st.session_state.discovered_links,
                save_to_txt=True,
                comp_name=safe_name,
            )

            if not scraped_text:
                st.error("❌ No content could be scraped.")
                st.stop()

            st.success("✅ Scraping completed!")

            # Extract using LLM
            st.info("🧠 Extracting structured data...")
            all_json = extract_all_data_from_file(scraped_path, starting_url)

            comp_json = all_json.get("competition", {})
            history_json = all_json.get("history", [])
            timeline_json = all_json.get("timeline", [])

            st.success("✅ Extraction complete!")

            # Upload to Supabase
            st.info("📡 Uploading to Supabase...")
            result = insert_competition_bundle(comp_json, timeline_json, history_json)

            if result.get("status") == "success":
                st.success("✅ Successfully uploaded to Supabase!")
            else:
                st.error(f"❌ Upload failed: {result.get('error')}")

            # Display results
            st.subheader("🏁 Competition")
            st.json(comp_json)

            st.subheader("📜 History")
            st.json(history_json)

            st.subheader("🕒 Timeline")
            st.json(timeline_json)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
