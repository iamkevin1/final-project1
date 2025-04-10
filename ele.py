# electricity_analyzer_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from PIL import Image

# Initialize storage
DATA_FILE = 'electricity_readings.csv'
APPLIANCES_FILE = 'appliances.csv'
os.makedirs('uploads', exist_ok=True)

# Initialize CSV files if not exist
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["timestamp", "reading", "image_path"]).to_csv(DATA_FILE, index=False)

if not os.path.exists(APPLIANCES_FILE):
    pd.DataFrame(columns=["name", "power_kw", "hours_per_day"]).to_csv(APPLIANCES_FILE, index=False)

# Load data
def load_data():
    return pd.read_csv(DATA_FILE, parse_dates=["timestamp"])

def load_appliances():
    return pd.read_csv(APPLIANCES_FILE)

# Save data
def save_reading(timestamp, reading, image):
    filename = f"uploads/{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
    image.save(filename)
    new_data = pd.DataFrame([[timestamp, reading, filename]], columns=["timestamp", "reading", "image_path"])
    df = pd.read_csv(DATA_FILE)
    df = pd.concat([df, new_data])
    df.to_csv(DATA_FILE, index=False)

# Save appliance data
def save_appliance(name, power_kw, hours):
    df = pd.read_csv(APPLIANCES_FILE)
    new_appliance = pd.DataFrame([[name, power_kw, hours]], columns=["name", "power_kw", "hours_per_day"])
    df = pd.concat([df, new_appliance])
    df.to_csv(APPLIANCES_FILE, index=False)

# Main app
st.title("⚡ Electricity Reading and Analyzer")

menu = st.sidebar.radio("Select an option", [
    "1. Upload Reading",
    "2. View All Readings",
    "3. Analyze Usage",
    "4. Appliance Estimator"
])

# Upload Reading
if menu.startswith("1"):
    st.header("📤 Upload Electricity Reading")
    image = st.file_uploader("Upload meter image")
    reading = st.number_input("Enter reading (in kWh)", min_value=0.0, format="%.1f")
    timestamp = st.datetime_input("Time of reading", datetime.now())
    if st.button("Save Reading") and image:
        img = Image.open(image)
        save_reading(timestamp, reading, img)
        st.success("Reading saved successfully!")

# View All Readings
elif menu.startswith("2"):
    st.header("📄 All Readings")
    df = load_data().sort_values("timestamp")
    st.dataframe(df)

# Analyze Usage
elif menu.startswith("3"):
    st.header("📊 Analyze Usage")
    df = load_data().sort_values("timestamp")
    if len(df) >= 2:
        df["usage"] = df["reading"].diff()
        df = df.dropna()
        df.set_index("timestamp", inplace=True)
        time_unit = st.selectbox("View by", ["D", "W", "M", "Y"], format_func=lambda x: {"D": "Daily", "W": "Weekly", "M": "Monthly", "Y": "Yearly"}[x])
        grouped = df["usage"].resample(time_unit).sum()
        fig = px.line(grouped, labels={'value': 'kWh'}, title="Electricity Usage")
        st.plotly_chart(fig)
    else:
        st.warning("Not enough data to analyze. Add more readings.")

# Appliance Estimator
elif menu.startswith("4"):
    st.header("🔌 Appliance Usage Estimator")
    with st.form("Add Appliance"):
        name = st.text_input("Appliance Name")
        power_kw = st.number_input("Power Rating (kW)", min_value=0.0, format="%.2f")
        hours = st.number_input("Usage per day (hours)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Appliance")
        if submitted:
            save_appliance(name, power_kw, hours)
            st.success("Appliance added!")

    df = load_appliances()
    if not df.empty:
        df["daily_kwh"] = df["power_kw"] * df["hours_per_day"]
        total = df["daily_kwh"].sum()
        st.write("### Appliance Usage Table")
        st.dataframe(df)
        st.metric("Estimated Daily Usage", f"{total:.2f} kWh")
    else:
        st.info("No appliances added yet.")
