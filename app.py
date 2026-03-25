import logging

from dotenv import load_dotenv
import pandas as pd
import streamlit as st

from data_service import hamta_badplatser, hamta_vader
from utils import initiera_databas, spara_till_databas

load_dotenv()

logging.basicConfig(
    filename="app_logg.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

st.title("Vädret över badplatser i Sverige")
st.write("Välj en eller flera badplatser för att se aktuellt väder.")

initiera_databas()

alla_badplatser = hamta_badplatser()

badplats_val = st.multiselect(
    " ",
    options=sorted([bad["namn"] for bad in alla_badplatser if bad["namn"]]),
    placeholder="Välj badplats"
)

if st.button("Hämta badplatser och väder"):
    if not badplats_val:
        st.warning("Välj minst en badplats.")
    else:
        with st.spinner("Hämtar data från API:erna..."):
            valda_badplatser = [
                bad for bad in alla_badplatser if bad["namn"] in badplats_val
            ]

            if not valda_badplatser:
                st.warning("Inga badplatser hittades.")
            else:
                rader = []
                for bad in valda_badplatser:
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

                st.success(f"Hittade {len(df)} badplatser och sparade till databas.")

                st.subheader("Översikt")
                st.dataframe(
                    df[["Badplats", "Kommun", "Temperatur (C)", "Vind (m/s)"]],
                    use_container_width=True
                )

                for index, row in df.iterrows():
                    with st.expander(f"Detaljer: {row['Badplats']}"):
                        st.write(f"Kommun: {row['Kommun']}")
                        st.write(f"Temperatur: {row['Temperatur (C)']} °C")

                st.subheader("Karta över badplatser")
                st.map(df[["lat", "lon"]])
