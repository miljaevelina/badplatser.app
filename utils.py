import sqlite3
import streamlit as st

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

def hamta_kommuner(badplatser):
    kommuner = sorted(set(bad["kommun"] for bad in badplatser if bad["kommun"]))
    return ["Alla kommuner"] + kommuner
