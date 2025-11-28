import config
import difflib
import json
import os
import gspread
from google.oauth2 import service_account
from google.cloud import vision
from openai import OpenAI

# --- 1. SETUP ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_CREDENTIALS_PATH

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/cloud-vision"
]

creds = service_account.Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

vision_client = vision.ImageAnnotatorClient()
openai_client = OpenAI(api_key=config.OPENAI_KEY)


# --- 2. MANUFACTURER LOGIC ---

def load_manufacturers():
    try:
        with open(config.MANUFACTURERS_FILE, "r") as f:
            return [line.strip().upper() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return []

KNOWN_MANUFACTURERS = load_manufacturers()

def find_best_manufacturer(scanned_name):
    scanned_upper = str(scanned_name).strip().upper()
    if scanned_upper in KNOWN_MANUFACTURERS: return scanned_upper

    for known in sorted(KNOWN_MANUFACTURERS, key=len, reverse=True):
        if scanned_upper.startswith(known) or known.startswith(scanned_upper):
            return known

    matches = difflib.get_close_matches(scanned_upper, KNOWN_MANUFACTURERS, n=1, cutoff=0.8)
    return matches[0] if matches else scanned_upper


# --- 3. CORE FUNCTIONS ---

def analyze_image(image_bytes):
    image = vision.Image(content=image_bytes)
    response = vision_client.document_text_detection(image=image)
    text = response.full_text_annotation.text

    if not text: return None

    prompt = f"""
    Analyze this medical product label for inventory.
    
    1. MANUFACTURER: 
       - BRAND NAME or LOGO (Largest visual text).
       - Ignore legal factory text unless it's the brand.

    2. REF: 
       - Catalog Number/SKU (Strictly the code).

    3. NAME: 
       - The Short Product Title.
       - Example: "Gravity IV Set - Vented"

    4. DETAILS:
       - The technical specifications.
       - Example: "150cm, 3-way stopcock, 15um filter".

    5. QTY: 
       - Pack size. Default "1" if missing.

    Text content:
    {text}

    Return JSON: {{"manufacturer": "...", "ref": "...", "name": "...", "details": "...", "qty": "..."}}
    """

    gpt_response = openai_client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(gpt_response.choices[0].message.content)
    data['manufacturer'] = find_best_manufacturer(data['manufacturer'])
    return data


def check_item_exists(sheet_id, manufacturer, ref):
    """
    Scans the ENTIRE sheet and returns a LIST of all matches.
    """
    matches = [] # We will store all duplicate rows here
    
    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.sheet1
        all_values = ws.get_all_values()
        
        for i, row in enumerate(all_values):
            if i == 0 or not row or len(row) < 2: continue

            if str(row[0]).strip().upper() == str(manufacturer).strip().upper() and \
               str(row[1]).strip().upper() == str(ref).strip().upper():
                
                current_qty = int(row[4]) if len(row) > 4 and str(row[4]).isdigit() else 0
                
                # Add this match to our list
                matches.append({
                    "row": i + 1, 
                    "current_qty": current_qty, 
                    "name": row[2] if len(row) > 2 else "Unknown",
                    "details": row[3] if len(row) > 3 else ""
                })
        
        return matches # Returns a list [] (Empty if no matches)
        
    except Exception as e:
        print(f"Search Error: {e}")
        return []


def save_new_item(sheet_id, data):
    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.sheet1
        
        uid = f"{data['manufacturer'][:3]}{data['ref']}".upper().replace(" ", "")
        
        row = [
            data['manufacturer'],
            data['ref'],
            data['name'],
            data.get('details', ''),
            int(data['qty']),
            "Shelf A",
            uid
        ]
        
        ws.append_row(row)
        return True
    except Exception as e:
        print(f"Save Error: {e}")
        return False


def update_item_qty(sheet_id, row_number, new_total_qty):
    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.sheet1
        ws.update_cell(row_number, 5, int(new_total_qty))
        return True
    except Exception as e:
        print(f"Update Error: {e}")
        return False