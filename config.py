# config.py

# --- Language Configuration ---
# Maps user-friendly names to Wikimedia language codes
LANGUAGES = {
    "English": "en",
    "हिंदी (Hindi)": "hi",
    "தமிழ் (Tamil)": "ta",
    "বাংলা (Bengali)": "bn",
    "ಕನ್ನಡ (Kannada)": "kn"
}

# --- Regional Configuration (The Hackathon MVP Secret Sauce) ---
# This dictionary maps states to their Wikidata Q-codes.
# We also pre-select featured items for a reliable dashboard experience.
# To add a new state, find its Q-code on Wikidata and add it here.
REGIONS = {
    "Karnataka": {
        "q_code": "Q1185",
        "featured_figure": "Q3349636",  # Krishnadevaraya
        "featured_monument": "Q34998", # Hampi
    },
    "Maharashtra": {
        "q_code": "Q1191",
        "featured_figure": "Q43416",  # Shivaji
        "featured_monument": "Q11438", # Ajanta Caves
    },
    "Tamil Nadu": {
        "q_code": "Q1445",
        "featured_figure": "Q372138", # Rajaraja I
        "featured_monument": "Q24916262", # Great Living Chola Temples
    },
    "Uttar Pradesh": {
        "q_code": "Q1498",
        "featured_figure": "Q80093", # Rani Lakshmibai
        "featured_monument": "Q9542", # Taj Mahal
    },
    "West Bengal": {
        "q_code": "Q1588",
        "featured_figure": "Q2149", # Subhas Chandra Bose
        "featured_monument": "Q190691", # Sundarbans National Park
    }
}
