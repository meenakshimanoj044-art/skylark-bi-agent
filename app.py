import streamlit as st
import requests
import pandas as pd
import json

# --- 1. CORE UI LAYOUT SETUP ---
st.set_page_config(page_title="Skylark Monday BI Agent", layout="wide")
st.title(" Monday.com Business Intelligence Agent")
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
    
    url = "https://monday.com"
    headers = {"Authorization": api_token, "API-Version": "2024-04"}
    
    # Secure GraphQL extraction utilizing fast page limit
    query = f"""
    query {{
      boards (ids: [{board_id}]) {{
        items_page (limit: 150) {{
          items {{
            name
            column_values {{
              id
              text
            }}
          }}
        }}
      }}
    }}
    """
    try:
        response = requests.post(url, json={'query': query}, headers=headers, timeout=12)
        res_json = response.json()
        
        if 'errors' in res_json:
            st.sidebar.error(f"API Error: {res_json['errors'][0]['message']}")
            return pd.DataFrame()
            
        items = res_json['data']['boards'][0]['items_page']['items']
        
        # Flattening structurally nested JSON into raw row records
        rows = []
        for item in items:
            row = {'Item Name': item['name']}
            for val in item['column_values']:
                row[val['id']] = val['text']
            rows.append(row)
        return pd.DataFrame(rows)
    except Exception as e:
        st.sidebar.error(f"Network error on board {board_id}: {str(e)}")
        return pd.DataFrame()

# --- 3. RUNTIME APP LOGIC EXECUTION ---
if MONDAY_TOKEN and BOARD_DEALS and BOARD_ORDERS and OPENAI_KEY:
    
    # Initialize in-memory cache arrays to minimize runtime API usage
    if 'df_deals' not in st.session_state:
        with st.spinner("Downloading real-time datasets from Monday.com..."):
            st.session_state.df_deals = fetch_monday_board(BOARD_DEALS, MONDAY_TOKEN)
            st.session_state.df_orders = fetch_monday_board(BOARD_ORDERS, MONDAY_TOKEN)
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
                    # Correct OpenRouter Endpoint Routing
                    api_url = "https://openrouter.ai"
                    headers = {
                        "Authorization": f"Bearer {OPENAI_KEY}", # This field takes your sk-or-... key now
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "meta-llama/llama-3.1-8b-instruct:free", # Completely free, high-performance model
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
    st.info("📋 Active Setup Needed: Please enter valid Monday.com credentials and your OpenRouter API key in the sidebar to wake up the agent.")

