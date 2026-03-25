import logging

from dotenv import load_dotenv 
import pandas as pd
import streamlit as st

from data_service import hamta_badplatser, hamta_vader, markera_som_favorit
from utils import initiera_databas, spara_till_databas

load_dotenv()

logging.basicConfig(
    filename="app_logg.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

st.title("Vädret över badplatser i Skåne")
st.write("Välj en eller flera kommuner för att se aktuellt väder över badplatser.")

initiera_databas()

kommuner_val = st.multiselect(
    " ",
    options=["Eslöv", "Osby", "Malmö", "Lund", "Helsingborg"],
    placeholder="Välj kommun"
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

                        if st.button(f"Spara {row['Badplats']} som favorit", key=f"fav_{index}"):
                            if markera_som_favorit(row["Badplats"]):
                                st.toast(f"{row['Badplats']} har sparats som favorit!")
                            else:
                                st.error("Kunde inte spara favoriten.")

                st.subheader("Karta över badplatser")
                st.map(df[["lat", "lon"]])
