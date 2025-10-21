import streamlit as st
import requests
import pandas as pd
import time
import json

st.set_page_config(page_title="NumInfo Lookup", layout="wide")

# ---- Sidebar ----
st.sidebar.title("⚙️ Settings")
api_url = st.sidebar.text_input("External API URL (optional)", help="If empty, mock data will be used.")
timeout = st.sidebar.number_input("HTTP Timeout (seconds)", 5, 30, 8)
use_mock = st.sidebar.checkbox("Use Mock Data", value=(api_url.strip() == ""))
show_hacker_style = st.sidebar.checkbox("Enable Hacker Style Header", value=False)

# ---- Styles ----
st.markdown("""
<style>
.card {background: linear-gradient(180deg,#ffffff,#f3f4f6);
       padding:16px; border-radius:12px;
       box-shadow:0 6px 18px rgba(15,23,42,0.06);}
.key {font-weight:600; color:#0f172a;}
.val {font-weight:600; color:#064e3b;}
</style>
""", unsafe_allow_html=True)

# ---- Header ----
if show_hacker_style:
    st.markdown("""
    <div style='font-family:monospace; background:#0b1220; color:#34d399;
                padding:14px; border-radius:8px'>
      [============== HACK INPUT MODE ==============]<br/>
      >>> Enter target mobile number <<<
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("📱 NumInfo — Phone Number Lookup")
    st.caption("Enter a phone number to fetch user details. Works with real or mock data.")

# ---- Input ----
col1, col2 = st.columns([3, 1])
with col1:
    number = st.text_input("Enter Phone Number", placeholder="+919876543210")
with col2:
    search_btn = st.button("🔍 Lookup")

# ---- Mock Data ----
def mock_lookup(num: str):
    data = [
        {"name": "Rahul Kumar", "fname": "Suresh Kumar", "mobile": num, "alt": "",
         "email": "rahul.k@example.com", "id": "ABC12345", "circle": "Delhi",
         "address": "Connaught Place, New Delhi"},
        {"name": "Priya Sharma", "fname": "Anil Sharma", "mobile": num,
         "alt": "+919812345678", "email": "priya.sh@example.com",
         "id": "ID998877", "circle": "Mumbai", "address": "Andheri West, Mumbai"},
        {"name": "Amit Verma", "fname": "R.C. Verma", "mobile": num,
         "alt": "+917001112233", "email": "amit.v@example.com",
         "id": "V123456", "circle": "Kolkata", "address": "Salt Lake, Kolkata"},
        {"name": "Sanjay Rao", "fname": "Mohan Rao", "mobile": num,
         "alt": "+917009998877", "email": "sanjay.rao@example.com",
         "id": "SR556677", "circle": "Chennai", "address": "T. Nagar, Chennai"},
    ]
    return data[hash(num) % len(data)]

# ---- Lookup Logic ----
if search_btn:
    if not number.strip():
        st.error("❌ Please enter a phone number!")
    else:
        with st.spinner("Fetching details..."):
            try:
                if use_mock or not api_url.strip():
                    time.sleep(0.7)
                    result = mock_lookup(number)
                else:
                    res = requests.get(api_url, params={"number": number}, timeout=timeout)
                    res.raise_for_status()
                    result = res.json()
            except Exception as e:
                st.error(f"⚠️ Error fetching info: {e}")
                result = {"error": str(e)}

        if "error" not in result:
            st.success("✅ Lookup Successful!")
            colL, colR = st.columns([2, 1])
            with colL:
                st.subheader("📋 Summary")
                for key, label in {
                    "name": "Name", "fname": "Father Name", "mobile": "Mobile",
                    "alt": "Alt Number", "email": "Email", "id": "ID",
                    "circle": "Circle", "address": "Address"
                }.items():
                    val = result.get(key, "N/A")
                    st.markdown(f"<div class='card'><div class='key'>{label}</div><div class='val'>{val}</div></div>", unsafe_allow_html=True)

            with colR:
                st.subheader("🧾 Raw JSON")
                st.json(result)

            df = pd.DataFrame([result])
            st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode("utf-8"),
                               file_name=f"numinfo_{number}.csv", mime="text/csv")
        else:
            st.warning("⚠️ Lookup failed. Check connection or API.")
