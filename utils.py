import sqlite3

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
            vattentemp REAL,
            vind REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(badplatser)")
    kolumner = [kolumn[1] for kolumn in cursor.fetchall()]

    if "vattentemp" not in kolumner:
        cursor.execute("ALTER TABLE badplatser ADD COLUMN vattentemp REAL")

    conn.commit()
    conn.close()

def spara_till_databas(data_lista):
    conn = sqlite3.connect("badplatser.db")
    cursor = conn.cursor()

    for item in data_lista:
        cursor.execute("""
            INSERT INTO badplatser (namn, kommun, lat, lon, temp, vattentemp, vind)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item["Badplats"],
            item["Kommun"],
            item["lat"],
            item["lon"],
            item["Temperatur (C)"],
            item.get("Vatten (C)"),
            item["Vind (m/s)"]
        ))

    conn.commit()
    conn.close()

def hamta_kommuner(badplatser):
    kommuner = sorted(set(
        bad["kommun"] for bad in badplatser if bad["kommun"]
    ))
    return ["Alla kommuner"] + kommuner
