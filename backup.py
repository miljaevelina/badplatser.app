import os
import time
import sqlite3

from dotenv import load_dotenv
import requests
import streamlit as st
import pandas as pd
import logging

load_dotenv()
logging.basicConfig(
    filename="app_logg.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
                st.error("Badplats-API svarar inte just nu. Försök igen senare.")
                return []

        except ValueError:
            st.error("Svar från Badplats-API kunde inte tolkas som JSON.")
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

def initiera_databas():
    conn = sqlite3.connect("badplatser.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badplatser (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            namn TEXT,
            kommun TEXT,
            lat REAL,
            lon REAL,
            temp REAL,
            vind REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def spara_till_databas(data_lista):
    conn = sqlite3.connect("badplatser.db")
    cursor = conn.cursor()
    for item in data_lista:
        cursor.execute("""
            INSERT INTO badplatser (namn, kommun, lat, lon, temp, vind)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item["Badplats"], item["Kommun"], item["lat"], item["lon"],
              item["Temperatur (C)"], item["Vind (m/s)"]))
    conn.commit()
    conn.close()

def visa_systemkarta():
    karta = """
+----------------+        GET JSON         +------------------+
|  Python App    |----------------------->|  Badplats-API    |
|                |                        | (HaV)            |
|  - Start       |                        |                  |
|  - Filtrera    |<-----------------------| JSON: namn,      |
|    badplatser  |                        | kommun, coords   |
+----------------+                        +------------------+
        |
        | Koordinater (lat/lon)
        v
+----------------+        GET JSON         +------------------+
| Python App     |----------------------->|  Open-Meteo API  |
| - Hämta väder  |                        |                  |
| - Tolka JSON   |<-----------------------| JSON: temp, vind |
+----------------+                        +------------------+
        |
        v
+----------------+
| Streamlit UI   |
| - Tabell       |
| - Karta        |
+----------------+
    """
    st.code(karta, language=None)

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

st.title("Badplatser och väder i Skåne")
st.write("Välj en eller flera kommuner för att se aktuellt väder över badplatser.")

initiera_databas()

kommuner_val = st.multiselect(
    "Välj kommuner",
    options=["Eslöv", "Osby", "Malmö", "Lund", "Helsingborg"],
    default=["Eslöv", "Osby"]
)

if st.button("Hämta badplatser och väder"):

    if not kommuner_val:
        st.warning("Välj minst en kommun.")
    else:
        with st.spinner("Hämtar data från API:erna..."):
            badplatser = hamta_badplatser(kommuner_val)

            if not badplatser:
                st.warning("Inga badplatser hittades för valda kommuner.")
            else:
                rader = []
                for bad in badplatser:
                    lon, lat = bad["koordinater"]
                    temp, vind = hamta_vader(lat, lon)
                    rader.append({
                        "Badplats": bad["namn"],
                        "Kommun": bad["kommun"],
                        "Temperatur (C)": temp,
                        "Vind (m/s)": vind,
                        "lat": lat,
                        "lon": lon
                    })

                df = pd.DataFrame(rader)
                spara_till_databas(rader)

                st.success(f"Hittade{len(df)} badplatser och sparade till databas.")

                st.subheader("Översikt")
                st.dataframe(
                    df[["Badplats", "Kommun", "Temperatur (C)", "Vind (m/s)"]],
                    use_container_width=True
                )

                for index, row in df.iterrows():
                    with st.expander(f"Detaljer: {row['Badplats']}"):
                        st.write(f"Kommun: {row['Kommun']}")
                        st.write(f"Temperatur: {row['Temperatur (C)']} °C")
                        
                        if st.button(f"Spara {row['Badplats']} som favorit", key=f"fav_{index}"):
                            if markera_som_favorit(row["Badplats"]):
                                st.toast(f"{row['Badplats']} har sparats som favorit!", icon="✅")
                            else:
                                st.error("Kunde inte spara favoriten.")

                st.subheader("Karta över badplatser")
                st.map(df[["lat", "lon"]])

if st.checkbox("Visa systemkarta"):
    st.subheader("Systemkarta - dataflöde")
    visa_systemkarta()