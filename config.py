import os
import json
import streamlit as st

# 1. SETUP: Are we on the Cloud or Local?
try:
    # --- CLOUD MODE (Streamlit) ---
    if "GOOGLE_CREDENTIALS_JSON" in st.secrets:
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
        
    # --- LOCAL MODE (Laptop) ---
    else:
        # Only import dotenv locally
        from dotenv import load_dotenv
        load_dotenv()
        
        GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "cred.json")
        OPENAI_KEY = os.getenv("OPENAI_API_KEY")
        APP_PASSWORD = os.getenv("APP_PASSWORD")

except (FileNotFoundError, AttributeError, ImportError, json.JSONDecodeError):
    # Fallback/Safety net
    pass

# 2. CONSTANTS
MANUFACTURERS_FILE = "cleaned_manufacturers.txt"

# 3. SHEET LOCATIONS
SHEET_LOCATIONS = {
    "Test": "1vcHtQK2Uy7_Gan8sntTgS5axJofceMn6V02Ks_iKww4",
    # Add your real rooms here later
}
