"""
NumInfo — Streamlit app integrated with the DecryptKarn API (Render-ready secure version).

✅ Reads API key from environment variable: API_KEY
✅ Uses GET https://decryptkarnrwalebkl.wasmer.app/?key=<API_KEY>&term=<term>
✅ Safe for public deployment (no key in code)
✅ Supports mock fallback & CSV export

To deploy:
1. Add API_KEY in Render's Environment tab.
2. Render automatically runs `streamlit run app.py` via Procfile.
"""

import os
import streamlit as st
import requests
import pandas as pd
import json
import time
from typing import Any, Dict, Tuple

# ---------- Config ----------
API_URL = "https://decryptkarnrwalebkl.wasmer.app/"
API_KEY = os.getenv("API_KEY", None)
TERM_PARAM = "term"
KEY_PARAM = "key"

# ---------- Streamlit setup ----------
st.set_page_config(page_title="NumInfo — DecryptKarn API", layout="wide")

st.title("📱 NumInfo — DecryptKarn API Lookup")
st.caption("A secure Streamlit frontend for your DecryptKarn API. The API key is read from environment variable `API_KEY`.")

# ---------- Sidebar ----------
st.sidebar.title("⚙️ Settings")

use_mock = st.sidebar.checkbox("Use mock data (no network)", value=False)
timeout = st.sidebar.number_input("HTTP Timeout (s)", 5, 30, 10)
auto_map = st.sidebar.checkbox("Auto-map fields for better display", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("🔒 **API key:** stored securely in Render as an environment variable.")

if not API_KEY and not use_mock:
    st.sidebar.error("❌ Missing API_KEY environment variable. Set it in Render's dashboard under Environment.")
    st.stop()

# ---------- Styles ----------
st.markdown("""
<style>
.card {background: linear-gradient(180deg,#ffffff,#f3f4f6);
       padding:12px; border-radius:10px;
       box-shadow:0 6px 18px rgba(15,23,42,0.06); margin-bottom:8px;}
.key {font-weight:700; color:#0b1220; margin-bottom:6px;}
.val {font-weight:600; color:#064e3b;}
.small {font-size:0.9rem; color:#475569;}
</style>
""", unsafe_allow_html=True)

# ---------- Input ----------
col1, col2 = st.columns([3, 1])
with col1:
    term = st.text_input("Enter search term (phone number / ID / keyword)", placeholder="e.g. F or +919876543210")
with col2:
    lookup = st.button("🔍 Lookup")

# ---------- Helpers ----------
def mock_lookup(term_value: str) -> Dict[str, Any]:
    samples = [
        {"name": "Rahul Kumar", "fname": "Suresh Kumar", "mobile": term_value,
         "email": "rahul.k@example.com", "address": "Delhi"},
        {"name": "Priya Sharma", "fname": "Anil Sharma", "mobile": term_value,
         "email": "priya.sh@example.com", "address": "Mumbai"},
        {"name": "Unknown", "mobile": term_value, "address": "Unknown", "note": "No data found"},
    ]
    return samples[hash(term_value) % len(samples)]

def call_api(term_value: str, timeout: int) -> Tuple[Dict[str, Any], int]:
    params = {KEY_PARAM: API_KEY, TERM_PARAM: term_value}
    response = requests.get(API_URL, params=params, timeout=timeout)
    status = response.status_code
    try:
        data = response.json()
    except ValueError:
        data = {"text": response.text}
    if isinstance(data, list):
        data = {"results": data}
    return data, status

def auto_map_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {"raw": data}
    mapping = {
        "name": ["name", "fullname", "user"],
        "fname": ["father_name", "fname", "parent"],
        "mobile": ["mobile", "phone", "number"],
        "email": ["email", "mail"],
        "circle": ["circle", "region", "area"],
        "address": ["address", "location"],
    }
    mapped = {}
    for out_key, keys in mapping.items():
        for k in keys:
            if k in data and data[k]:
                mapped[out_key] = data[k]
                break
    others = {k: v for k, v in data.items() if k not in mapped}
    if others:
        mapped["others"] = others
    return mapped

# ---------- Lookup ----------
if lookup:
    if not term:
        st.error("❌ Please enter a search term.")
    else:
        with st.spinner("Fetching data..."):
            try:
                if use_mock:
                    result = mock_lookup(term)
                    status = 200
                else:
                    result, status = call_api(term, timeout)
                time.sleep(0.3)
            except requests.RequestException as e:
                result = {"error": str(e)}
                status = getattr(e.response, "status_code", None)
            except Exception as e:
                result = {"error": str(e)}
                status = None

        st.info(f"API Response Status: {status if status else 'N/A'}")

        colL, colR = st.columns([2, 1])
        with colL:
            st.subheader("📋 Summary")
            display = auto_map_fields(result) if auto_map else result
            for key in ("name", "fname", "mobile", "email", "circle", "address"):
                if key in display:
                    val = display.get(key) or "N/A"
                    st.markdown(f"<div class='card'><div class='key'>{key.capitalize()}</div><div class='val'>{val}</div></div>", unsafe_allow_html=True)
            if "others" in display:
                with st.expander("Other Fields"):
                    st.json(display["others"])

        with colR:
            st.subheader("🧾 Raw JSON")
            st.json(result)

        # CSV download
        try:
            df = pd.DataFrame([result]) if isinstance(result, dict) else pd.DataFrame(result)
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv_bytes, file_name=f"numinfo_{term}.csv", mime="text/csv")
        except Exception as e:
            st.warning(f"Could not generate CSV: {e}")

st.markdown("---")
st.caption("🔐 API key is securely loaded from the environment (Render.com → Environment → API_KEY).")
