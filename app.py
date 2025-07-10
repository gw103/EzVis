"""
FOB Test Analysis Dashboard - Main Application Entry Point
"""

import streamlit as st
from config.settings import configure_page
from ui.components import apply_custom_styling
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content


def main():
    """Main application entry point"""
    # Configure page
    configure_page()
    
    # Apply custom styling
    apply_custom_styling()
    
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.title("FOB Test Analysis Dashboard")
    st.markdown("Visualize and compare Functional Observational Battery (FOB) test results")
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    defaults = {
        'projects': {},
        'active_project': None,
        'experiments': {},
        'selected_experiments': [],
        'mode': "Individual Behavior",
        'fob_plot_type': None,
        'selected_time': 0,
        'selected_behavior': "",
        'global_min': 0,
        'global_max': 10
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Ensure all existing experiments have numerical_score column
    ensure_numerical_scores_in_experiments()


def ensure_numerical_scores_in_experiments():
    """Ensure all experiments in session state have numerical_score column"""
    if 'experiments' not in st.session_state:
        return
    
    from core.data_processor import FOBDataProcessor
    
    for group_name, df in st.session_state.experiments.items():
        if 'numerical_score' not in df.columns:
            df_copy = df.copy()
            df_copy['numerical_score'] = df_copy['score'].apply(FOBDataProcessor.parse_score)
            st.session_state.experiments[group_name] = df_copy


if __name__ == "__main__":
    main()