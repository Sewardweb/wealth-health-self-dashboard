import os
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data.csv"

# Title
st.title("WEALTH • HEALTH • SELF Dashboard")

# --- Entry Form (only one st.form block) ---
categories = ["Work", "Personal", "Health goal", "Finance", "Other"]
with st.form("entry"):
    decision = st.text_input("What decision are you logging?")
    category = st.selectbox("Category", categories)
    w = st.slider("Wealth (-100 to 100)", -100, 100, 0)
    h = st.slider("Health (-100 to 100)", -100, 100, 0)
    s = st.slider("Self (-100 to 100)", -100, 100, 0)
    submit = st.form_submit_button("Log Decision")

if submit:
    # Warn for negative or zero impact
    negative = [
        name
        for name, val in [("Wealth", w), ("Health", h), ("Self", s)]
        if val < 0
    ]
    zero = [
        name
        for name, val in [("Wealth", w), ("Health", h), ("Self", s)]
        if val == 0
    ]
    if negative:
        st.error(f"Negative impact on: {', '.join(negative)}")
    elif zero:
        st.warning(f"No benefit to: {', '.join(zero)}")

    # Append new entry to CSV
    df_new = pd.DataFrame([{
        "Decision": decision,
        "Category": category,
        "Wealth": w,
        "Health": h,
        "Self": s,
        "Time": pd.Timestamp.now()
    }])
    df_new.to_csv(
        DATA_PATH,
        mode="a",
        index=False,
        header=not DATA_PATH.exists()
    )
    st.success("Decision logged!")

# --- Load history ---
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    df = pd.DataFrame(columns=[
        "Decision", "Category", "Wealth", "Health", "Self", "Time"
    ])

# Ensure Category exists (for older CSVs)
if "Category" not in df.columns:
    df["Category"] = "Uncategorized"

# Parse timestamps if any rows exist
if not df.empty:
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

# --- Automated Summary ---
if not df.empty:
    today = pd.Timestamp.now().normalize()
    df_today = df[df["Time"].dt.normalize() == today]
    decisions_today = len(df_today)
    avg_wealth = df["Wealth"].mean()
    avg_neg_flags = df.apply(
        lambda r: sum(val < 0 for val in [r.Wealth, r.Health, r.Self]),
        axis=1
    ).mean()
else:
    decisions_today = 0
    avg_wealth = 0
    avg_neg_flags = 0

st.subheader("📊 Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Decisions Today", decisions_today)
c2.metric("Avg Wealth Impact", f"{avg_wealth:.1f}")
c3.metric("Avg Negative Flags", f"{avg_neg_flags:.2f}")

# --- Normalize for ternary (shift negatives into positives) ---
df["w2"] = df["Wealth"] + 100
df["h2"] = df["Health"] + 100
df["s2"] = df["Self"] + 100

# --- Filter by user choice ---
sel = st.multiselect(
    "Which decisions?",
    df["Decision"].unique().tolist(),
    default=df["Decision"].unique().tolist()
)
df2 = df[df["Decision"].isin(sel)]

# --- Plots ---
if not df2.empty:
    # Ternary plot with category color
    fig = px.scatter_ternary(
        df2,
        a="w2", b="h2", c="s2",
        color="Category",
        hover_name="Decision",
        hover_data=["Wealth", "Health", "Self", "Time"],
        size_max=12
    )
    st.plotly_chart(fig, use_container_width=True)

    # Bar chart of last-selected decision
    last = df2.iloc[-1]
    melt = last[["Wealth", "Health", "Self"]].reset_index()
    melt.columns = ["Sector", "Impact"]
    fig2 = px.bar(
        melt,
        x="Sector",
        y="Impact",
        title=f"Raw impact for: {last['Decision']} ({last['Category']})"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Overall impact across all filtered decisions
    totals = df2[["Wealth", "Health", "Self"]].sum()
    melt_totals = totals.reset_index()
    melt_totals.columns = ["Sector", "Total Impact"]
    fig3 = px.bar(
        melt_totals,
        x="Sector",
        y="Total Impact",
        title="Overall Impact for Selected Decisions"
    )
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("No decisions to show.")