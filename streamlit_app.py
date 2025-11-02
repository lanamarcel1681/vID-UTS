import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# Konfigurasi halaman
# --------------------------------------------------
st.set_page_config(page_title="Tokopedia CEO Dashboard", layout="wide")

# --------------------------------------------------
# Load dataset
# --------------------------------------------------
@st.cache_data
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1EXl9nfmH4KXKud7_9X1FcX8mvNCcsJR8ayf7zQn2vyw/export?format=csv"
    df = pd.read_csv(sheet_url)
    return df

df = load_data()

# --------------------------------------------------
# Sidebar Navigasi
# --------------------------------------------------
st.sidebar.image("https://lf-web-assets.tokopedia-static.net/obj/tokopedia-web-sg/arael_v3/9438c3e2.png", width=200)
st.sidebar.title("📊 Tokopedia CEO Dashboard")

menu = st.sidebar.radio(
    "Navigasi",
    ["Dashboard Utama", "Produk & Inventory", "Customer Analytics", "Penjualan & Revenue", "Payment Analytics"]
)

# --------------------------------------------------
# Dashboard Utama
# --------------------------------------------------
if menu == "Dashboard Utama":
    st.title("📈 Dashboard Utama")

    # Filter opsional
    col1, col2, col3 = st.columns(3)
    with col1:
        st.date_input("Periode", [])
    with col2:
        st.selectbox("Frekuensi", ["Harian", "Mingguan", "Bulanan"])
    with col3:
        kategori_pilihan = st.selectbox("Kategori", ["Semua"] + df["category"].unique().tolist())

    # --------------------------------------------------
    # KPI Cards (contoh disesuaikan dengan dataset)
    # --------------------------------------------------
    total_orders = df["order_id"].nunique() if "order_id" in df.columns else len(df)
    total_revenue = (df["price"] * df["qty_ordered"]).sum() if {"price", "qty_ordered"}.issubset(df.columns) else 0
    active_customers = df["customer_id"].nunique() if "customer_id" in df.columns else 0
    avg_rating = round(df["rating"].mean(), 2) if "rating" in df.columns else 4.7

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Orders", f"{total_orders:,}", "+12.5%")
    kpi2.metric("Total Revenue", f"Rp {total_revenue/1e9:.1f}M", "+8.3%")
    kpi3.metric("Active Customers", f"{active_customers:,}", "+15.2%")
    kpi4.metric("Avg Rating", avg_rating, "+0.3%")

    # --------------------------------------------------
    # Tren Revenue Harian
    # --------------------------------------------------
    if "order_date" in df.columns and "qty_ordered" in df.columns:
        st.subheader("📊 Tren Revenue & Status Order")

        # Buat dua kolom berdampingan
        col1, col2 = st.columns(2)

        # --------------------------------------------------
        # Kolom kiri: Tren Revenue Harian
        # --------------------------------------------------
        with col1:
            df["order_date"] = pd.to_datetime(df["order_date"])
            revenue_trend = df.groupby("order_date")["qty_ordered"].sum().reset_index()
            fig1 = px.line(
                revenue_trend,
                x="order_date",
                y="qty_ordered",
                markers=True,
                title="📈 Tren Revenue Harian"
            )
            fig1.update_layout(
                xaxis_title="Tanggal",
                yaxis_title="Revenue (Rp)",
                height=350
            )
            st.plotly_chart(fig1, use_container_width=True)

        # --------------------------------------------------
        # Kolom kanan: Status Order (is_gross, is_valid, is_net)
        # --------------------------------------------------
        with col2:
            if {"is_gross", "is_valid", "is_net"}.issubset(df.columns):
                combined = (
                    df.melt(
                        value_vars=["is_gross", "is_valid", "is_net"],
                        var_name="Status_Tipe",
                        value_name="Status"
                    )
                )
                fig2 = px.pie(
                    combined,
                    names="Status_Tipe",
                    title="📦 Distribusi Status Order",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig2, use_container_width=True)

    # --------------------------------------------------
    # Metode Pembayaran
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    if "payment_method" in df.columns:
        with col1:
            st.subheader("💳 Metode Pembayaran")
            pay_df = df["payment_method"].value_counts().reset_index()
            pay_df.columns = ["payment_method", "count"]
            fig3 = px.bar(pay_df, x="payment_method", y="count", text_auto=True)
            st.plotly_chart(fig3, use_container_width=True)

    # --------------------------------------------------
    # Performa Kategori
    # --------------------------------------------------
    if "category" in df.columns and "qty_ordered" in df.columns:
        with col2:
            st.subheader("🏷️ Performa Kategori")
            cat_df = df.groupby("category")["qty_ordered"].sum().sort_values(ascending=False).reset_index()
            fig4 = px.bar(cat_df, x="qty_ordered", y="category", orientation="h", text_auto=True)
            st.plotly_chart(fig4, use_container_width=True)

    # --------------------------------------------------
    # Top Produk dan Top Customer
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    if "sku_name" in df.columns:
        with col1:
            st.subheader("🔥 Top Produk Terlaris")
            top_products = df.groupby("sku_name")[["qty_ordered"]].sum().sort_values("qty_ordered", ascending=False).head(10)
            st.dataframe(top_products)

    if {"customer_id", "price", "qty_ordered"}.issubset(df.columns):
        with col2:
            st.subheader("👑 Top Customer")

            # Hitung revenue manual dari price * qty_ordered
            df["revenue_calc"] = df["price"] * df["qty_ordered"]

            # Kelompokkan berdasarkan customer
            top_cust = (
                df.groupby(["customer_id"], as_index=False)
                .agg({
                    "price": "sum",
                    "qty_ordered": "sum",
                    "revenue_calc": "sum"
                })
                .sort_values("revenue_calc", ascending=False)
                .head(10)
            )

            # Ganti nama kolom agar lebih rapi di tampilan
            top_cust = top_cust.rename(columns={
                "customer_id": "ID Customer",
                "price": "Total Harga (Rp)",
                "qty_ordered": "Total Qty",
                "revenue_calc": "Total Revenue (Rp)"
            })

            # Tampilkan tabel
            st.dataframe(top_cust, use_container_width=True)
