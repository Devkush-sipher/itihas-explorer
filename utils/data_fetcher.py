# utils/data_fetcher.py

import requests
import wikipediaapi
import datetime
import streamlit as st
from config import REGIONS

# --- Wikidata SPARQL Query Functions ---

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

@st.cache_data(ttl=3600) # Cache data for 1 hour
def run_sparql_query(query):
    """Sends a SPARQL query to the Wikidata endpoint and returns the JSON response."""
    headers = {'User-Agent': 'ItihasExplorer/1.0 (Hackathon)', 'Accept': 'application/json'}
    try:
        response = requests.get(WIKIDATA_ENDPOINT, headers=headers, params={'query': query, 'format': 'json'})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: Could not connect to Wikidata. Please check your connection. Details: {e}")
        return None

@st.cache_data(ttl=3600)
def get_entity_details(entity_q_code, lang_code='en'):
    """Fetches the label, description, and Wikipedia page title for a given Wikidata Q-code."""
    query = f"""
    SELECT ?label ?description ?article WHERE {{
      BIND(wd:{entity_q_code} AS ?item)
      ?item rdfs:label ?label.
      OPTIONAL {{ ?item schema:description ?description. FILTER(LANG(?description) = "{lang_code}") }}
      OPTIONAL {{
        ?article schema:about ?item ;
                 schema:inLanguage "{lang_code}" ;
                 schema:isPartOf <https://{lang_code}.wikipedia.org/>.
      }}
      FILTER(LANG(?label) = "{lang_code}")
    }} LIMIT 1
    """
    data = run_sparql_query(query)
    if data and data['results']['bindings']:
        binding = data['results']['bindings'][0]
        return {
            "label": binding.get('label', {}).get('value', 'N/A'),
            "description": binding.get('description', {}).get('value', 'No description available.'),
            "page_title": binding.get('article', {}).get('value', '').split('/')[-1]
        }
    return None

@st.cache_data(ttl=3600)
def get_on_this_day_events(region_q_code, lang_code='en'):
    """Finds historical events for the current month and day located in the selected region."""
    today = datetime.datetime.now()
    month = today.month
    day = today.day

    # This query is simplified and might not always return results.
    # A more robust implementation would check for events without a specific day as well.
    query = f"""
    SELECT ?eventLabel ?date WHERE {{
      ?event wdt:P17 wd:Q668 . # Is in India
      ?event p:P131 ?statement .
      ?statement ps:P131 wd:{region_q_code} . # Located in region
      ?event wdt:P585 ?date.
      FILTER(MONTH(?date) = {month} && DAY(?date) = {day})
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang_code},en". }}
    }} LIMIT 5
    """
    data = run_sparql_query(query)
    events = []
    if data and data['results']['bindings']:
        for item in data['results']['bindings']:
            date_str = item.get('date', {}).get('value')
            if date_str:
                 events.append({
                    "label": item.get('eventLabel', {}).get('value', 'Event'),
                    "year": datetime.datetime.fromisoformat(date_str.replace('Z', '')).year
                })
    return events

@st.cache_data(ttl=3600)
def get_timeline_events(region_q_code, lang_code='en'):
    """Fetches major historical events for a region, sorted by date."""
    query = f"""
    SELECT ?eventLabel ?eventDescription ?date WHERE {{
      ?event wdt:P31/wdt:P279* wd:Q198. # Instance of 'historical event' or its subclasses
      ?event p:P131 ?statement .
      ?statement ps:P131 wd:{region_q_code} .
      ?event wdt:P585 ?date.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang_code},en". }}
    }}
    ORDER BY ?date
    LIMIT 25
    """
    data = run_sparql_query(query)
    events = []
    if data and data['results']['bindings']:
        for item in data['results']['bindings']:
            events.append({
                "label": item.get('eventLabel', {}).get('value', 'Event'),
                "description": item.get('eventDescription', {}).get('value', 'No description.'),
                "date": datetime.datetime.fromisoformat(item.get('date', {}).get('value').replace('Z', '')).strftime('%d %B %Y')
            })
    return events


# --- Wikipedia API Functions ---

@st.cache_data(ttl=3600)
def get_wiki_summary_and_image(page_title, lang_code='en'):
    """
    Fetches summary and a suitable image URL from a Wikipedia page.
    This function is now robust against non-existent pages and lack of images.
    """
    if not page_title:
        return {"summary": "No Wikipedia article found for this entry.", "image_url": None}

    wiki_api = wikipediaapi.Wikipedia(
        language=lang_code,
        user_agent="ItihasExplorer/1.0 (Hackathon)"
    )
    page = wiki_api.page(page_title)

    if not page.exists():
        return {"summary": f"The Wikipedia article '{page_title}' does not exist in this language.", "image_url": None}

    # Fetch summary (first ~100 words)
    summary = ' '.join(page.summary.split(' ')[:100])
    if len(page.summary.split(' ')) > 100:
        summary += '...'

    # Find a suitable image
    image_url = None
    # Prioritize the main page image if available
    if hasattr(page, 'fullurl') and 'action=view' not in page.fullurl: # A heuristic check
        if page.thumbnail:
            image_url = page.thumbnail

    # If no main image, search sections for the first usable image
    if not image_url:
        for section in page.sections:
            for img_title in section.images:
                # Basic filter to avoid icons and flags
                if img_title.lower().endswith(('.jpg', '.jpeg', '.png')):
                     # We need to construct the URL manually or use another API call.
                     # For simplicity, we'll skip this complex part in a hackathon.
                     # The thumbnail is the most reliable approach with this library.
                    break
            if image_url:
                break
    
    return {"summary": summary, "image_url": image_url}
