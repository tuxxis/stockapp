import streamlit as st
import config
import brain
import time

# 1. UI CONFIG: Set layout to "wide" to use full screen
st.set_page_config(page_title="TUXOSS Inventory", page_icon="🏥", layout="wide")

# 2. MOBILE CSS HACK: Remove wasted whitespace
st.markdown("""
<style>
    /* Remove top padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    /* Make the camera widget fill the width */
    div[data-testid="stCameraInput"] {
        width: 100%;
    }
    /* Make buttons huge and touch-friendly */
    button {
        height: 3rem !important; 
    }
</style>
""", unsafe_allow_html=True)

# --- 0. THE BOUNCER (SECURITY) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    if st.session_state['password_input'] == config.APP_PASSWORD:
        st.session_state['authenticated'] = True
        del st.session_state['password_input']
    else:
        st.error("⛔ Incorrect Passphrase")

if not st.session_state['authenticated']:
    st.markdown("## 🔒 Restricted Access")
    st.text_input("Enter Passphrase:", type="password", key="password_input", on_change=check_password)
    st.stop()

# --- SESSION STATE ---
if 'warehouse_id' not in st.session_state:
    st.session_state['warehouse_id'] = None
if 'warehouse_name' not in st.session_state:
    st.session_state['warehouse_name'] = None
if 'scan_counter' not in st.session_state:
    st.session_state['scan_counter'] = 0
if 'force_create' not in st.session_state:
    st.session_state['force_create'] = False

# --- FUNCTIONS ---
def select_warehouse():
    st.title("🏥 TUXOSS Mobile")
    location_names = [""] + list(config.SHEET_LOCATIONS.keys())
    selected_name = st.selectbox("🔍 Select Location", location_names, index=0)

    if selected_name:
        if st.button(f"✅ Enter {selected_name}", use_container_width=True):
            st.session_state['warehouse_id'] = config.SHEET_LOCATIONS[selected_name]
            st.session_state['warehouse_name'] = selected_name
            st.rerun()

    st.write("---")
    custom_id = st.text_input("Or Paste Google Sheet ID:")
    if st.button("Connect Custom ID", use_container_width=True):
        if len(custom_id) > 10:
            st.session_state['warehouse_id'] = custom_id
            st.session_state['warehouse_name'] = "Custom Location"
            st.rerun()

def reset_camera():
    """Forces the camera to clear and resets flags"""
    st.session_state['scan_counter'] += 1
    if 'scanned_data' in st.session_state:
        del st.session_state['scanned_data']
    st.session_state['force_create'] = False
    st.rerun()

# --- MAIN APP ---
if st.session_state['warehouse_id'] is None:
    select_warehouse()
else:
    # Header - Compact
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"📍 {st.session_state['warehouse_name']}")
    with col2:
        if st.button("⬅", use_container_width=True):
            st.session_state['warehouse_id'] = None
            st.rerun()

    # Camera with Dynamic Key
    # Note: label_visibility="collapsed" hides the "Scanner" text to save space
    img_file = st.camera_input("Scanner", key=f"cam_{st.session_state['scan_counter']}", label_visibility="collapsed")

    if img_file:
        if 'scanned_data' not in st.session_state:
            with st.spinner("Reading Label..."):
                st.session_state['scanned_data'] = brain.analyze_image(img_file.getvalue())

        initial_data = st.session_state['scanned_data']
        
        if initial_data:
            st.divider()
            
            # LIVE INPUTS
            c1, c2 = st.columns(2)
            with c1:
                live_manuf = st.text_input("Manuf.", value=initial_data['manufacturer'])
            with c2:
                live_ref = st.text_input("REF", value=initial_data['ref'])

            check = brain.check_item_exists(st.session_state['warehouse_id'], live_manuf, live_ref)

            st.divider()

            is_update_mode = len(check) > 0 and not st.session_state['force_create']

            # --- SCENARIO A: MATCH FOUND (UPDATE MODE) ---
            if is_update_mode:
                target_row = None
                if len(check) == 1:
                    target_row = check[0]
                    st.warning(f"🔔 Match: Row {target_row['row']}")
                else:
                    st.warning(f"🔔 {len(check)} Duplicates!")
                    options = {f"Row {m['row']}: {m['current_qty']}x ({m['name'][:15]}...)": m for m in check}
                    selected_label = st.selectbox("Pick one:", list(options.keys()))
                    target_row = options[selected_label]

                st.info(f"**{target_row['name']}**")
                
                with st.form("update_stock_form"):
                    col_a, col_b = st.columns(2)
                    with col_a: 
                        st.metric("In Stock", target_row['current_qty'])
                    with col_b: 
                        add_qty = st.number_input("Add", value=int(initial_data.get('qty', 1)), min_value=1)

                    submitted = st.form_submit_button("✅ Update Stock", type="primary", use_container_width=True)
                    
                    if submitted:
                        new_total = target_row['current_qty'] + add_qty
                        brain.update_item_qty(st.session_state['warehouse_id'], target_row['row'], new_total)
                        st.toast(f"✅ Added {add_qty}!", icon="✅")
                        time.sleep(1)
                        reset_camera()

                if st.button("➕ New Entry Instead", use_container_width=True):
                    st.session_state['force_create'] = True
                    st.rerun()

            # --- SCENARIO B: NEW ITEM (CREATE MODE) ---
            else:
                if len(check) > 0:
                    st.info("✨ Creating Duplicate")
                else:
                    st.info("✨ New Item")
                
                with st.form("new_item_form"):
                    new_name = st.text_input("Name", value=initial_data['name'])
                    new_details = st.text_area("Details", value=initial_data.get('details', ''))
                    new_qty = st.number_input("Qty", value=int(initial_data.get('qty', 1)))
                    
                    submitted_new = st.form_submit_button("💾 Save Item", type="primary", use_container_width=True)
                    
                    if submitted_new:
                        save_data = {
                            "manufacturer": live_manuf,
                            "ref": live_ref,
                            "name": new_name,
                            "details": new_details,
                            "qty": new_qty
                        }
                        brain.save_new_item(st.session_state['warehouse_id'], save_data)
                        st.toast("✅ Saved!", icon="✅")
                        time.sleep(1)
                        reset_camera()
