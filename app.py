"""
NumInfo — Streamlit app integrated with the provided real API.

Default API (pre-filled):
  Base URL: https://decryptkarnrwalebkl.wasmer.app/
  Key param: key
  Key value: lodalelobaby
  Term param: term

How to run locally:
  pip install -r requirements.txt
  streamlit run app.py

On Render: include requirements.txt and Procfile (provided below).
"""
import streamlit as st
import requests
import pandas as pd
import json
import time
from typing import Any, Dict, Tuple

# ---------- Page config ----------
st.set_page_config(page_title="NumInfo — DecryptKarn API", layout="wide")

# ---------- Sidebar: API settings ----------
st.sidebar.title("API & Settings")

st.sidebar.markdown(
    "Defaults are pre-filled for your API: "
    "`https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term=<value>`."
)

base_url = st.sidebar.text_input(
    "API base URL",
    value="https://decryptkarnrwalebkl.wasmer.app/",
    help="Base URL (no query string). Example: https://decryptkarnrwalebkl.wasmer.app/"
)

key_param = st.sidebar.text_input(
    "Key parameter name",
    value="key",
    help="Query param name that holds the API key (default: key)"
)

api_key = st.sidebar.text_input(
    "API key (value)",
    value="lodalelobaby",
    help="API key value (default from your example). You can replace it with a real key."
)

term_param = st.sidebar.text_input(
    "Term parameter name",
    value="term",
    help="Query param name for the searched term (default: term)"
)

http_timeout = st.sidebar.number_input("HTTP timeout (s)", min_value=1, max_value=30, value=10)
use_mock = st.sidebar.checkbox("Use mock data (no network)", value=False)
auto_map = st.sidebar.checkbox("Attempt to auto-map common fields", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("If your API needs different auth (header, POST) let me know and I will adapt.")

# ---------- Styles ----------
st.markdown(
    """
<style>
.card {background: linear-gradient(180deg,#ffffff,#f3f4f6);
       padding:12px; border-radius:10px;
       box-shadow:0 6px 18px rgba(15,23,42,0.06); margin-bottom:8px;}
.key {font-weight:700; color:#0b1220; margin-bottom:6px;}
.val {font-weight:600; color:#064e3b;}
.small {font-size:0.9rem; color:#475569;}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.title("📱 NumInfo — DecryptKarn API Integration")
st.subheader("Lookup a term (phone number or other) using the provided API")
st.write(
    "Enter the search term below. By default the app will call your API with "
    f"`{key_param}={api_key}` and `{term_param}=<term>`."
)

# ---------- Input ----------
col1, col2 = st.columns([3, 1])
with col1:
    term = st.text_input("Search term (phone number / term)", placeholder="+919876543210 or F")
with col2:
    do_lookup = st.button("🔎 Lookup")

# ---------- Helpers ----------
def mock_lookup(term_value: str) -> Dict[str, Any]:
    """Return deterministic mock data for demos/testing."""
    samples = [
        {"name": "Rahul Kumar", "fname": "Suresh Kumar", "mobile": term_value, "email": "rahul.k@example.com", "address": "Delhi"},
        {"name": "Priya Sharma", "fname": "Anil Sharma", "mobile": term_value, "email": "priya.sh@example.com", "address": "Mumbai"},
        {"name": "Unknown", "mobile": term_value, "address": "Unknown", "note": "No data found"},
    ]
    idx = 0 if not term_value else abs(hash(term_value)) % len(samples)
    return samples[idx]

def call_real_api(base: str, keyp: str, keyv: str, termp: str, termv: str, timeout: int) -> Tuple[Dict[str, Any], int]:
    """
    Call the real API using GET and return parsed JSON (or a wrapper if plain text).
    Returns (result_dict, status_code).
    """
    params = {keyp: keyv, termp: termv}
    # Make request
    resp = requests.get(base, params=params, timeout=timeout)
    status_code = resp.status_code
    # Try JSON
    try:
        data = resp.json()
        # If API returns a list, convert to wrapper dict
        if isinstance(data, list):
            data = {"results": data}
    except ValueError:
        # Not JSON: return plain text under 'text' key
        data = {"text": resp.text}
    return data, status_code

def auto_map_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Try to map common names to our display fields.
    This is best-effort — if keys are different we still show the raw JSON.
    """
    mapped = {}
    if not isinstance(data, dict):
        return {"raw": data}
    # Flatten top-level keys for common patterns
    mapping_candidates = {
        "name": ["name", "fullname", "full_name", "user", "username"],
        "fname": ["father_name", "fname", "father", "parent"],
        "mobile": ["mobile", "phone", "msisdn", "number"],
        "alt": ["alt", "alternate", "alt_number"],
        "email": ["email", "mail"],
        "id": ["id", "identifier", "uid"],
        "circle": ["circle", "region", "area"],
        "address": ["address", "addr", "location"],
    }
    # shallow search
    for out_key, candidates in mapping_candidates.items():
        for c in candidates:
            if c in data and data[c]:
                mapped[out_key] = data[c]
                break
    # include any explicit direct hits if present
    for k in mapping_candidates.keys():
        if k in data and (k not in mapped):
            mapped[k] = data[k]
    # keep other fields under 'others'
    others = {k: v for k, v in data.items() if k not in mapped}
    if others:
        mapped["others"] = others
    return mapped

# ---------- Lookup action ----------
if do_lookup:
    if not term:
        st.error("Please enter a search term (phone number or term).")
    else:
        with st.spinner("Looking up..."):
            try:
                if use_mock:
                    result = mock_lookup(term)
                    status = 200
                else:
                    # Validate URL
                    if not base_url.strip():
                        st.error("Base URL is empty. Provide a valid API base URL in the sidebar.")
                        st.stop()
                    # Call real API
                    result, status = call_real_api(base_url.strip(), key_param.strip(), api_key.strip(), term_param.strip(), term.strip(), http_timeout)
                time.sleep(0.3)
            except requests.exceptions.RequestException as e:
                st.error(f"Network error while calling API: {e}")
                result = {"error": str(e)}
                status = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                result = {"error": str(e)}
                status = None

        # Show status
        if status:
            st.info(f"API response status: {status}")

        # Pretty display
        colL, colR = st.columns([2, 1])
        with colL:
            st.subheader("Summary")
            display_obj = result
            if auto_map and isinstance(result, dict):
                mapped = auto_map_fields(result)
                display_obj = mapped
            # Show mapped/important fields first if available
            if isinstance(display_obj, dict):
                # Show some priority keys if present
                for key in ("name", "fname", "mobile", "alt", "email", "id", "circle", "address"):
                    if key in display_obj:
                        val = display_obj.get(key) or "N/A"
                        st.markdown(f"<div class='card'><div class='key'>{key.capitalize()}</div><div class='val'>{val}</div></div>", unsafe_allow_html=True)
                # Show 'others' collapsed
                if "others" in display_obj:
                    with st.expander("Other fields"):
                        st.json(display_obj["others"])
                # If no mapped keys, show raw JSON prettily
                if not any(k in display_obj for k in ("name", "mobile", "email", "address")):
                    st.write("No common fields were mapped — see raw JSON on the right.")
            else:
                st.write(display_obj)

        with colR:
            st.subheader("Raw API response")
            # If result is dict or list show JSON otherwise show text
            if isinstance(result, (dict, list)):
                st.json(result)
            else:
                st.text(str(result))

        # CSV download — convert best-effort to DataFrame
        try:
            if isinstance(result, dict):
                # If the dict contains 'results' (list), use that
                if "results" in result and isinstance(result["results"], list):
                    df = pd.DataFrame(result["results"])
                else:
                    # single-row
                    df = pd.DataFrame([result])
            elif isinstance(result, list):
                df = pd.DataFrame(result)
            else:
                df = pd.DataFrame([{"value": str(result)}])
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", data=csv_bytes, file_name=f"numinfo_{term}.csv", mime="text/csv")
        except Exception as e:
            st.warning(f"Could not prepare CSV: {e}")

# ---------- Footer ----------
st.markdown("---")
st.caption(
    "This app uses the API parameters you provided in the sidebar. "
    "If your API requires a different auth method (headers or POST body), or returns a nested JSON we should map, "
    "paste an example JSON response here and I will adapt the mapping."
)
