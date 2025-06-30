# utils/data_fetcher.py

import requests
import wikipediaapi
import datetime
import streamlit as st

# --- Wikidata SPARQL Query Functions ---
# (No changes needed in the Wikidata functions, but they are included for completeness)

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

@st.cache_data(ttl=3600)
def run_sparql_query(query):
    headers = {'User-Agent': 'ItihasExplorer/1.0 (Hackathon)', 'Accept': 'application/json'}
    try:
        response = requests.get(WIKIDATA_ENDPOINT, headers=headers, params={'query': query, 'format': 'json'})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: Could not connect to Wikidata. Details: {e}")
        return None

@st.cache_data(ttl=3600)
def get_entity_details(entity_q_code, lang_code='en'):
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
    today = datetime.datetime.now()
    month = today.month
    day = today.day
    query = f"""
    SELECT ?eventLabel ?date WHERE {{
      ?event wdt:P17 wd:Q668 .
      ?event p:P131 ?statement .
      ?statement ps:P131 wd:{region_q_code} .
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
    query = f"""
    SELECT ?eventLabel ?eventDescription ?date WHERE {{
      ?event wdt:P31/wdt:P279* wd:Q198.
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

def _get_image_url_from_api(page_title, lang_code):
    """
    Helper function to get the main image URL directly from the MediaWiki API.
    This is much more reliable than parsing with the wikipedia-api library.
    """
    API_URL = f"https://{lang_code}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "pageimages",
        "pithumbsize": 500,  # Request a thumbnail of 500px width
        "pilicense": "any"
    }
    try:
        response = requests.get(API_URL, params=params, headers={'User-Agent': 'ItihasExplorer/1.0'})
        response.raise_for_status()
        data = response.json()
        # The response structure is nested. We need to navigate it carefully.
        page_id = next(iter(data['query']['pages']))
        if page_id != "-1" and 'thumbnail' in data['query']['pages'][page_id]:
            return data['query']['pages'][page_id]['thumbnail']['source']
    except Exception as e:
        print(f"Could not fetch image for '{page_title}'. Error: {e}")
    return None


@st.cache_data(ttl=3600)
def get_wiki_summary_and_image(page_title, lang_code='en'):
    """
    Fetches summary using the 'wikipedia-api' library and the main image
    using a direct MediaWiki API call for reliability.
    """
    if not page_title:
        return {"summary": "No Wikipedia article found for this entry.", "image_url": None}

    # --- Step 1: Get summary using the wrapper library (it's good at this) ---
    wiki_api = wikipediaapi.Wikipedia(
        language=lang_code,
        user_agent="ItihasExplorer/1.0 (Hackathon)"
    )
    page = wiki_api.page(page_title)

    if not page.exists():
        return {"summary": f"The Wikipedia article '{page_title}' does not exist in this language.", "image_url": None}

    summary = ' '.join(page.summary.split(' ')[:100])
    if len(page.summary.split(' ')) > 100:
        summary += '...'

    # --- Step 2: Get the image using our robust, direct API call ---
    image_url = _get_image_url_from_api(page_title, lang_code)

    return {"summary": summary, "image_url": image_url}
