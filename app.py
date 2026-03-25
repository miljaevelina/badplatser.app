import logging

from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import pydeck as pdk

from data_service import hamta_badplatser, hamta_vader
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
vald_kommun = st.selectbox("Välj stad/kommun", kommuner)

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

                st.subheader("Karta över badplatser")

                if df.empty:
                    st.info("Ingen data att visa på kartan.")
                else:
                    center_lat = df["lat"].mean()
                    center_lon = df["lon"].mean()

                    view_state = pdk.ViewState(
                        latitude=center_lat,
                        longitude=center_lon,
                        zoom=6,
                        pitch=0
                    )

                    scatter = pdk.Layer(
                        "ScatterplotLayer",
                        data=df,
                        get_position='[lon, lat]',
                        get_fill_color='[255, 0, 0]',
                        get_radius=10,        # Ändra till ett litet värde
                        radius_min_pixels=5,  # Minsta storlek i pixlar
                        radius_max_pixels=10, # Maxstorlek i pixlar
                        pickable=True
                    )

                    tooltip = {
                        "html": "<b>{Badplats}</b><br>Kommun: {Kommun}",
                        "style": {"backgroundColor": "black", "color": "white"}
                    }

                    deck = pdk.Deck(
                        layers=[scatter],
                        initial_view_state=view_state,
                        tooltip=tooltip
                    )

                    st.pydeck_chart(deck)
