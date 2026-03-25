import logging
import pandas as pd
import pydeck as pdk
import streamlit as st
from dotenv import load_dotenv

from data_service import hamta_badplatser, hamta_vader, hamta_vattentemp
from utils import initiera_databas, spara_till_databas, hamta_kommuner

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
kommuner = hamta_kommuner(alla_badplatser)
vald_kommun = st.selectbox(" ", kommuner)

if vald_kommun == "Alla kommuner":
    filtrerade_badplatser = alla_badplatser
else:
    filtrerade_badplatser = [
        bad for bad in alla_badplatser if bad["kommun"] == vald_kommun
    ]

badplats_val = st.multiselect(
    " ",
    options=sorted([bad["namn"] for bad in filtrerade_badplatser if bad["namn"]]),
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

            rader = []
            for bad in valda_badplatser:
                lon, lat = bad["koordinater"]
                temp, vind = hamta_vader(lat, lon)
                vatten_temp = hamta_vattentemp(bad["id"])
                
                rader.append({
                    "Badplats": bad["namn"],
                    "Kommun": bad["kommun"],
                    "Temperatur (C)": temp,
                    "Vatten (C)": vatten_temp,
                    "Vind (m/s)": vind,
                    "lat": lat,
                    "lon": lon
                })

            df = pd.DataFrame(rader)
            spara_till_databas(rader)

            st.success(f" {len(df)} badplatser hittades.")

            st.subheader("Översikt")
            st.dataframe(
                df[["Badplats", "Kommun", "Temperatur (C)", "Vatten (C)", "Vind (m/s)"]],
                use_container_width=True
            )

            st.subheader("Karta över badplatser")
            if df.empty:
                st.info("Ingen data att visa på kartan.")
            else:
                view_state = pdk.ViewState(
                    latitude=df["lat"].mean(),
                    longitude=df["lon"].mean(),
                    zoom=6,
                    pitch=0
                )

                scatter = pdk.Layer(
                    "ScatterplotLayer",
                    data=df,
                    get_position="[lon, lat]",
                    get_fill_color="[255, 0, 0]",
                    get_radius=1,
                    radius_min_pixels=6,
                    radius_max_pixels=8,
                    pickable=True
                )

                tooltip = {
                    "html": "<b>{Badplats}</b><br>Vatten: {Vatten (C)} C",
                    "style": {"backgroundColor": "black", "color": "white"}
                }

                deck = pdk.Deck(
                    layers=[scatter],
                    initial_view_state=view_state,
                    tooltip=tooltip
                )

                st.pydeck_chart(deck, use_container_width=True)
