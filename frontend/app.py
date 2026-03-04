import streamlit as st
import requests
from streamlit_geolocation import streamlit_geolocation

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Smart Parking", layout="wide")

st.title("🚗 AI Smart Parking Optimization System")

# 📍 Get user location

location = streamlit_geolocation()

if location and location["latitude"] is not None:
    lat = location["latitude"]
    lon = location["longitude"]
    st.success(f"📍 Live GPS Location: {lat}, {lon}")
else:
    st.warning("Location permission denied. Using default.")
    #lat, lon = 26.8872595, 81.0573365


# FETCH NEARBY PARKING (OSM)

if st.button("🔍 Find Nearby Parking"):
    try:
        res = requests.get(
            f"{BACKEND_URL}/nearby-parking",
            params={"lat": lat, "lon": lon}
        )
        res.raise_for_status()
        parkings = res.json()

        if parkings:
            st.subheader("🅿️ Nearby Parking Areas")
            st.table(parkings)
        else:
            st.info("No nearby parking found")

    except Exception as e:
        st.error(f"Error fetching parking: {e}")



st.divider()

# ----------------------------
# AI RECOMMENDATION
# ----------------------------

st.subheader("🤖 AI Parking Recommendation")

if st.button("Recommend Best Parking"):
    try:
        payload = {
            "lat": lat,
            "lon": lon
        }

        res = requests.post(f"{BACKEND_URL}/recommend",params={"lat": lat, "lon": lon})

        res.raise_for_status()
        data = res.json()

        parking = data["recommended_parking"]

        st.success("🚗 Recommended Parking Lot")

        st.write(f"**Name:** {parking['name']}")
        st.write(f"**Available Slots:** {parking['available_slots']}")
        st.write(f"**Total Slots:** {parking['total_slots']}")

        st.info(f"🧠 Reason: {data['reason']}")

    except Exception as e:
        st.error(str(e))
