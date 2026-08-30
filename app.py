import streamlit as st
import requests
import pandas as pd
import json

# --- 1. CORE UI LAYOUT SETUP ---
st.set_page_config(page_title="Skylark Monday BI Agent", layout="wide")
st.title("🦅 Monday.com Business Intelligence Agent")
st.caption("Automated Executive Data Analytics Interface")

# Sidebar Configuration for Security
st.sidebar.header("🔑 API Connection Configuration")
MONDAY_TOKEN = st.sidebar.text_input("Monday.com API Token", type="password")
BOARD_DEALS = st.sidebar.text_input("Deals Board ID")
BOARD_ORDERS = st.sidebar.text_input("Work Orders Board ID")
OPENAI_KEY = st.sidebar.text_input("OpenAI API Key", type="password")

# --- 2. RESILIENT DATA EXTRACTION LAYER ---
def fetch_monday_board(board_id, api_token):
    if not board_id or not api_token:
        return pd.DataFrame()
    
    # Correct backend endpoint address
    url = "https://monday.com"
    headers = {
        "Authorization": api_token.strip(), 
        "API-Version": "2024-04",
        "Content-Type": "application/json"
    }
    
    query = """
    query ($board_ids: [ID!]) {
      boards (ids: $board_ids) {
        items_page (limit: 100) {
          items {
            name
            column_values {
              id
              text
            }
          }
        }
      }
    }
    """
    try:
        variables = {"board_ids": [str(board_id).strip()]}
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return pd.DataFrame()
            
        res_json = response.json()
        if 'errors' in res_json:
            return pd.DataFrame()
            
        boards_list = res_json.get('data', {}).get('boards', [])
        if not boards_list or len(boards_list) == 0:
            return pd.DataFrame()
            
        # FIXED PARSING: Extracting safely from the first list element dictionary
        target_board = boards_list[0]
        items_page = target_board.get('items_page', {}) if target_board else {}
        items = items_page.get('items', []) if items_page else []
        
        if not items:
            return pd.DataFrame()

        # Flattening structurally nested JSON into raw row records
        rows = []
        for item in items:
            row = {'Item Name': item.get('name', 'Unnamed Item')}
            for val in item.get('column_values', []):
                if 'id' in val:
                    row[val['id']] = val.get('text', '') if val.get('text') else "N/A"
            rows.append(row)
            
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

# --- 3. RUNTIME APP LOGIC EXECUTION ---
if MONDAY_TOKEN and BOARD_DEALS and BOARD_ORDERS and OPENAI_KEY:
    
    # Force fresh data fetch down on credential adjustments
    if 'df_deals' not in st.session_state or st.session_state.df_deals.empty:
        with st.spinner("Downloading real-time datasets from Monday.com..."):
            st.session_state.df_deals = fetch_monday_board(BOARD_DEALS, MONDAY_TOKEN)
            st.session_state.df_orders = fetch_monday_board(BOARD_ORDERS, MONDAY_TOKEN)
            
    if 'df_deals' in st.session_state and not st.session_state.df_deals.empty and 'df_orders' in st.session_state and not st.session_state.df_orders.empty:
        if 'success_shown' not in st.session_state:
            st.sidebar.success("Boards synchronized successfully!")
            st.session_state.success_shown = True

        # MANDATORY ASSIGNMENT FEATURE: Leadership Updates Toggle Switch
        leadership_mode = st.checkbox("👔 Activate Executive Briefing Layer (Leadership Updates Mode)")

        # Data Quality Verification Expanders
        with st.expander("🔍 Inspect Fetched Monday.com Rows (Resilience Verification)"):
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Deals Pipeline")
                st.dataframe(st.session_state.df_deals, use_container_width=True)
            with c2:
                st.subheader("Work Orders Tracker")
                st.dataframe(st.session_state.df_orders, use_container_width=True)

        # Chat Log Handling
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Conversational Input Stream
        if user_query := st.chat_input("Query anything regarding pipeline health, sectoral performance, or revenue numbers..."):
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            deals_json = st.session_state.df_deals.to_json(orient="records")
            orders_json = st.session_state.df_orders.to_json(orient="records")

            if leadership_mode:
                system_role = """You are a C-Suite executive intelligence strategist. Synthesize all numbers instantly into aggregated metrics, bold absolute dollar values, and strategic summaries."""
            else:
                system_role = """You are a meticulous Data Engineering BI Analyst. Your goal is to analyze messy data arrays, normalize mismatched names, and return precise metrics."""

            prompt_payload = f"{system_role}\n\nDEALS BOARD:\n{deals_json}\n\nWORK ORDERS:\n{orders_json}\n\nUSER PROMPT:\n{user_query}"

            # --- OPENROUTER ROUTING ENGINE INTERFACE ---
            with st.chat_message("assistant"):
                with st.spinner("Synthesizing datasets via OpenRouter..."):
                    try:
                        api_url = "https://openrouter.ai"
                        headers = {
                            "Authorization": f"Bearer {OPENAI_KEY.strip()}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://streamlit.io",
                            "X-Title": "Skylark BI Agent"
                        }
                        payload = {
                            "model": "meta-llama/llama-3.1-8b-instruct:free",
                            "messages": [{"role": "user", "content": prompt_payload}],
                            "temperature": 0.15
                        }
                        response = requests.post(api_url, json=payload, headers=headers, timeout=25)
                        
                        if response.status_code != 200:
                            st.error(f"OpenRouter Gateway Error {response.status_code}: Please check credits or key validity.")
                        else:
                            assistant_response = response.json()['choices'][0]['message']['content']
                            st.markdown(assistant_response)
                            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    except Exception as e:
                        st.error(f"Processing Pipeline Execution Failure: {str(e)}")
    else:
        st.sidebar.error("Handshake Incomplete: Please check that your Board IDs are correct and your boards are set to Public/Main.")
else:
    st.info("📋 Active Setup Needed: Please enter valid credentials in the sidebar to wake up the agent.")
