#!/usr/bin/env python3
"""
Streamlit Frontend for AURELIA Financial QA Chatbot
Modern chat interface for the Lab 1 financial document system
"""

import streamlit as st
import requests
import time
import json
from typing import Dict, List, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="AURELIA Financial Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }

    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
    }

    .user-message {
        background-color: #eff6ff;
        border-left-color: #3b82f6;
    }

    .assistant-message {
        background-color: #f0fdf4;
        border-left-color: #10b981;
    }

    .source-item {
        background-color: #f8fafc;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }

    .filter-badge {
        background-color: #ddd6fe;
        color: #5b21b6;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }

    .metric-card {
        background-color: #f9fafb;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health() -> bool:
    """Check if the API is running and healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200 and response.json().get("system_ready", False)
    except:
        return False

def get_api_stats() -> Optional[Dict]:
    """Get API statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_suggestions() -> List[str]:
    """Get suggested questions"""
    try:
        response = requests.get(f"{API_BASE_URL}/suggestions", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def ask_question(question: str, filter_type: str = None, page_start: int = None, page_end: int = None) -> Optional[Dict]:
    """Send question to API"""
    try:
        payload = {"question": question}

        if filter_type and filter_type != "none":
            payload["filter_type"] = filter_type

        if page_start and page_end:
            payload["page_start"] = page_start
            payload["page_end"] = page_end

        response = requests.post(
            f"{API_BASE_URL}/ask",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def display_sources(sources: List[Dict]):
    """Display source information"""
    if not sources:
        return

    with st.expander(f"📚 Sources ({len(sources)} documents)", expanded=False):
        for source in sources:
            st.markdown(f"""
            <div class="source-item">
                <strong>#{source['rank']} [{source['element_type']}] Page {source['page_number']}</strong><br>
                <em>{source['section']}</em><br>
                {source['content_preview']}
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main Streamlit application"""

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>💰 AURELIA Financial Assistant</h1>
        <p>Ask questions about MATLAB Financial Toolbox & quantitative finance</p>
    </div>
    """, unsafe_allow_html=True)

    # Check API health
    api_healthy = check_api_health()

    if not api_healthy:
        st.error("🚨 **API Server Not Running**")
        st.markdown("""
        Please start the backend server first:
        ```bash
        python backend.py
        ```
        Then refresh this page.
        """)
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("🔧 Settings")

        # Filter options
        st.subheader("Search Filters")
        filter_type = st.selectbox(
            "Element Type",
            ["none", "code", "matlab", "matlab_financial", "tables", "text"],
            help="Filter by document element type"
        )

        # Page range
        st.subheader("Page Range")
        use_page_filter = st.checkbox("Limit to page range")

        if use_page_filter:
            col1, col2 = st.columns(2)
            with col1:
                page_start = st.number_input("Start Page", min_value=1, max_value=100, value=1)
            with col2:
                page_end = st.number_input("End Page", min_value=1, max_value=100, value=100)
        else:
            page_start = None
            page_end = None

        # System stats
        st.subheader("📊 System Stats")
        stats = get_api_stats()

        if stats:
            st.metric("Total Vectors", f"{stats['total_vectors']:,}")

            with st.expander("Element Distribution"):
                for element_type, count in stats['element_distribution'].items():
                    st.write(f"**{element_type}**: {count}")

        # Suggested questions
        st.subheader("💡 Quick Questions")
        suggestions = get_suggestions()

        if suggestions:
            selected_suggestion = st.selectbox(
                "Try these examples:",
                [""] + suggestions[:8],
                help="Click to use suggested questions"
            )

            if selected_suggestion and st.button("Use This Question"):
                st.session_state.suggested_question = selected_suggestion

    # Main chat interface
    st.header("💬 Chat with Financial Documents")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong> {message['content']}
                {f'<span class="filter-badge">{message.get("filter", "")}</span>' if message.get("filter") else ""}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>AURELIA:</strong> {message['content']}
            </div>
            """, unsafe_allow_html=True)

            # Display sources if available
            if "sources" in message:
                display_sources(message["sources"])

    # Question input
    question_input = st.chat_input("Ask about financial concepts, MATLAB functions, or quantitative methods...")

    # Handle suggested question
    if "suggested_question" in st.session_state:
        question_input = st.session_state.suggested_question
        del st.session_state.suggested_question

    # Process question
    if question_input:
        # Add user message to history
        filter_description = ""
        if filter_type != "none":
            filter_description = f"Filter: {filter_type}"
        if use_page_filter:
            filter_description += f" | Pages: {page_start}-{page_end}"

        st.session_state.chat_history.append({
            "role": "user",
            "content": question_input,
            "filter": filter_description if filter_description else None
        })

        # Show thinking indicator
        with st.spinner("🤔 Analyzing financial documents..."):
            # Get response from API
            response = ask_question(
                question_input,
                filter_type if filter_type != "none" else None,
                page_start if use_page_filter else None,
                page_end if use_page_filter else None
            )

        if response:
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["sources"],
                "processing_time": response["processing_time"]
            })

            # Show processing time
            st.caption(f"⏱️ Response generated in {response['processing_time']:.2f} seconds")

            # Show filter applied
            if response.get("filter_applied"):
                st.caption(f"🔍 Filter applied: {response['filter_applied']}")

        # Rerun to show new messages
        st.rerun()

    # Example questions at the bottom
    if not st.session_state.chat_history:
        st.markdown("---")
        st.subheader("🎯 Try These Example Questions:")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **General Financial Questions:**
            - What is the Black-Scholes model?
            - How do I calculate portfolio risk?
            - What is Value at Risk (VaR)?

            **MATLAB Code Examples:**
            - Show me blsprice function examples
            - How do I use the irr function?
            - Portfolio optimization code examples
            """)

        with col2:
            st.markdown("""
            **Advanced Topics:**
            - Monte Carlo simulation for options
            - Interest rate derivative pricing
            - Credit risk modeling techniques

            **Data & Tables:**
            - Show financial data tables
            - Interest rate term structures
            - Option pricing parameters
            """)

if __name__ == "__main__":
    main()