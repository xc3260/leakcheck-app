import streamlit as st
import pandas as pd
import json
import os
from leakcheck import LeakCheckAPI_v2, LeakCheckAPI_Public

# Configure the Streamlit page
st.set_page_config(
    page_title="LeakCheck Breach Explorer",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
    <style>
        /* Modern fonts & base colors */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Premium custom metric container styling */
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            border-color: rgba(9, 132, 227, 0.4);
        }
        .metric-val {
            font-size: 2.2rem;
            font-weight: 700;
            color: #0984e3;
            margin-bottom: 2px;
        }
        .metric-label {
            font-size: 0.95rem;
            color: #b2bec3;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 600;
        }
        
        /* Custom badge styling for compromised fields */
        .comp-badge {
            display: inline-block;
            background-color: rgba(214, 48, 49, 0.15);
            color: #d63031;
            border: 1px solid rgba(214, 48, 49, 0.3);
            border-radius: 6px;
            padding: 3px 10px;
            margin: 4px;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        
        /* Hero header section */
        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(90deg, #0984e3, #d63031);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }
        .hero-subtitle {
            font-size: 1.15rem;
            color: #636e72;
            margin-bottom: 24px;
        }
    </style>
""", unsafe_allow_html=True)

# Main Hero Header
st.markdown('<h1 class="hero-title">🔐 LeakCheck Breach Explorer</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Check if credentials have been compromised across thousands of leaked databases.</p>', unsafe_allow_html=True)

# Sidebar - Settings & Configuration
st.sidebar.markdown("## ⚙️ Configuration")

# API Mode Toggle
api_mode = st.sidebar.radio(
    "Select API Access Mode",
    ["Public API (Unauthenticated)", "Private API (Authenticated)"],
    index=0
)

# API Credentials for Private API
api_key = None
if api_mode == "Private API (Authenticated)":
    env_key = os.getenv('LEAKCHECK_APIKEY', '')
    api_key = st.sidebar.text_input(
        "LeakCheck API Key",
        value=env_key,
        type="password",
        help="Paste your API key here (must be at least 40 characters)."
    )
    if not api_key:
        st.sidebar.warning("🔑 An API key is required for private mode.")
    elif len(api_key) < 40:
        st.sidebar.error("⚠️ Invalid API key (must be >= 40 chars).")

# Advanced Options Collapsible
with st.sidebar.expander("🛠️ Advanced Settings", expanded=False):
    proxy = st.text_input(
        "Proxy Server (Optional)",
        value=os.getenv('LEAKCHECK_PROXY', ''),
        placeholder="http://host:port or socks5://host:port",
        help="Set an HTTP, HTTPS, or SOCKS5 proxy to route requests."
    )
    
    # Show limit & offset only for private API
    limit = 100
    offset = 0
    if api_mode == "Private API (Authenticated)":
        limit = st.slider("Result Limit", min_value=10, max_value=1000, value=100, step=10)
        offset = st.number_input("Result Offset", min_value=0, max_value=2500, value=0, step=10)

# Layout for Search Fields
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Search Query",
        placeholder="Enter email, username, phone, hash, or domain...",
        label_visibility="collapsed"
    )

with col2:
    query_types = [
        "auto",
        "email",
        "username",
        "phone",
        "domain",
        "hash",
        "phash",
        "origin",
        "password"
    ]
    query_type = st.selectbox(
        "Query Type",
        query_types,
        index=0,
        label_visibility="collapsed"
    )

search_clicked = st.button("🔍 Search Breach Databases", use_container_width=True, type="primary")

# Execute Search
if search_clicked:
    if not query.strip():
        st.warning("⚠️ Please enter a query to search.")
    else:
        # Initialize API wrapper
        api = None
        try:
            if api_mode == "Public API (Unauthenticated)":
                api = LeakCheckAPI_Public()
            else:
                if not api_key:
                    raise ValueError("API Key is missing. Please provide it in the sidebar.")
                api = LeakCheckAPI_v2(api_key=api_key)
            
            # Apply proxy if provided
            if proxy.strip():
                api.set_proxy(proxy.strip())
                
            # Perform query with spinner
            with st.spinner("Searching breach intelligence databases..."):
                if api_mode == "Public API (Unauthenticated)":
                    results = api.lookup(query=query.strip())
                else:
                    results = api.lookup(
                        query=query.strip(),
                        query_type=query_type if query_type != "auto" else None,
                        limit=limit,
                        offset=offset
                    )
            
            # Display Results
            if results:
                st.success("Search completed successfully!")
                
                # --- PROCESS PUBLIC RESULTS ---
                if api_mode == "Public API (Unauthenticated)":
                    found_count = results.get("found", 0)
                    compromised_fields = results.get("fields", [])
                    sources_list = results.get("sources", [])
                    
                    # Metrics Layout
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-val">{found_count}</div>
                                <div class="metric-label">Total Leaks Found</div>
                            </div>
                        """, unsafe_allow_html=True)
                    with m_col2:
                        badges_html = "".join([f'<span class="comp-badge">{field}</span>' for field in compromised_fields])
                        if not badges_html:
                            badges_html = '<span style="color: #636e72;">None</span>'
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-val" style="font-size: 1.5rem; padding-top: 8px;">{badges_html}</div>
                                <div class="metric-label">Compromised Fields</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Sources DataFrame
                    if sources_list:
                        df = pd.DataFrame(sources_list)
                        # Clean columns names for premium presentation
                        df.rename(columns={"name": "Breach Source / Database", "date": "Breach Date"}, inplace=True)
                        df.index = df.index + 1
                        
                        st.markdown("### 📋 Compromised Sources list")
                        st.dataframe(df, use_container_width=True)
                        
                        # Export actions
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        json_data = json.dumps(results, indent=4)
                        
                        exp_col1, exp_col2 = st.columns(2)
                        with exp_col1:
                            st.download_button(
                                "📥 Download Results as CSV",
                                data=csv_data,
                                file_name=f"leakcheck_{query.strip()}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        with exp_col2:
                            st.download_button(
                                "📥 Download Raw JSON Response",
                                data=json_data,
                                file_name=f"leakcheck_{query.strip()}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                    else:
                        st.info("No compromised database sources returned from the public API.")
                        
                # --- PROCESS PRIVATE RESULTS ---
                else:
                    # results is a list of matches
                    total_records = len(results)
                    
                    # Extract compromised fields dynamically from result list
                    compromised_fields = set()
                    for item in results:
                        fields = item.get("fields", [])
                        if isinstance(fields, list):
                            for f in fields:
                                compromised_fields.add(f)
                    
                    # Metrics Layout
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-val">{total_records}</div>
                                <div class="metric-label">Total Leaked Credentials Retrieved</div>
                            </div>
                        """, unsafe_allow_html=True)
                    with m_col2:
                        badges_html = "".join([f'<span class="comp-badge">{field}</span>' for field in compromised_fields])
                        if not badges_html:
                            badges_html = '<span style="color: #636e72;">None</span>'
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-val" style="font-size: 1.5rem; padding-top: 8px;">{badges_html}</div>
                                <div class="metric-label">Compromised Fields</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Table formatting
                    rows = []
                    for item in results:
                        source_info = item.get("source")
                        source_name = source_info.get("name", "N/A") if isinstance(source_info, dict) else str(source_info)
                        source_date = source_info.get("date", "N/A") if isinstance(source_info, dict) else "N/A"
                        
                        row = {
                            "Source": source_name,
                            "Breach Date": source_date,
                            "Email": item.get("email", "N/A"),
                            "Username": item.get("username", "N/A"),
                            "Password": item.get("password", "N/A")
                        }
                        
                        # Add any additional fields not in standard columns
                        for key, val in item.items():
                            if key not in ["source", "email", "username", "password", "fields"]:
                                row[key.capitalize()] = val
                        rows.append(row)
                        
                    df = pd.DataFrame(rows)
                    df.index = df.index + 1
                    
                    st.markdown("### 📋 Compromised Credentials Table")
                    st.dataframe(df, use_container_width=True)
                    
                    # Export actions
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    json_data = json.dumps(results, indent=4)
                    
                    exp_col1, exp_col2 = st.columns(2)
                    with exp_col1:
                        st.download_button(
                            "📥 Download Results as CSV",
                            data=csv_data,
                            file_name=f"leakcheck_private_{query.strip()}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    with exp_col2:
                        st.download_button(
                            "📥 Download Raw JSON Response",
                            data=json_data,
                            file_name=f"leakcheck_private_{query.strip()}.json",
                            mime="application/json",
                            use_container_width=True
                        )
            else:
                st.info("🎉 No leaks found! Your credentials do not appear in compromised databases.")
                
        except Exception as e:
            st.error(f"❌ Error during request: {str(e)}")

# Info block at the bottom
st.divider()
st.markdown("""
    <div style="text-align: center; color: #636e72; font-size: 0.85rem;">
        Developed with ❤️ using Streamlit & LeakCheck API client wrapper. 
        Please visit <a href="https://leakcheck.net" target="_blank" style="color: #0984e3; text-decoration: none;">LeakCheck.net</a> for official API documentation and plans.
    </div>
""", unsafe_allow_html=True)
