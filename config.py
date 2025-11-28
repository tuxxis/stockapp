# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "cred.json")
MANUFACTURERS_FILE = "cleaned_manufacturers.txt"

# The "Menu" of Sheets (Warehouses)
# You can add as many as you want here.
SHEET_LOCATIONS = {
    "Test": "1vcHtQK2Uy7_Gan8sntTgS5axJofceMn6V02Ks_iKww4",
   
}