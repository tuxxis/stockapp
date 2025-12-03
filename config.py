import os
import json

# --- Import Streamlit conditionally to prevent crashes on local runs ---
try:
    import streamlit as st
except ImportError:
    st = None

# 1. GUARANTEE VARIABLE EXISTENCE (Anti-Crash Measure)
# Define variables first so 'brain.py' doesn't crash on import if loading fails.
GOOGLE_CREDENTIALS_PATH = None
OPENAI_KEY = None
APP_PASSWORD = None


# 2. SETUP: Load Environment (Cloud vs Local)
try:
    # --- CLOUD MODE (Streamlit) ---
    if st and "GOOGLE_CREDENTIALS_JSON" in st.secrets:
        # 1. Get the raw text from secrets
        raw_json = st.secrets["GOOGLE_CREDENTIALS_JSON"]
        
        # 2. Parse the JSON string
        creds_dict = json.loads(raw_json)
        
        # 3. Write it to cred.json so brain.py can find it
        with open("cred.json", "w") as f:
            json.dump(creds_dict, f)
        
        GOOGLE_CREDENTIALS_PATH = "cred.json"
        OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
        APP_PASSWORD = st.secrets["APP_PASSWORD"]
        
    # --- LOCAL MODE (Laptop/VPS) ---
    else:
        # Only import dotenv locally
        from dotenv import load_dotenv
        load_dotenv()
        
        GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "cred.json")
        OPENAI_KEY = os.getenv("OPENAI_API_KEY")
        APP_PASSWORD = os.getenv("APP_PASSWORD")

except Exception as e:
    # This catches errors like ImportErrors or FileNotFoundError
    # The program continues, but variables remain None, which is fine for the crash prevention
    pass

# Ensure variables have default values if they're still None
if GOOGLE_CREDENTIALS_PATH is None:
    GOOGLE_CREDENTIALS_PATH = "cred.json"
if APP_PASSWORD is None:
    APP_PASSWORD = "Tryitout0-0"  # Default fallback password


# 3. CONSTANTS
MANUFACTURERS_FILE = "cleaned_manufacturers.txt"

# 4. SHEET LOCATIONS
SHEET_LOCATIONS = {
    "Test": "1vcHtQK2Uy7_Gan8sntTgS5axJofceMn6V02Ks_iKww4",
    # Add your real rooms here later
}