import streamlit as st
import requests
import pandas as pd
import json

# --- 1. CORE UI LAYOUT SETUP ---
st.set_page_config(page_title="Skylark Monday BI Agent", layout="wide")
st.title("Monday.com Business Intelligence Agent")
st.caption("Automated Executive Data Analytics Interface")

# Sidebar Configuration for Security
st.sidebar.header("API Connection Configuration")
MONDAY_TOKEN = st.sidebar.text_input("Monday.com API Token", type="password")
BOARD_DEALS = st.sidebar.text_input("Deals Board ID")
BOARD_ORDERS = st.sidebar.text_input("Work Orders Board ID")
OPENAI_KEY = st.sidebar.text_input("OpenAI API Key", type="password")

# --- 2. RESILIENT DATA EXTRACTION LAYER ---
def fetch_monday_board(board_id, api_token):
    if not board_id or not api_token:
        return pd.DataFrame()
    
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": api_token.strip(), 
        "API-Version": "2024-04",
        "Content-Type": "application/json"
    }
    
    # Fully-compliant v2 GraphQL query payload structure using variables
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
            st.sidebar.error(f"HTTP Connection Blocked: {response.status_code}")
            return pd.DataFrame()
            
        res_json = response.json()
        
        if 'errors' in res_json:
            st.sidebar.error(f"GraphQL Notification: {res_json['errors'][0]['message']}")
            return pd.DataFrame()
            
        boards_list = res_json.get('data', {}).get('boards', [])
        if not boards_list:
            return pd.DataFrame()
            
        # Target first entry element
        target_board = boards_list[0]
        items = target_board.get('items_page', {}).get('items', [])
        
        # Flattening structurally nested JSON into raw row records
        rows = []
        for item in items:
            row = {'Item Name': item.get('name', 'Unnamed Item')}
            for val in item.get('column_values', []):
                if 'id' in val:
                    row[val['id']] = val.get('text', '') if val.get('text') else "N/A"
            rows.append(row)
            
        return pd.DataFrame(rows)
    except Exception as e:
        st.sidebar.error(f"Extraction error: {str(e)}")
        return pd.DataFrame()

# --- 3. RUNTIME APP LOGIC EXECUTION ---
if MONDAY_TOKEN and BOARD_DEALS and BOARD_ORDERS and OPENAI_KEY:
    
    # Initialize in-memory cache arrays to minimize runtime API usage
    if 'df_deals' not in st.session_state or st.session_state.df_deals.empty:
        with st.spinner("Downloading real-time datasets from Monday.com..."):
            st.session_state.df_deals = fetch_monday_board(BOARD_DEALS, MONDAY_TOKEN)
            st.session_state.df_orders = fetch_monday_board(BOARD_ORDERS, MONDAY_TOKEN)
            
    if 'df_deals' in st.session_state and not st.session_state.df_deals.empty and 'df_orders' in st.session_state and not st.session_state.df_orders.empty:
        st.sidebar.success("Boards synchronized successfully!")

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

            # High-Density JSON conversion to guarantee context payload safety
            deals_json = st.session_state.df_deals.to_json(orient="records")
            orders_json = st.session_state.df_orders.to_json(orient="records")

            # Context-dependent behavioral system prompting
            if leadership_mode:
                system_role = """You are a C-Suite executive intelligence strategist. The user is asking a high-level query.
                Synthesize all numbers instantly into aggregated metrics, bold absolute dollar values, and strategic summaries.
                Ignore granular code logs. Format your entire answer using a polished markdown presentation template suitable for a leadership briefing slide."""
            else:
                system_role = """You are a meticulous Data Engineering BI Analyst. Your goal is to analyze messy data arrays,
                normalize mismatched date configurations or sector names implicitly, handle empty fields gracefully, and return precise metrics answering the operational prompt."""

            prompt_payload = f"""
            {system_role}
            
            LIVE DATA PAYLOAD FROM MONDAY.COM WORKSPACE:
            ---
            DEALS BOARD DATA ROWS:
            {deals_json}
            
            WORK ORDERS BOARD DATA ROWS:
            {orders_json}
            ---
            
            USER CONVERSATIONAL QUERY: "{user_query}"
            
            Analyze the structural records carefully, cross-reference when needed, and formulate a definitive, polished response block. Use Markdown tables if comparisons are requested.
            """

            # --- OPENROUTER ROUTING ENGINE INTERFACE ---
            with st.chat_message("assistant"):
                with st.spinner("Synthesizing datasets via OpenRouter..."):
                    try:
                        api_url = "https://openrouter.ai"
                        headers = {
                            "Authorization": f"Bearer {OPENAI_KEY.strip()}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "meta-llama/llama-3.1-8b-instruct:free",
                            "messages": [{"role": "user", "content": prompt_payload}],
                            "temperature": 0.15
                        }
                        response = requests.post(api_url, json=payload, headers=headers, timeout=25)
                        assistant_response = response.json()['choices']['message']['content']
                        
                        st.markdown(assistant_response)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    except Exception as e:
                        st.error(f"Processing Pipeline Execution Failure: {str(e)}")
    else:
        st.sidebar.warning("Awaiting secure connection parameters. Paste your personal API token into the sidebar.")
else:
    st.info("📋 Active Setup Needed: Please enter valid Monday.com credentials and your OpenRouter API key in the sidebar to wake up the agent.")
