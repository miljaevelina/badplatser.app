import requests # IMPORTERAR BIBLIOTEKET FÖR ATT GÖRA HTTP-ANROP

# LÄNK TILL OFFICIELL DOKUMENTATION FÖR API-badplatser
badplatser_base = "https://badplatsen.havochvatten.se/badplatsen/api/feature/"

# DETTA KOPPLAR IHOP API:erna MED KOORDINATER FRÅN BADPLATS-API
def hamta_badplatser(kommuner): # DEFINIERAR EN FUNKTIONSOM TAR EN LISTA MED KOMMUNERNA SOM "ARGUMENT"
    try: # KÖR KODEN NEDAN 
        response = requests.get(badplatser_base, timeout=10) # UTFÖR GET-ANROP
        response.raise_for_status() # KASTAR ETT FEL OM HTTP-STATUSKODEN MISSLYCKAS VID FÖRFRÅGAN
        data = response.json() # HANTERAR OCH TOLKAR JSON-SVAREN SOM KONVERTERAS TILL API-SVAR FRÅN TEXT (JSON) TILL PYTHON-BIBLIOTEK OCH LISTOR
        features = data.get("features", []) # HÄMTAR EN LISTA MED ALLA BADPLATSER
        
        #DETTA HÄMTAR SPECIFIKA FÄLT FRÅN JSON
        badplatser = [] # SKAPAR EN TOM LISTA SOM FYLLS PÅ MED BADPLATSER NEDAN
        for item in features: # LOOPAR IGENOM BADPLATSERNA PÅ LISTAN 
            properties = item.get("properties", {}) # METADATA OM BADPLATSEN
            namn = properties.get("NAMN") # HÄMTAR BADPLATSENS NAMN
            kommun = properties.get("KMN_NAMN") # HÄMTAR KOMMUNNAMNEN FÖR BADPLATSERNA

            geometry = item.get("geometry") # HÄMTAR KOORDINATERNA (geometri-data) FÖR BADPLATSEN
            if geometry is None: # KONTROLLERAR OM GEOMETRI SAKNAS
                continue # HOPPAR ÖVER BADPLATS SOM SAKNAS FÖR ATT KUNNA GÅ VIDARE TILL NÄSTA

            coords = geometry.get("coordinates") # HÄMTAR SJÄLVA KOORDINATEN (LONGITUDE/LATITUDE) FÖR BADPLATSEN
            if coords is None: # KONTROLLERAR OM KOORDINATER SAKNAS
                continue # HOPPAR ÖVER BADPLATSER FÖR ATT KUNNA GÅ VIDARE TILL NÄSTA

            if kommun in kommuner: # KOONTROLLERAR OM BADPLATSENS KOMMUN FINNS MED PÅ DEN VALDA LISTAN
                badplatser.append({ # LÄGGER TILL BADPLATSEN I LISTAN MED NAMN, KOMMUN & KOORDINATER
                    "namn": namn,
                    "kommun": kommun,
                    "koordinater": coords
                })

        return badplatser # RETURNERAR DEN FÄRDIGA LISTAN MED BADPLATSER I SKÅNE

    except requests.exceptions.RequestException as e: # FÅNGAR NÄTVERKSFEL ELLER VID INGEN ANSLUTNING
        print("Fel vid hämtning av badplatser:", e)
        return [] # RETURNERAR TOM LISTA VID FEL
    except ValueError: # FÅNGAR FEL OM SVARET INTE KAN TOLKAS SOM JSON
        print("Svar kunde inte tolkas som JSON") 
        return [] # RETURNERAR TOM LISTA VID FEL 

 
def hamta_vader(lat, lon): # DEFINIERAR EN FUNKTION SOM TAR LATITUD OCH LONGITUD SOM ARGUMENT
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true" # LÄNK TILL OFFICIELL DOKUMENTATION FÖR API-väder & BYGGER API-ADRESSEN MED KOORDINATERNA
    
    # DETTA HÄMTAR JSON FRÅN VÄDER-API, VÄDER OCH VIND HÄMTAS FRÅN JSON-STRUKTUREN OCH JSON KONVERTERAR DET TILL PYTHON
    try:
        response = requests.get(url) # UTFÖR GET-ANROP TILL VÄDER-API
        response.raise_for_status() # KASTAR ETT FEL OM HTTP-STATUSKOD MISSLYCKAS VID FÖRFRÅGAN
        data = response.json() # TOLKAR JSON-SVARET OCH KONVERTERAR DET TILL PYTHON
        temp = data["current_weather"]["temperature"] # HÄMTAR TEMPERATUREN FRÅN JSON-STRUKTUREN
        vind = data["current_weather"]["windspeed"] # HÄMTAR VINDHASTIGEHETEN FRÅN JSON-STRUKTUREN
        return temp, vind # RETURNERAR TEMPERATUR OCH VIND 
    except Exception as e: # FÅNGAR ALLA FEL
        print("Fel vid väderhämtning:", e)
        return None, None # RETURNERAR INGET VÄRDE VID FEL


if __name__ == "__main__": # SÄKERSTÄLLER ATT KODEN NEDAN BARA KÖRS OM FILEN STARTAS DIREKT, INTE OM DEN IMPORTERAS
    kommuner = ["Eslöv", "Osby", "Malmö", "Lund", "Helsingborg"] # DEFINIERAR VILKA KOMMUNER SOM SKA SÖKAS UPP

    badplatser = hamta_badplatser(kommuner) # ANROPAR FUNKTIONEN OCH SPARAR RESULTATET I EN VARIABEL

    print("--- Väder över badplatser i Skåne ---:", len(badplatser))
    print("----------------------------------")

    for bad in badplatser: # LOOPAR IGENOM VARJE BADPLATS I RESULTATLISTAN
        namn = bad["namn"] # HÄMTAR NAMNET FRÅN BADPLATS-OBJEKTET
        kommun = bad["kommun"] # HÄMTAR KOMMUNEN FRÅN BADPLATS-OBJEKTET
        lon, lat = bad["koordinater"] # FRÅNGAR UPP KOORDINATERNA GEOJSON HAR ORDNINGEN LON, LAT

        temp, vind = hamta_vader(lat, lon) # ANROPAR VÄDERFUNKTIONEN MED KOORDINATERNA

        if temp is not None: # KONTROLLERAR ATT VÄDERHÄMTNINGEN LYCKAS INNAN UTSKRIFT
            print(f"Badplats: {namn}") 
            print(f"Kommun: {kommun}") 
            print(f"Temperatur: {temp} °C") 
            print(f"Vind: {vind} m/s")
            print("----------------------------------")