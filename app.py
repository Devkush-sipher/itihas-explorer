# app.py

import streamlit as st
from config import LANGUAGES, REGIONS
from utils.data_fetcher import (
    get_entity_details,
    get_on_this_day_events,
    get_timeline_events,
    get_wiki_summary_and_image
)

# --- Page Configuration and Styling ---
st.set_page_config(
    page_title="Itihas Explorer",
    page_icon="📜",
    layout="wide"
)

# Function to load local CSS
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found. The app will use default styling.")

load_css('style.css')

# --- Sidebar for User Selections ---
st.sidebar.title("Explorer Settings")

selected_language_name = st.sidebar.selectbox(
    "Choose your language:",
    options=list(LANGUAGES.keys())
)
lang_code = LANGUAGES[selected_language_name]

selected_region_name = st.sidebar.selectbox(
    "Choose a region to explore:",
    options=list(REGIONS.keys())
)
region_info = REGIONS[selected_region_name]
region_q_code = region_info["q_code"]

st.sidebar.markdown("---")
st.sidebar.info("This app uses data from Wikidata and Wikipedia to bring regional Indian history to life in local languages.")


# --- Main Application ---

st.title(f"📜 Itihas Explorer: A Journey Through {selected_region_name}")

# --- Tabbed Interface ---
tab1, tab2 = st.tabs(["**Dashboard**", "**Interactive Timeline**"])

with tab1:
    st.header("Regional Dashboard")
    
    with st.spinner(f"Loading dashboard for {selected_region_name}..."):
        col1, col2 = st.columns(2)

        # --- Featured Figure Column ---
        with col1:
            st.subheader("Featured Historical Figure")
            figure_q_code = region_info["featured_figure"]
            details = get_entity_details(figure_q_code, lang_code)
            
            if details:
                st.markdown(f"#### {details['label']}")
                # Check if a Wikipedia page exists before trying to fetch content
                if details['page_title']:
                    wiki_content = get_wiki_summary_and_image(details['page_title'], lang_code)
                    if wiki_content['image_url']:
                        st.image(wiki_content['image_url'], caption=details['label'], use_column_width=True)
                    st.write(wiki_content['summary'])
                else:
                    st.info(f"Details for '{details['label']}' found on Wikidata, but no Wikipedia article is available in {selected_language_name}.")
            else:
                st.error("Could not load featured figure details.")

        # --- Featured Monument Column ---
        with col2:
            st.subheader("Featured Monument")
            monument_q_code = region_info["featured_monument"]
            details = get_entity_details(monument_q_code, lang_code)

            if details:
                st.markdown(f"#### {details['label']}")
                if details['page_title']:
                    wiki_content = get_wiki_summary_and_image(details['page_title'], lang_code)
                    if wiki_content['image_url']:
                        st.image(wiki_content['image_url'], caption=details['label'], use_column_width=True)
                    st.write(wiki_content['summary'])
                else:
                    st.info(f"Details for '{details['label']}' found on Wikidata, but no Wikipedia article is available in {selected_language_name}.")
            else:
                st.error("Could not load featured monument details.")

    st.markdown("---")
    
    # --- "On This Day" Section ---
    st.subheader("On This Day in History")
    with st.spinner("Searching for events on this day..."):
        on_this_day_events = get_on_this_day_events(region_q_code, lang_code)
        if on_this_day_events:
            for event in on_this_day_events:
                st.info(f"**{event['year']}:** {event['label']}")
        else:
            st.write("No specific events found for today in this region's recorded history.")


with tab2:
    st.header(f"Historical Timeline of {selected_region_name}")

    with st.spinner("Building the timeline... This may take a moment."):
        timeline_events = get_timeline_events(region_q_code, lang_code)

        if timeline_events:
            for event in timeline_events:
                with st.expander(f"**{event['date']}** - {event['label']}"):
                    st.write(event['description'])
        else:
            st.warning("Could not retrieve timeline events for this region. The data may not be available on Wikidata yet.")
