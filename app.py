# =============================
# KARTU PERSEDIAAN - RETUR SESUAI AKUNTANSI + UNIT PRICE
# Metode : Moving Average (Average Perpetual)
# =============================

import streamlit as st
import pandas as pd
from datetime import date
import os
from io import BytesIO
import json

USER_FILE = "users.json"
DATA_FOLDER = "data_persediaan"

# ---------------- LOGIN SYSTEM ----------------

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)


def login_page():
    st.title("🔐 Login Kartu Persediaan")
    tab_login, tab_register = st.tabs(["Login", "Register"])
    users = load_users()

    with tab_login:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if email in users and users[email]["password"] == password:
                st.session_state["login"] = True
                st.session_state["user"] = email
                st.success("Login berhasil!")
                st.rerun()
            else:
                st.error("Email / Password salah")

    with tab_register:
        reg_email = st.text_input("Email Baru")
        reg_pass = st.text_input("Password Baru", type="password")
        if st.button("Register"):
            users[reg_email] = {"password": reg_pass}
            save_users(users)
            st.success("Akun berhasil dibuat")


# ---------------- APLIKASI UTAMA ----------------

def main_app():
    st.title("📦 Kartu Persediaan - Akuntansi")

    def load_data():
        data = {}
        saldo = {}
        if os.path.exists(DATA_FOLDER):
            for file in os.listdir(DATA_FOLDER):
                if file.endswith(".csv"):
                    nama = file.replace(".csv", "")
                    df = pd.read_csv(os.path.join(DATA_FOLDER, file))

                    if "Unit Price" not in df.columns:
                        df["Unit Price"] = df.apply(
                            lambda x: x["Saldo (Nilai)"] / x["Saldo (Qty)"] if x["Saldo (Qty)"] > 0 else 0,
                            axis=1
                        )

                    data[nama] = df
                    if len(df) > 0:
                        saldo[nama] = {
                            "qty": df.iloc[-1]["Saldo (Qty)"],
                            "nilai": df.iloc[-1]["Saldo (Nilai)"]
                        }
                    else:
                        saldo[nama] = {"qty": 0, "nilai": 0}
        return data, saldo

    def save_data():
        os.makedirs(DATA_FOLDER, exist_ok=True)
        for nama, df in st.session_state["persediaan"].items():
            df.to_csv(os.path.join(DATA_FOLDER, f"{nama}.csv"), index=False)

    if "persediaan" not in st.session_state:
        data, saldo = load_data()
        st.session_state["persediaan"] = data
        st.session_state["saldo"] = saldo

    nama_barang = st.sidebar.text_input("Nama Barang Baru")
    if st.sidebar.button("Tambah Barang") and nama_barang:
        st.session_state["persediaan"][nama_barang] = pd.DataFrame(columns=[
            "Tanggal", "Keterangan", "Masuk (Qty)", "Harga Beli",
            "Keluar (Qty)", "Harga Jual",
            "Unit Price", "Saldo (Qty)", "Saldo (Nilai)"
        ])
        st.session_state["saldo"][nama_barang] = {"qty": 0, "nilai": 0}

    pilihan_barang = st.sidebar.selectbox("Pilih Barang", list(st.session_state["persediaan"].keys()))

    st.subheader(f"Input Transaksi : {pilihan_barang}")
    jenis = st.selectbox("Jenis", ["Pembelian", "Penjualan", "Retur Pembelian", "Retur Penjualan"])
    tanggal = st.date_input("Tanggal", date.today())
    qty = st.number_input("Jumlah", min_value=0, step=1)
    harga = st.number_input("Harga per Unit", min_value=0.0, step=100.0)

    if st.button("Simpan"):
        df = st.session_state["persediaan"][pilihan_barang]
        saldo = st.session_state["saldo"][pilihan_barang]

        # hitung HPP rata-rata
        hpp = saldo["nilai"] / saldo["qty"] if saldo["qty"] > 0 else 0

        if jenis == "Pembelian":
            saldo["qty"] += qty
            saldo["nilai"] += qty * harga

        elif jenis == "Penjualan":
            saldo["qty"] -= qty
            saldo["nilai"] -= qty * hpp

        elif jenis == "Retur Pembelian":
            saldo["qty"] -= qty
            saldo["nilai"] -= qty * hpp

        elif jenis == "Retur Penjualan":
            saldo["qty"] += qty
            saldo["nilai"] += qty * hpp

        unit_price = saldo["nilai"] / saldo["qty"] if saldo["qty"] > 0 else 0

        new_row = {
            "Tanggal": tanggal,
            "Keterangan": jenis,
            "Masuk (Qty)": qty if jenis in ["Pembelian", "Retur Penjualan"] else 0,
            "Harga Beli": harga if jenis == "Pembelian" else 0,
            "Keluar (Qty)": qty if jenis in ["Penjualan", "Retur Pembelian"] else 0,
            "Harga Jual": harga if jenis == "Penjualan" else 0,
            "Unit Price": unit_price,
            "Saldo (Qty)": saldo["qty"],
            "Saldo (Nilai)": saldo["nilai"]
        }

        st.session_state["persediaan"][pilihan_barang] = pd.concat([
            df,
            pd.DataFrame([new_row])
        ], ignore_index=True)

        save_data()
        st.success("✅ Tersimpan")

    st.dataframe(st.session_state["persediaan"][pilihan_barang])


# ---------- RUN ----------
if "login" not in st.session_state:
    st.session_state["login"] = False

if st.session_state["login"]:
    main_app()
else:
    login_page()