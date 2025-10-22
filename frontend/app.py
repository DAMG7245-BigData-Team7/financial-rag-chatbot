#!/usr/bin/env python3
"""
AURELIA Streamlit Frontend
User interface for Financial Concept Note Generator
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Page configuration
st.set_page_config(
    page_title="AURELIA - Financial Concept Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
# Get FastAPI URL from environment
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8080")
# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
        font-size: 0.875rem;
    }
    .source-fintbx {
        background-color: #d4edda;
        color: #155724;
    }
    .source-wikipedia {
        background-color: #fff3cd;
        color: #856404;
    }
    .cached-badge {
        background-color: #cce5ff;
        color: #004085;
    }
    .new-badge {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def call_query_api(concept: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Call FastAPI /query endpoint"""
    try:
        response = requests.post(
            f"{FASTAPI_URL}/query",
            json={"concept": concept, "force_refresh": force_refresh},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {e}")
        return None


def call_health_api() -> Dict[str, Any]:
    """Call FastAPI /health endpoint"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return {"status": "disconnected"}


def call_stats_api() -> Dict[str, Any]:
    """Call FastAPI /stats endpoint"""
    try:
        response = requests.get(f"{FASTAPI_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None


def display_concept_note(response: Dict[str, Any]):
    """Display the concept note in a nice format"""
    
    note = response.get("note", {})
    source = response.get("source", "unknown")
    cached = response.get("cached", False)
    sources_used = response.get("sources_used", [])
    
    # Header with badges
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"## 📊 {note.get('concept', 'Concept')}")
    
    with col2:
        if source == "fintbx":
            st.markdown('<span class="source-badge source-fintbx">📄 Financial Toolbox</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="source-badge source-wikipedia">🌐 Wikipedia</span>', unsafe_allow_html=True)
    
    with col3:
        if cached:
            st.markdown('<span class="source-badge cached-badge">💾 Cached</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="source-badge new-badge">✨ Newly Generated</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Definition
    st.markdown("### 📖 Definition")
    st.write(note.get("definition", "N/A"))
    
    # Key Points
    if note.get("key_points"):
        st.markdown("### 🔑 Key Points")
        for point in note["key_points"]:
            st.markdown(f"- {point}")
    
    # MATLAB Functions
    if note.get("matlab_functions"):
        st.markdown("### 💻 MATLAB Functions")
        for func in note["matlab_functions"]:
            st.code(func, language="matlab")
    
    # Examples
    if note.get("examples"):
        st.markdown("### 📝 Examples")
        for example in note["examples"]:
            if "```" in example or "=" in example or "(" in example:
                st.code(example, language="matlab")
            else:
                st.markdown(f"- {example}")
    
    # Formulas
    if note.get("formulas"):
        st.markdown("### 🧮 Formulas")
        for formula in note["formulas"]:
            # Check if it's LaTeX format
            if "$" in formula or "\\" in formula:
                try:
                    st.latex(formula)
                except:
                    st.code(formula, language="text")
            else:
                st.code(formula, language="text")
    
    # Related Concepts
    if note.get("related_concepts"):
        st.markdown("### 🔗 Related Concepts")
        cols = st.columns(min(len(note["related_concepts"]), 4))
        for i, concept in enumerate(note["related_concepts"]):
            with cols[i % 4]:
                st.button(concept, key=f"related_{i}")
    
    # Practical Applications
    if note.get("practical_applications"):
        st.markdown("### 🎯 Practical Applications")
        for app in note["practical_applications"]:
            st.markdown(f"- {app}")
    
    # Sources/Citations
    st.markdown("---")
    st.markdown("### 📚 Sources")
    
    if sources_used:
        if source == "fintbx":
            st.info(f"📄 **Financial Toolbox Documentation:** {', '.join(sources_used)}")
        else:
            st.info(f"🌐 **Wikipedia:** {sources_used[0]}")
    
    # Metadata
    with st.expander("ℹ️ Metadata"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Source:** {source}")
            st.write(f"**Cached:** {'Yes' if cached else 'No'}")
        with col2:
            if response.get("relevance_score"):
                st.write(f"**Relevance Score:** {response['relevance_score']:.3f}")
            if response.get("generated_at"):
                st.write(f"**Generated:** {response['generated_at']}")


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🎯 AURELIA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automated Financial Concept Note Generator</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API Status
        st.markdown("### 📡 API Status")
        health = call_health_api()
        
        if health.get("status") == "healthy":
            st.success("✅ API Connected")
            st.write(f"**Pinecone:** {health.get('pinecone', 'unknown')}")
            st.write(f"**PostgreSQL:** {health.get('postgres', 'unknown')}")
        else:
            st.error("❌ API Disconnected")
            st.write(f"**URL:** {FASTAPI_URL}")
        
        # Statistics
        st.markdown("### 📊 Statistics")
        stats = call_stats_api()
        
        if stats:
            st.metric("Total Cached Concepts", stats.get("total_cached_concepts", 0))
            
            source_breakdown = stats.get("source_breakdown", {})
            col1, col2 = st.columns(2)
            with col1:
                st.metric("From Toolbox", source_breakdown.get("fintbx", 0))
            with col2:
                st.metric("From Wikipedia", source_breakdown.get("wikipedia", 0))
        
        # About
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("""
        AURELIA uses RAG (Retrieval-Augmented Generation) to automatically 
        generate standardized concept notes for financial topics.
        
        **Data Sources:**
        1. MATLAB Financial Toolbox (primary)
        2. Wikipedia (fallback)
        """)
    
    # Main content
    st.markdown("---")
    
    # Input section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        concept = st.text_input(
            "Enter a financial concept:",
            placeholder="e.g., Duration, Sharpe Ratio, Black-Scholes Model, IRR",
            help="Enter any financial concept to generate a structured note"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        force_refresh = st.checkbox("Force Refresh", help="Regenerate even if cached")
    
    # Generate button
    if st.button("🚀 Generate Concept Note", type="primary", use_container_width=True):
        if not concept:
            st.warning("⚠️ Please enter a concept first!")
        else:
            with st.spinner(f"🔍 Generating concept note for '{concept}'..."):
                result = call_query_api(concept, force_refresh)
                
                if result:
                    # Store in session state
                    st.session_state['last_result'] = result
                    st.session_state['last_concept'] = concept
    
    # Display results
    if 'last_result' in st.session_state:
        st.markdown("---")
        display_concept_note(st.session_state['last_result'])
    
    # Example concepts
    st.markdown("---")
    st.markdown("### 💡 Example Concepts to Try")
    
    examples = [
        "Duration", "Sharpe Ratio", "Black-Scholes Model",
        "Internal Rate of Return", "Net Present Value",
        "Portfolio Optimization", "Yield Curve", "Option Greeks"
    ]
    
    cols = st.columns(4)
    for i, example in enumerate(examples):
        with cols[i % 4]:
            if st.button(example, key=f"example_{i}"):
                st.session_state['query_concept'] = example
                st.rerun()
    
    # Handle example button clicks
    if 'query_concept' in st.session_state:
        concept_to_query = st.session_state['query_concept']
        del st.session_state['query_concept']
        
        with st.spinner(f"🔍 Generating concept note for '{concept_to_query}'..."):
            result = call_query_api(concept_to_query, False)
            
            if result:
                st.session_state['last_result'] = result
                st.session_state['last_concept'] = concept_to_query
                st.rerun()


if __name__ == "__main__":
    main()