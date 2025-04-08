# main.py
import streamlit as st
from core.link_discovery import discover_links

# === Streamlit page setup ===
st.set_page_config(page_title="CaseComp Ingestor - Step 1: Link Discovery")
st.title("🧠 Case Competition Ingestion (Step 1)")

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

    # Optional metadata
    with st.expander("Optional Metadata"):
        organizer = st.text_input("Organizer (optional)")
        university = st.text_input("University (optional)")
        city = st.text_input("City (optional)")
    
    submitted = st.form_submit_button("🔍 Discover Links")

# === State Setup ===
if "discovered_links" not in st.session_state:
    st.session_state.discovered_links = []

# === Run Discovery ===
if submitted:
    if not comp_name or not starting_url:
        st.error("Please provide at least Competition Name and Starting URL.")
        st.stop()

    metadata = {
        "organizer": organizer,
        "university": university,
        "city": city,
    }

    st.info("Searching for related links...")
    links = discover_links(comp_name, starting_url, starting_category, metadata)
    st.session_state.discovered_links = links
    st.success(f"✅ Found {len(links)} links!")

# === Editable Table View ===
if st.session_state.discovered_links:
    st.subheader("Review and Edit Link Categories")

    updated_links = []
    category_options = [
        "Main Website", "Instagram Post or Profile", "LinkedIn Post or Profile",
        "Facebook Post or Profile", "YouTube Video", "News Article", 
        "University Page", "Ticket Host", "Forum", "PDF Document", "Other"
    ]

    for i, entry in enumerate(st.session_state.discovered_links):
        cols = st.columns([3, 2, 3, 2])  # URL | Title | Snippet | Category

        with cols[0]:
            st.markdown(f"[{entry['url']}]({entry['url']})")
        with cols[1]:
            st.caption(entry.get("title", ""))
        with cols[2]:
            st.caption(entry.get("snippet", ""))
        with cols[3]:
            new_category = st.selectbox(
                label=f"Category {i}",
                options=category_options,
                index=category_options.index(entry["category"]) if entry["category"] in category_options else category_options.index("Other"),
                key=f"category_select_{i}"
            )
            entry["category"] = new_category

        updated_links.append(entry)

    st.session_state.discovered_links = updated_links

    st.markdown("---")
    if st.button("✅ Confirm Categories and Continue"):
        st.success("Categories updated. Ready for Step 2 (Scraping)!")
        # Future: trigger step 2 here if you want

    # OPTIONAL: (future feature) Save to CSV
    # if st.button("💾 Export to CSV"):
    #     # Coming soon

else:
    st.info("⚡ Start by entering competition info above!")

