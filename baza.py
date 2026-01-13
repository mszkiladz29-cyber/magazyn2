import streamlit as st
import psycopg2 # ZAMIAST sqlite3
import pandas as pd

# Pobranie URL z Secrets
DB_URL = st.secrets["DATABASE_URL"]

def get_connection():
    # Łączymy się z Supabase przez URL
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Składnia PostgreSQL: SERIAL zamiast AUTOINCREMENT
    c.execute('''CREATE TABLE IF NOT EXISTS kategorie (
                    id SERIAL PRIMARY KEY,
                    nazwa TEXT NOT NULL,
                    opis TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produkty (
                    id SERIAL PRIMARY KEY,
                    nazwa TEXT NOT NULL,
                    liczba INTEGER,
                    cena NUMERIC,
                    kategoria_id INTEGER REFERENCES kategorie(id))''')
    conn.commit()
    conn.close()

def get_data(query):
    conn = get_connection()
    # pandas automatycznie obsłuży połączenie
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    # W PostgreSQL używamy %s zamiast ?
    c.execute(query, params)
    conn.commit()
    conn.close()

# --- RESZTA INTERFEJSU (ZMIANA ? NA %s) ---
init_db()

st.title("📦 System Zarządzania Magazynem (Supabase)")

menu = ["Produkty", "Kategorie", "Zarządzaj Danymi"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Zarządzaj Danymi":
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Dodaj Kategorię"):
            nazwa_kat = st.text_input("Nazwa Kategorii")
            opis_kat = st.text_area("Opis")
            if st.button("Zapisz Kategorię"):
                # Zmieniono ? na %s
                execute_query("INSERT INTO kategorie (nazwa, opis) VALUES (%s, %s)", (nazwa_kat, opis_kat))
                st.success(f"Dodano kategorię: {nazwa_kat}")

        with st.expander("Dodaj Produkt"):
            nazwa_prod = st.text_input("Nazwa Produktu")
            liczba = st.number_input("Ilość", min_value=0)
            cena = st.number_input("Cena", min_value=0.0)
            kat_df = get_data("SELECT id, nazwa FROM kategorie")
            
            if not kat_df.empty:
                kat_options = {row['nazwa']: row['id'] for _, row in kat_df.iterrows()}
                wybrana_kat = st.selectbox("Wybierz kategorię", options=list(kat_options.keys()))
                if st.button("Zapisz Produkt"):
                    # Zmieniono ? na %s
                    execute_query("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (%s, %s, %s, %s)",
                                  (nazwa_prod, liczba, cena, kat_options[wybrana_kat]))
                    st.success(f"Dodano produkt: {nazwa_prod}")

    with col2:
        # Sekcja usuwania (również zamień ? na %s w zapytaniach DELETE)
        st.warning("Usuń elementy")
        # ... analogicznie jak wyżej ...
        # execute_query("DELETE FROM produkty WHERE id = %s", (int(id_prod),))
