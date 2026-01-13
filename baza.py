import streamlit as st
import sqlite3
import pandas as pd

# Konfiguracja bazy danych
DB_NAME = "magazyn.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tworzenie tabeli Kategorie
    c.execute('''CREATE TABLE IF NOT EXISTS kategorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    opis TEXT)''')
    # Tworzenie tabeli Produkty
    c.execute('''CREATE TABLE IF NOT EXISTS produkty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    liczba INTEGER,
                    cena REAL,
                    kategoria_id INTEGER,
                    FOREIGN KEY (kategoria_id) REFERENCES kategorie(id))''')
    conn.commit()
    conn.close()

def get_data(query):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Inicjalizacja bazy przy starcie
init_db()

st.title("📦 System Zarządzania Magazynem")

menu = ["Produkty", "Kategorie", "Zarządzaj Danymi"]
choice = st.sidebar.selectbox("Menu", menu)

# --- SEKCJA PRODUKTY ---
if choice == "Produkty":
    st.subheader("Lista Produktów")
    query = '''SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
               FROM produkty p LEFT JOIN kategorie k ON p.kategoria_id = k.id'''
    df_prod = get_data(query)
    st.dataframe(df_prod, use_container_width=True)

# --- SEKCJA KATEGORIE ---
elif choice == "Kategorie":
    st.subheader("Lista Kategorii")
    df_kat = get_data("SELECT * FROM kategorie")
    st.table(df_kat)

# --- SEKCJA ZARZĄDZAJ (DODAWANIE I USUWANIE) ---
elif choice == "Zarządzaj Danymi":
    col1, col2 = st.columns(2)

    with col1:
        st.info("➕ Dodaj Nowe Elementy")
        
        # Formularz Kategorii
        with st.expander("Dodaj Kategorię"):
            nazwa_kat = st.text_input("Nazwa Kategorii")
            opis_kat = st.text_area("Opis")
            if st.button("Zapisz Kategorię"):
                execute_query("INSERT INTO kategorie (nazwa, opis) VALUES (?, ?)", (nazwa_kat, opis_kat))
                st.success(f"Dodano kategorię: {nazwa_kat}")

        # Formularz Produktu
        with st.expander("Dodaj Produkt"):
            nazwa_prod = st.text_input("Nazwa Produktu")
            liczba = st.number_input("Ilość", min_value=0, step=1)
            cena = st.number_input("Cena", min_value=0.0, step=0.01)
            
            # Pobranie kategorii do selectboxa
            kat_df = get_data("SELECT id, nazwa FROM kategorie")
            kat_options = {row['nazwa']: row['id'] for _, row in kat_df.iterrows()}
            wybrana_kat = st.selectbox("Wybierz kategorię", options=list(kat_options.keys()))

            if st.button("Zapisz Produkt"):
                execute_query("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)",
                              (nazwa_prod, liczba, cena, kat_options[wybrana_kat]))
                st.success(f"Dodano produkt: {nazwa_prod}")

    with col2:
        st.warning("🗑️ Usuń Elementy")
        
        # Usuwanie Produktu
        st.subheader("Usuń Produkt")
        prod_df = get_data("SELECT id, nazwa FROM produkty")
        prod_to_del = st.selectbox("Wybierz produkt do usunięcia", prod_df['nazwa'].tolist())
        if st.button("Usuń Produkt"):
            id_prod = prod_df[prod_df['nazwa'] == prod_to_del]['id'].values[0]
            execute_query("DELETE FROM produkty WHERE id = ?", (int(id_prod),))
            st.rerun()

        # Usuwanie Kategorii
        st.subheader("Usuń Kategorię")
        kat_df_del = get_data("SELECT id, nazwa FROM kategorie")
        kat_to_del = st.selectbox("Wybierz kategorię do usunięcia", kat_df_del['nazwa'].tolist())
        if st.button("Usuń Kategorię"):
            id_kat = kat_df_del[kat_df_del['nazwa'] == kat_to_del]['id'].values[0]
            execute_query("DELETE FROM kategorie WHERE id = ?", (int(id_kat),))
            st.rerun()
