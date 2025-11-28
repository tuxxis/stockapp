import os
import streamlit as st

# 1. SETUP: Are we on the Cloud or Local?
try:
    # --- CLOUD MODE (Streamlit) ---
    # We check if the secret exists in the cloud vault
    if "GOOGLE_CREDENTIALS_JSON" in st.secrets:
        print("☁️ Detected Cloud Environment")
        
        # We RECREATE the missing 'cred.json' file from the secret
        with open("cred.json", "w") as f:
            f.write(st.secrets["GOOGLE_CREDENTIALS_JSON"])
        
        GOOGLE_CREDENTIALS_PATH = "cred.json"
        OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
        APP_PASSWORD = st.secrets["APP_PASSWORD"]
        
    # --- LOCAL MODE (Laptop) ---
    else:
        print("💻 Detected Local Environment")
        from dotenv import load_dotenv
        load_dotenv()
        
        GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "cred.json")
        OPENAI_KEY = os.getenv("OPENAI_API_KEY")
        APP_PASSWORD = os.getenv("APP_PASSWORD")

except (FileNotFoundError, AttributeError):
    # Fallback if something goes wrong, prevents immediate crash on import
    pass

# 2. CONSTANTS
MANUFACTURERS_FILE = "cleaned_manufacturers.txt"

# 3. SHEET LOCATIONS
SHEET_LOCATIONS = {
    "Main Stockroom": "1i6zpWB-dCZnKNTseK74p9AOtMubwXPciSQGs4P6VuPk",
    # Add your other vans/rooms here
}
