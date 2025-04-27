import streamlit as st
import pandas as pd
import requests
import time

# --- CONFIGURE YOUR THINGSPEAK CHANNEL ---
THINGSPEAK_CHANNEL_ID = '2737844'   # <-- replace
THINGSPEAK_API_KEY = 'NZPFRLVTR72J95E1'     # <-- replace
THINGSPEAK_FIELD = 1                         # Field you want to track
SAFE_THRESHOLD = 50                          # Set your threshold for alerting

# --- FUNCTION TO FETCH DATA FROM THINGSPEAK ---
def fetch_thingspeak_data(channel_id, api_key, field):
    url = f"https://api.thingspeak.com/channels/{channel_id}/fields/{field}.json?api_key={api_key}&results=20"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        feeds = data['feeds']
        timestamps = [feed['created_at'] for feed in feeds]
        values = [feed[f'field{field}'] for feed in feeds]
        df = pd.DataFrame({'Timestamp': timestamps, 'Value': values})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df.dropna(inplace=True)
        return df
    else:
        st.error("Failed to fetch data from ThingSpeak.")
        return pd.DataFrame()

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="🌟 Real-Time ThingSpeak Dashboard", layout="wide")

st.title("🌟 ThingSpeak Real-Time Monitoring Dashboard")
st.caption("Monitoring live data from your IoT device via ThingSpeak")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Settings ⚙️")
    refresh_interval = st.slider('Auto-refresh every (seconds)', min_value=5, max_value=60, value=10, step=5)
    auto_refresh = st.checkbox("Enable Auto Refresh", value=True)
    alert_threshold = st.number_input('Alert if value exceeds:', value=SAFE_THRESHOLD)
    st.markdown("---")
    download_btn = st.button("📥 Download Data as CSV")

# --- PLACEHOLDERS ---
chart_placeholder = st.empty()
table_placeholder = st.empty()
alert_placeholder = st.empty()

# --- MAIN LOOP ---
def main_loop():
    df = fetch_thingspeak_data(THINGSPEAK_CHANNEL_ID, THINGSPEAK_API_KEY, THINGSPEAK_FIELD)

    if not df.empty:
        # --- Display real-time line chart ---
        with chart_placeholder.container():
            st.subheader("📈 Live Sensor Data")
            st.line_chart(df.set_index('Timestamp')['Value'])

        # --- Display table ---
        with table_placeholder.container():
            st.subheader("📄 Recent Readings")
            st.dataframe(df)

        # --- Check for alerts ---
        latest_value = df['Value'].iloc[-1]
        if latest_value > alert_threshold:
            alert_placeholder.warning(f"⚠️ ALERT: Sensor value ({latest_value:.2f}) exceeds threshold ({alert_threshold})!")
        else:
            alert_placeholder.success(f"✅ Sensor value ({latest_value:.2f}) is within safe range.")

        # --- Download Button ---
        if download_btn:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name='thingspeak_data.csv',
                mime='text/csv',
            )
    else:
        st.error("No data to display.")

# --- RUN APP ---
if auto_refresh:
    while True:
        main_loop()
        time.sleep(refresh_interval)
        st.experimental_rerun()
else:
    if st.button("🔄 Refresh Now"):
        main_loop()
