import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px  # Dodatkowe wykresy

# Konfiguracja strony
st.set_page_config(page_title="Magazyn Pro", layout="wide", page_icon="📦")

DB_NAME = "magazyn.db"

# --- LOGIKA BAZY DANYCH ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    c.execute('''CREATE TABLE IF NOT EXISTS kategorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL UNIQUE,
                    opis TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produkty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    liczba INTEGER DEFAULT 0,
                    cena REAL DEFAULT 0.0,
                    kategoria_id INTEGER,
                    FOREIGN KEY (kategoria_id) REFERENCES kategorie(id) ON DELETE CASCADE)''')
    conn.commit()
    conn.close()

def get_data(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_query(query, params=()):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return False

init_db()

# --- SIDEBAR / MENU ---
st.sidebar.title("🎮 Panel Sterowania")
menu = ["📊 Dashboard", "📦 Produkty", "📂 Kategorie", "⚙️ Ustawienia"]
choice = st.sidebar.radio("Nawigacja", menu)

# --- 1. DASHBOARD (STATYSTYKI) ---
if choice == "📊 Dashboard":
    st.title("📊 Analiza Magazynu")
    
    df = get_data('''SELECT p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
                     FROM produkty p JOIN kategorie k ON p.kategoria_id = k.id''')
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Suma Produktów", int(df['liczba'].sum()))
        col2.metric("Wartość Magazynu", f"{ (df['liczba'] * df['cena']).sum():,.2f} zł")
        col3.metric("Liczba Kategorii", df['kategoria'].nunique())

        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df, values='liczba', names='kategoria', title="Podział ilościowy na kategorie")
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            df['wartosc'] = df['liczba'] * df['cena']
            fig2 = px.bar(df, x='nazwa', y='wartosc', color='kategoria', title="Wartość poszczególnych produktów")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Baza jest pusta. Dodaj dane w sekcji Ustawienia.")

# --- 2. PRODUKTY (WIDOK I WYSZUKIWANIE) ---
elif choice == "📦 Produkty":
    st.title("📦 Przegląd Produktów")
    
    search = st.text_input("🔍 Szukaj produktu po nazwie...")
    query = '''SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
               FROM produkty p LEFT JOIN kategorie k ON p.kategoria_id = k.id'''
    
    df_prod = get_data(query)
    if search:
        df_prod = df_prod[df_prod['nazwa'].str.contains(search, case=False)]

    st.dataframe(df_prod, use_container_width=True, hide_index=True)

# --- 3. KATEGORIE ---
elif choice == "📂 Kategorie":
    st.title("📂 Zarządzanie Kategoriami")
    df_kat = get_data("SELECT id, nazwa, opis FROM kategorie")
    st.table(df_kat)

# --- 4. USTAWIENIA (EDYCJA, DODAWANIE, USUWANIE) ---
elif choice == "⚙️ Ustawienia":
    st.title("⚙️ Administracja Danymi")
    
    tab1, tab2, tab3 = st.tabs(["➕ Dodaj", "📝 Edytuj", "🗑️ Usuń"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Nowy Produkt")
            n_name = st.text_input("Nazwa")
            n_qty = st.number_input("Ilość", min_value=0)
            n_price = st.number_input("Cena", min_value=0.0)
            kat_data = get_data("SELECT id, nazwa FROM kategorie")
            n_kat = st.selectbox("Kategoria", options=kat_data['nazwa'].tolist())
            if st.button("Dodaj Produkt"):
                k_id = kat_data[kat_data['nazwa'] == n_kat]['id'].values[0]
                execute_query("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?,?,?,?)", 
                              (n_name, n_qty, n_price, int(k_id)))
                st.success("Produkt dodany!")

        with c2:
            st.subheader("Nowa Kategoria")
            nk_name = st.text_input("Nazwa Kategorii")
            nk_desc = st.text_area("Opis Kategorii")
            if st.button("Dodaj Kategorię"):
                execute_query("INSERT INTO kategorie (nazwa, opis) VALUES (?,?)", (nk_name, nk_desc))
                st.rerun()

    with tab2:
        st.subheader("Szybka edycja ilości/ceny")
        edit_df = get_data("SELECT id, nazwa, liczba, cena FROM produkty")
        edited_data = st.data_editor(edit_df, key="prod_editor", hide_index=True)
        if st.button("Zapisz zmiany w tabeli"):
            for index, row in edited_data.iterrows():
                execute_query("UPDATE produkty SET liczba = ?, cena = ? WHERE id = ?", 
                              (row['liczba'], row['cena'], row['id']))
            st.success("Zaktualizowano dane!")

    with tab3:
        st.subheader("Usuwanie rekordów")
        del_target = st.radio("Co chcesz usunąć?", ["Produkt", "Kategorię (usunie też przypisane produkty!)"])
        
        if "Produkt" in del_target:
            p_list = get_data("SELECT id, nazwa FROM produkty")
            to_del = st.selectbox("Wybierz produkt", p_list['nazwa'].tolist())
            if st.button("Usuń Produkt"):
                execute_query("DELETE FROM produkty WHERE nazwa = ?", (to_del,))
                st.rerun()
        else:
            k_list = get_data("SELECT id, nazwa FROM kategorie")
            to_del_k = st.selectbox("Wybierz kategorię", k_list['nazwa'].tolist())
            if st.button("Usuń Kategorię"):
                execute_query("DELETE FROM kategorie WHERE nazwa = ?", (to_del_k,))
                st.rerun()
