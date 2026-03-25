import os
import time
import requests
import streamlit as st
import logging

badplatser_base = "https://badplatsen.havochvatten.se/badplatsen/api/feature/"

MIN_INTERVALL = 0.3
senaste_anrop = {
    "badplatser": 0,
    "vader": 0
}

def rate_limit(api_namn):
    nu = time.time()
    tid_sedan_sist = nu - senaste_anrop[api_namn]
    if tid_sedan_sist < MIN_INTERVALL:
        time.sleep(MIN_INTERVALL - tid_sedan_sist)
    senaste_anrop[api_namn] = time.time()

@st.cache_data(ttl=3600)
def hamta_badplatser(kommuner):
    for forsok in range(3):
        try:
            rate_limit("badplatser")
            response = requests.get(badplatser_base, timeout=10)
            response.raise_for_status()
            data = response.json()
            features = data.get("features", [])
            
            badplatser = []
            for item in features:
                properties = item.get("properties", {})
                namn = properties.get("NAMN")
                kommun = properties.get("KMN_NAMN")
                geometry = item.get("geometry")
                
                if geometry is None:
                    continue
                coords = geometry.get("coordinates")
                if coords is None:
                    continue
                
                if kommun in kommuner:
                    badplatser.append({
                        "namn": namn,
                        "kommun": kommun,
                        "koordinater": coords
                    })
            return badplatser
        except requests.exceptions.RequestException:
            if forsok < 2:
                time.sleep(2)
            else:
                st.error("Badplats-API svarar inte just nu.")
                return []
        except ValueError:
            st.error("Svar från Badplats-API kunde inte tolkas.")
            return []

@st.cache_data(ttl=600)
def hamta_vader(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    for forsok in range(3):
        try:
            rate_limit("vader")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            temp = data["current_weather"]["temperature"]
            vind = data["current_weather"]["windspeed"]
            return temp, vind
        except requests.exceptions.RequestException:
            if forsok < 2:
                time.sleep(2)
            else:
                return None, None
        except ValueError:
            return None, None

def markera_som_favorit(badplats_namn):
    token = os.getenv("API_TOKEN")
    url = "https://jsonplaceholder.typicode.com/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": "Favoritbadplats",
        "body": f"Badplatsen {badplats_namn} har markerats som favorit.",
        "userId": 1
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        logging.info(f"Favorit sparad: {badplats_namn}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Kunde inte spara {badplats_namn}. Fel: {e}")
        return False    
