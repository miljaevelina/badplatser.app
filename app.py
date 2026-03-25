import pandas as pd
import pydeck as pdk
import streamlit as st
from data_service import hamta_badplatser, hamta_vader, hamta_vattentemp
from utils import initiera_databas, spara_till_databas, hamta_kommuner

st.title("Vädret och vattentemp")

initiera_databas()
alla_badplatser = hamta_badplatser()
kommuner = hamta_kommuner(alla_badplatser)
vald_kommun = st.selectbox("Välj stad/kommun", kommuner)

filtrerade = alla_badplatser if vald_kommun == "Alla kommuner" else [b for b in alla_badplatser if b["kommun"] == vald_kommun]
badplats_val = st.multiselect(" ", options=sorted([b["namn"] for b in filtrerade]), placeholder="Välj badplats")

if st.button("Hämta data"):
    if not badplats_val:
        st.warning("Välj minst en badplats.")
    else:
        with st.spinner("Hämtar data..."):
            rader = []
            for bad in [b for b in alla_badplatser if b["namn"] in badplats_val]:
                lon, lat = bad["koordinater"]
                luft_temp, vind = hamta_vader(lat, lon)
                vatten_temp = hamta_vattentemp(bad["id"])
                
                rader.append({
                    "Badplats": bad["namn"],
                    "Kommun": bad["kommun"],
                    "Luft (C)": luft_temp,
                    "Vatten (C)": vatten_temp,
                    "Vind (m/s)": vind,
                    "lat": lat,
                    "lon": lon
                })

            df = pd.DataFrame(rader)
            st.dataframe(df.drop(columns=["lat", "lon"]), use_container_width=True)

            st.subheader("Karta")
            if not df.empty:
                deck = pdk.Deck(
                    layers=[pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', 
                            get_fill_color='[255, 0, 0]', get_radius=1, radius_min_pixels=6, pickable=True)],
                    initial_view_state=pdk.ViewState(latitude=df["lat"].mean(), longitude=df["lon"].mean(), zoom=6),
                    tooltip={"html": "<b>{Badplats}</b><br>Vatten: {Vatten (C)} C"}
                )
                st.pydeck_chart(deck, use_container_width=True)
