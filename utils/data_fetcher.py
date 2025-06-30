# utils/data_fetcher.py

import requests
import wikipediaapi
import datetime
from config import REGIONS # Import our configuration

# --- Wikidata SPARQL Query Functions ---

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

def run_sparql_query(query):
    """Sends a SPARQL query to the Wikidata endpoint and returns the JSON response."""
    headers = {'User-Agent': 'ItihasExplorer/1.0 (Hackathon)', 'Accept': 'application/json'}
    try:
        response = requests.get(WIKIDATA_ENDPOINT, headers=headers, params={'query': query, 'format': 'json'})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error running SPARQL query: {e}")
        return None

def get_entity_details(entity_q_code, lang_code='en'):
    """Fetches the label, description, and Wikipedia page title for a given Wikidata Q-code."""
    query = f"""
    SELECT ?label ?description ?article WHERE {{
      BIND(wd:{entity_q_code} AS ?item)
      ?item rdfs:label ?label.
      OPTIONAL {{ ?item schema:description ?description. FILTER(LANG(?description) = "{lang_code}") }}
      OPTIONAL {{
        ?article schema:about ?item .
        ?article schema:inLanguage "{lang_code}" .
        FILTER (SUBSTR(str(?article), 1, 25) = "https://{lang_code}.wikipedia.org/")
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

def get_on_this_day_events(region_q_code, lang_code='en'):
    """Finds historical events for the current month and day located in the selected region."""
    today = datetime.datetime.now()
    month = today.month
    day = today.day

    query = f"""
    SELECT ?eventLabel ?eventDescription ?date WHERE {{
      ?event wdt:P31/wdt:P279* wd:Q198. # Instance of 'historical event' or its subclasses
      ?event wdt:P131 wd:{region_q_code}. # Located in the selected region
      ?event wdt:P585 ?date.
      FILTER(MONTH(?date) = {month} && DAY(?date) = {day})
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang_code},en". }}
    }}
    ORDER BY ?date
    LIMIT 5
    """
    data = run_sparql_query(query)
    events = []
    if data and data['results']['bindings']:
        for item in data['results']['bindings']:
            events.append({
                "label": item.get('eventLabel', {}).get('value', 'Event'),
                "description": item.get('eventDescription', {}).get('value', 'No description.'),
                "year": datetime.datetime.strptime(item.get('date', {}).get('value'), '%Y-%m-%dT%H:%M:%SZ').year
            })
    return events

def get_timeline_events(region_q_code, lang_code='en'):
    """Fetches major historical events for a region, sorted by date."""
    query = f"""
    SELECT ?eventLabel ?eventDescription ?date WHERE {{
      ?event wdt:P31/wdt:P279* wd:Q198.
      ?event wdt:P131 wd:{region_q_code}.
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
                "date": datetime.datetime.strptime(item.get('date', {}).get('value'), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
            })
    return events


# --- Wikipedia API Functions ---

def get_wiki_summary_and_image(page_title, lang_code='en'):
    """Fetches summary and main image URL from a Wikipedia page."""
    wiki_api = wikipediaapi.Wikipedia(
        language=lang_code,
        user_agent="ItihasExplorer/1.0 (Hackathon)"
    )
    page = wiki_api.page(page_title)
    if not page.exists():
        return {"summary": "Wikipedia page not found.", "image_url": None}

    # Fetch summary (first ~150 words)
    summary = ' '.join(page.summary.split(' ')[:150]) + '...'

    # Fetch main image
    image_url = None
    if page.images:
        # This is a heuristic to find the main page image, might need refinement
        for img in page.images:
             if img.lower().endswith(('.jpg', '.jpeg', '.png')) and 'logo' not in img.lower() and 'flag' not in img.lower():
                image_url = page.images[img]
                break
    
    # A better way if the first one fails
    if not image_url and page.sections:
        for sec in page.sections:
            if 'gallery' not in sec.title.lower():
                for img_title, img_url in sec.images.items():
                    if img_title.lower().endswith(('.jpg', '.jpeg', '.png')):
                        image_url = img_url
                        break
                if image_url:
                    break

    return {"summary": summary, "image_url": image_url}
