import time
import requests
import streamlit as st

badplatser_base = "https://badplatsen.havochvatten.se/badplatsen/api/feature/"

MIN_INTERVALL = 0.3
senaste_anrop = {"badplatser": 0, "vader": 0, "detaljer": 0}

def rate_limit(api_namn):
    nu = time.time()
    tid_sedan_sist = nu - senaste_anrop[api_namn]
    if tid_sedan_sist < MIN_INTERVALL:
        time.sleep(MIN_INTERVALL - tid_sedan_sist)
    senaste_anrop[api_namn] = time.time()

@st.cache_data(ttl=3600)
def hamta_badplatser():
    try:
        rate_limit("badplatser")
        response = requests.get(badplatser_base, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        badplatser = []
        for item in data.get("features", []):
            props = item.get("properties", {})
            geo = item.get("geometry")
            if geo and geo.get("coordinates"):
                badplatser.append({
                    "namn": props.get("NAMN"),
                    "kommun": props.get("KMN_NAMN"),
                    "koordinater": geo.get("coordinates"),
                    "id": props.get("NUTS_CODE")
                })
        return badplatser
    except:
        return []

@st.cache_data(ttl=600)
def hamta_vader(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        rate_limit("vader")
        data = requests.get(url, timeout=10).json()
        return data["current_weather"]["temperature"], data["current_weather"]["windspeed"]
    except:
        return None, None

@st.cache_data(ttl=3600)
def hamta_vattentemp(nuts_code):
    if not nuts_code: return None
    url = f"https://badplatsen.havochvatten.se/badplatsen/api/detail/{nuts_code}"
    try:
        rate_limit("detaljer")
        data = requests.get(url, timeout=10).json()
        # Hämtar senaste vattentemperaturen från listan om den finns
        coper = data.get("coperSmhiList", [])
        if coper:
            return coper[0].get("temperature")
        return None
    except:
        return None
