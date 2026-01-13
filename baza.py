import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Konfiguracja strony
st.set_page_config(page_title="System Magazynowy Pro", layout="wide", page_icon="📦")

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

# --- MENU BOCZNE ---
st.sidebar.title("📦 Nawigacja")
menu = ["📊 Dashboard", "🔎 Przegląd i Edycja", "📂 Kategorie", "⚙️ Administracja"]
choice = st.sidebar.radio("Przejdź do:", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📊 Analityka Magazynu")
    
    df = get_data('''SELECT p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
                     FROM produkty p JOIN kategorie k ON p.kategoria_id = k.id''')
    
    if not df.empty:
        df['Wartość'] = df['liczba'] * df['cena']
        
        # Metryki u góry
        m1, m2, m3 = st.columns(3)
        m1.metric("Wszystkie produkty (szt.)", int(df['liczba'].sum()))
        m2.metric("Łączna wartość", f"{df['Wartość'].sum():,.2f} zł")
        m3.metric("Liczba kategorii", df['kategoria'].nunique())

        # Wykresy
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df, values='liczba', names='kategoria', title="Struktura zapasów wg kategorii", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.bar(df, x='nazwa', y='Wartość', color='kategoria', title="Wartość finansowa produktów")
            st.plotly_chart(fig_bar, use_container_width=True)

        # Powiadomienia o niskim stanie
        low_stock = df[df['liczba'] < 5]
        if not low_stock.empty:
            st.warning("⚠️ **Uwaga: Niski stan magazynowy!**")
            st.write(low_stock[['nazwa', 'liczba']])
    else:
        st.info("Dodaj pierwsze dane, aby zobaczyć statystyki.")

# --- 2. PRZEGLĄD I EDYCJA ---
elif choice == "🔎 Przegląd i Edycja":
    st.title("🔎 Przegląd i Szybka Edycja")
    st.write("Możesz edytować stany i ceny bezpośrednio w tabeli.")
    
    df_edit = get_data('''SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
                          FROM produkty p LEFT JOIN kategorie k ON p.kategoria_id = k.id''')
    
    # Wykorzystanie st.data_editor do masowej edycji
    edited_df = st.data_editor(df_edit, key="editor", hide_index=True, use_container_width=True)
    
    if st.button("💾 Zapisz zmiany w bazie"):
        for index, row in edited_df.iterrows():
            execute_query("UPDATE produkty SET liczba = ?, cena = ? WHERE id = ?", 
                          (row['liczba'], row['cena'], row['id']))
        st.success("Dane zostały zaktualizowane!")
        st.rerun()

# --- 3. KATEGORIE ---
elif choice == "📂 Kategorie":
    st.title("📂 Zarządzanie Kategoriami")
    df_kat = get_data("SELECT id, nazwa, opis FROM kategorie")
    st.dataframe(df_kat, use_container_width=True, hide_index=True)

# --- 4. ADMINISTRACJA ---
elif choice == "⚙️ Administracja":
    st.title("⚙️ Dodawanie i Usuwanie")
    
    tab1, tab2 = st.tabs(["➕ Dodaj Nowe", "🗑️ Usuń Dane"])
    
    with tab1:
        col_p, col_k = st.columns(2)
        with col_p:
            st.subheader("Nowy Produkt")
            with st.form("add_p"):
                p_name = st.text_input("Nazwa produktu")
                p_qty = st.number_input("Ilość", min_value=0)
                p_price = st.number_input("Cena (zł)", min_value=0.0)
                kat_list = get_data("SELECT id, nazwa FROM kategorie")
                p_kat = st.selectbox("Kategoria", options=kat_list['nazwa'].tolist()) if not kat_list.empty else None
                
                if st.form_submit_button("Dodaj Produkt"):
                    if p_kat:
                        k_id = kat_list[kat_list['nazwa'] == p_kat]['id'].values[0]
                        execute_query("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?,?,?,?)",
                                      (p_name, p_qty, p_price, int(k_id)))
                        st.success("Produkt dodany!")
                    else:
                        st.error("Najpierw utwórz kategorię!")

        with col_k:
            st.subheader("Nowa Kategoria")
            with st.form("add_k"):
                k_name = st.text_input("Nazwa kategorii")
                k_desc = st.text_area("Opis")
                if st.form_submit_button("Dodaj Kategorię"):
                    execute_query("INSERT INTO kategorie (nazwa, opis) VALUES (?,?)", (k_name, k_desc))
                    st.success("Kategoria dodana!")
                    st.rerun()

    with tab2:
        st.subheader("Usuwanie rekordów")
        p_list = get_data("SELECT id, nazwa FROM produkty")
        to_del = st.selectbox("Wybierz produkt do usunięcia", p_list['nazwa'].tolist())
        if st.button("Usuń wybrany produkt"):
            execute_query("DELETE FROM produkty WHERE nazwa = ?", (to_del,))
            st.success("Usunięto!")
            st.rerun()
