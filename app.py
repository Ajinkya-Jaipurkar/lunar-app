import streamlit as st
from skyfield.api import load, wgs84
from pytz import timezone
from astral import LocationInfo
from astral.sun import sun
import datetime
import pytz

# --- PASSWORD PROTECTION ---
def check_password():
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.text_input("Enter App Password", type="password", key="password", on_change=password_entered)
    if "password" in st.session_state and st.session_state["password"] == "my_secret_moon_app":
        st.session_state["password_correct"] = True
        st.rerun() # Reloads the app to show the content
    elif "password" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def password_entered():
    """Checks whether a password entered by the user is correct."""
    if st.session_state.get("password") == "my_secret_moon_app":
        st.session_state["password_correct"] = True
        del st.session_state["password"] # Don't store the password
    else:
        st.session_state["password_correct"] = False

if not check_password():
    st.stop() # This stops the app from loading anything below this line

# ---------------------------------
# (The rest of your previous code goes below this line)
# You can change "my_secret_moon_app" to any password you want.
# --- Vedic Astrology Constants ---
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Your specific personalized data
USER_MOON_NAKSHATRA = "Bharani"
USER_ASC_NAKSHATRA = "Rohini"

# Calculate Auspicious Nakshatras from Janma Nakshatra (Bharani)
janma_idx = NAKSHATRAS.index(USER_MOON_NAKSHATRA)
auspicious_indices = [
    (janma_idx + 1) % 27,  # 2nd
    (janma_idx + 3) % 27,  # 4th (Rohini)
    (janma_idx + 5) % 27,  # 6th
    (janma_idx + 7) % 27,  # 8th
    (janma_idx + 8) % 27  # 9th
]
AUSPICIOUS_NAKS = [NAKSHATRAS[i] for i in auspicious_indices]


# --- Astronomical & Astrological Functions ---
def get_moon_nakshatra(date_obj):
    # Load ephemeris
    ts = load.timescale()
    eph = load('de421.bsp')
    earth = eph['earth']
    moon = eph['moon']

    # Convert date to UTC for calculation
    utc_dt = date_obj.astimezone(pytz.utc)
    t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second)

    # Get moon's ecliptic longitude relative to Earth
    astrometric = earth.at(t).observe(moon)
    ecliptic_lat, ecliptic_lon, _ = astrometric.ecliptic_latlon()

    # Vedic Astrology uses the Fixed Sidereal Zodiac (Lahiri Ayanamsa approx 24.2 degrees currently)
    # We offset the tropical longitude by ~24.2 degrees
    sidereal_lon = (ecliptic_lon.degrees - 24.2) % 360

    # Each Nakshatra is 13.333 degrees (360/27)
    nak_index = int(sidereal_lon // (360 / 27))
    # Each Pada is 3.333 degrees
    pada = int((sidereal_lon % (360 / 27)) // (360 / 108)) + 1

    return NAKSHATRAS[nak_index], pada


def get_yogic_times(date_obj, lat, lon, tz_str):
    tz = timezone(tz_str)
    location = LocationInfo("UserLoc", "Region", tz_str, lat, lon)
    s = sun(location.observer, date=date_obj, tzinfo=location.timezone)

    sunrise = s['sunrise']
    sunset = s['sunset']

    # 1. Brahma Muhurta (approx 1 hour and 36 minutes before sunrise)
    brahma_start = sunrise - datetime.timedelta(minutes=96)
    brahma_end = sunrise - datetime.timedelta(minutes=48)

    # 2. Abhijit Muhurta (Midday - 24 mins around solar noon)
    solar_noon = sunrise + (sunset - sunrise) / 2
    abhijit_start = solar_noon - datetime.timedelta(minutes=12)
    abhijit_end = solar_noon + datetime.timedelta(minutes=12)

    # 3. Rahu Kalam (9th part of daytime, generally avoided)
    day_duration = sunset - sunrise
    rahu_start = sunrise + day_duration * (8 / 9)
    rahu_end = sunrise + day_duration * (9 / 9)  # Sunset

    return {
        "Brahma Muhurta (Best for Yoga/Meditation)": f"{brahma_start.strftime('%I:%M %p')} - {brahma_end.strftime('%I:%M %p')}",
        "Abhijit Muhurta (Universal Auspicious Time)": f"{abhijit_start.strftime('%I:%M %p')} - {abhijit_end.strftime('%I:%M %p')}",
        "Rahu Kalam (AVOID for new ventures)": f"{rahu_start.strftime('%I:%M %p')} - {rahu_end.strftime('%I:%M %p')}"
    }


# --- Streamlit User Interface ---
st.set_page_config(page_title="My Lunar Yogic App", page_icon="🌙")

st.title("🌙 Personal Lunar & Yogic Tracker")
st.markdown(f"**User Profile:** Ascendant: Rohini (Pada 1) | Moon: Bharani (Pada 1)")

# Location and Date Inputs
st.sidebar.header("Settings")
lat = st.sidebar.number_input("Latitude", value=13.0827)  # Default Chennai
lon = st.sidebar.number_input("Longitude", value=80.2707)
tz_str = st.sidebar.selectbox("Timezone", ["Asia/Kolkata", "America/New_York", "Europe/London", "Australia/Sydney"])
date_input = st.sidebar.date_input("Select Date", datetime.date.today())
time_input = st.sidebar.time_input("Select Time", datetime.datetime.now().time())

# Combine date and time
local_tz = timezone(tz_str)
selected_datetime = local_tz.localize(datetime.datetime.combine(date_input, time_input))

# Calculate current Moon Nakshatra
current_nak, current_pada = get_moon_nakshatra(selected_datetime)

st.header("📊 Current Moon Position")
st.metric(label="Current Nakshatra", value=current_nak)
st.metric(label="Current Pada", value=f"Pada {current_pada}")

# Check Auspiciousness
st.header("✨ Personal Auspiciousness Check")
if current_nak in AUSPICIOUS_NAKS:
    st.success(
        f"**AUSPICIOUS FOR YOU!** The Moon is currently in {current_nak} (Pada {current_pada}). This is a highly supportive time for your endeavors.")
    if current_nak == USER_ASC_NAKSHATRA:
        st.balloons()
        st.info(
            "🌟 **SUPER ALIGNED!** Moon is in Rohini, your Ascendant Nakshatra. The 4th from your Moon. This is a peak day for physical health, real estate, and inner peace. Best day of the month for deep Yoga!")
else:
    st.warning(
        f"The Moon is in {current_nak}. This is a neutral day for you. Focus on routine tasks and spiritual grounding.")

st.header("🧘‍♂️ Specific Yogic Times (Muhurtas)")
yogic_times = get_yogic_times(selected_datetime, lat, lon, tz_str)
for name, time_range in yogic_times.items():
    st.write(f"**{name}:**")
    st.code(time_range)
    if "AVOID" in name:
        st.caption(
            "Rahu Kalam is traditionally inauspicious for starting new things, but fine for continuing routine or spiritual practices.")