import streamlit as st
import pandas as pd
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="Astro Soul",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Lato', sans-serif;
    }
    .stApp {
        background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);
        color: #e0e0e0;
    }
    div.stExpander {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 10px;
    }
    h1, h2, h3 {
        font-family: 'Cinzel', serif !important;
        color: #f8c291 !important;
        text-shadow: 0px 0px 10px rgba(248, 194, 145, 0.3);
        text-align: center;
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 12, 41, 0.95);
    }
    .stButton>button {
        background: linear-gradient(90deg, #d53369 0%, #daae51 100%);
        color: white;
        border: none;
        border-radius: 25px;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
        width: 100%;
        text-transform: uppercase;
        font-family: 'Cinzel', serif;
        margin-top: 20px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

@st.cache_data
def load_data():
    try:
        s = pd.read_csv('signs.csv', index_col=0)
        h = pd.read_csv('houses.csv', index_col=0)
        s.columns = s.columns.str.strip()
        s.index = s.index.str.strip()
        h.columns = h.columns.str.strip()
        h.index = pd.to_numeric(h.index, errors='coerce')
        return s, h
    except Exception as e:
        return None, None

def format_rounded_up(float_degrees):
    return f"{math.ceil(float_degrees)}°"

def get_house_of_planet(planet_lon, houses_list):
    house_ids = [const.HOUSE1, const.HOUSE2, const.HOUSE3, const.HOUSE4,
                 const.HOUSE5, const.HOUSE6, const.HOUSE7, const.HOUSE8,
                 const.HOUSE9, const.HOUSE10, const.HOUSE11, const.HOUSE12]
    for i in range(12):
        cusp_start = houses_list.get(house_ids[i]).lon
        next_idx = (i + 1) % 12
        cusp_end = houses_list.get(house_ids[next_idx]).lon
        
        if cusp_end < cusp_start: 
            if planet_lon >= cusp_start or planet_lon < cusp_end: return i + 1
        else:
            if cusp_start <= planet_lon < cusp_end: return i + 1
    return 1

def get_text_from_excel(df, row_name, col_name):
    try:
        if df is None or df.empty: return "Data missing."
        text = df.loc[row_name, col_name]
        if isinstance(text, pd.Series): text = text.iloc[0]
        text_str = str(text)
        if "]" in text_str:
            return text_str.split(']')[-1].strip()
        return text_str
    except:
        return "Interpretation not found."

def draw_chart_visual(chart_obj):
    fig = plt.figure(figsize=(10, 10), facecolor='none') 
    ax = fig.add_subplot(111, projection='polar')
    ax.set_facecolor('none')
    
    ZODIAC_SYMBOLS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
    sectors = np.linspace(0, 2 * np.pi, 13)
    
    # Draw Zodiac Ring
    for i in range(12):
        # Using a named color 'white' with alpha is safer
        ax.fill_between(np.linspace(sectors[i], sectors[i+1], 20), 0.9, 1.0, color='white', alpha=0.05)
        angle_mid = (sectors[i] + sectors[i+1]) / 2
        ax.text(angle_mid, 1.05, ZODIAC_SYMBOLS[i], size=16, color='#f8c291',
                horizontalalignment='center', verticalalignment='center')

    # Draw House Lines (The Fix is Here)
    house_ids = [const.HOUSE1, const.HOUSE2, const.HOUSE3, const.HOUSE4,
                 const.HOUSE5, const.HOUSE6, const.HOUSE7, const.HOUSE8,
                 const.HOUSE9, const.HOUSE10, const.HOUSE11, const.HOUSE12]
    
    houses_list = chart_obj.houses
    for i in range(12):
        cusp = houses_list.get(house_ids[i])
        rads = np.deg2rad(cusp.lon)
        
        # Fixed Color Format: (R, G, B, Alpha) using floats 0-1
        ax.plot([rads, rads], [0, 0.9], color=(1, 1, 1, 0.3), linestyle='--', linewidth=1)
        ax.text(rads, 0.4, str(i+1), size=10, color=(1, 1, 1, 0.5), ha='center', va='center')

    # Draw Planets
    planet_symbols = {
        'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
        'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
        'North Node': '☊'
    }
    
    calc_ids = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
                const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO, const.NORTH_NODE]
    
    for pid in calc_ids:
        obj = chart_obj.get(pid)
        rads = np.deg2rad(obj.lon)
        ax.plot(rads, 0.75, 'o', markersize=9, color='#f8c291', markeredgecolor='none', alpha=0.9)
        symbol = planet_symbols.get(obj.id, obj.id[0])
        ax.text(rads, 0.82, symbol, size=14, color='white', ha='center')

    ax.set_ylim(0, 1.1)
    ax.set_yticks([])
    ax.set_xticks(sectors[:-1])
    ax.set_xticklabels([])
    ax.grid(False)
    ax.spines['polar'].set_visible(False)
    
    return fig

# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center'>Birth Details</h2>", unsafe_allow_html=True)
    with st.form("input_form"):
        name = st.text_input("Full Name", "")
        city = st.text_input("City of Birth", "Calgary")
        birth_date = st.date_input("Date of Birth", datetime.date(1995, 3, 9))
        birth_time = st.time_input("Time of Birth", datetime.time(17, 51))
        submitted = st.form_submit_button("Reveal Soul Map 🔮")

# --- Main Logic ---
df_signs, df_houses = load_data()

if submitted:
    try:
        with st.spinner('Reading the stars...'):
            geolocator = Nominatim(user_agent="astro_soul_app_en")
            location = geolocator.geocode(city)
            if not location:
                st.error(f"City not found: {city}")
                st.stop()
            
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            local_tz = pytz.timezone(tz_str)
            dt_naive = datetime.datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M:%S")
            dt_aware = local_tz.localize(dt_naive)
            offset_seconds = dt_aware.utcoffset().total_seconds()
            flatlib_offset = f"{'+' if offset_seconds>=0 else '-'}{abs(int(offset_seconds/3600)):02d}:{int((abs(offset_seconds/3600)%1)*60):02d}"
            
            geo_pos = GeoPos(location.latitude, location.longitude)
            date = Datetime(f"{birth_date}".replace("-", "/"), f"{birth_time}", flatlib_offset)
            
            calc_ids = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
                        const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO, const.NORTH_NODE]
            
            chart = Chart(date, geo_pos, IDs=calc_ids)
            houses_list = chart.houses

        st.markdown(f"<h1>{name}'s Birth Chart</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; opacity: 0.7'>{city} | {birth_date.strftime('%B %d, %Y')} | {birth_time.strftime('%H:%M')}</p>", unsafe_allow_html=True)
        st.markdown("---")

        col_viz, col_space, col_text = st.columns([1, 0.1, 1.5])
        
        with col_viz:
            st.markdown("### Celestial Map")
            fig = draw_chart_visual(chart)
            st.pyplot(fig, use_container_width=True)
            
            asc = chart.get(const.ASC)
            st.info(f"🏹 **Rising Sign (ASC):** {asc.sign} at {format_rounded_up(asc.signlon)}")

        with col_text:
            st.markdown("### Planetary Positions")
            
            planet_mapping = {
                const.SUN: 'Sun / Earth', const.MOON: 'Moon', const.MERCURY: 'Mercury',
                const.VENUS: 'Venus', const.MARS: 'Mars', const.JUPITER: 'jupiter',
                const.SATURN: 'Saturn', const.URANUS: 'Uranus', const.NEPTUNE: 'Neptune',
                const.PLUTO: 'Pluto', const.NORTH_NODE: 'North Node'
            }
            
            for planet_id in calc_ids:
                obj = chart.get(planet_id)
                house_num = get_house_of_planet(obj.lon, houses_list)
                csv_col_name = planet_mapping.get(planet_id)
                
                sign_text = get_text_from_excel(df_signs, obj.sign, csv_col_name)
                house_text = get_text_from_excel(df_houses, house_num, csv_col_name)
                
                with st.expander(f"{obj.id} in {obj.sign} (House {house_num})  |  {format_rounded_up(obj.signlon)}"):
                    st.markdown(f"""
                    <div style='margin-bottom: 15px;'>
                        <strong style='color: #f8c291; font-size: 1.1em;'>In {obj.sign}:</strong><br>
                        <span style='opacity: 0.9'>{sign_text}</span>
                    </div>
                    <div>
                        <strong style='color: #f8c291; font-size: 1.1em;'>In House {house_num}:</strong><br>
                        <span style='opacity: 0.9'>{house_text}</span>
                    </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Calculation Error: {e}")

else:
    st.markdown("""
    <div style='text-align: center; margin-top: 50px; opacity: 0.6;'>
        <h2>Ready to explore your soul map?</h2>
        <p>Enter birth details on the sidebar to begin.</p>
    </div>
    """, unsafe_allow_html=True)
