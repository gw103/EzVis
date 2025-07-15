# dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
import os
import re
import uuid
import random
import datetime

# Set up the page
st.set_page_config(
    page_title="📊 FOB Test Analysis Dashboard",
    page_icon="🐭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
def set_custom_style():
    st.markdown("""
        <style>
        .main {
            background-color: #f5f9ff;
        }
        .sidebar .sidebar-content {
            background-color: #e8f4ff;
        }
        h1 {
            color: #1a3d6d;
            border-bottom: 2px solid #1a3d6d;
        }
        .stButton>button {
            background-color: #1a3d6d;
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #2a5a9c;
            transform: scale(1.05);
        }
        .worksheet-container {
            background-color: white;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .plot-container {
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            background-color: white;
        }
        .abnormal-high {
            background-color: #ffcccc;
        }
        .abnormal-low {
            background-color: #cce5ff;
        }
        .normal {
            background-color: #e6ffe6;
        }
        .template-download {
            border: 1px solid #1a3d6d;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            background-color: #e8f4ff;
        }
        .autonomic-table {
            width: 100%;
            margin-bottom: 20px;
        }
        .autonomic-table th {
            background-color: #1a3d6d;
            color: white;
        }
        .autonomic-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        </style>
    """, unsafe_allow_html=True)

set_custom_style()

# App header
st.title("FOB Test Analysis Dashboard")
st.markdown("Visualize and compare Functional Observational Battery (FOB) test results")

# Constants for modes
AUTONOMIC_OBSERVATIONS = [
    'piloerection',
    'skin color',
    'cyanosis',
    'respiratory activity',
    'irregular breathing',
    'stertorous'
]

REFLEX_OBSERVATIONS = [
    'startle response',
    'touch reactivity',
    'vocalization',
    'abnormal gait',
    'corneal reflex',
    'pinna reflex',
    'catalepsy',
    'grip reflex',
    'pulling reflex',
    'righting reflex',
    'body tone',
    'pain response'
]

CONVULSIVE_OBSERVATIONS = [
    'spontaneous activity',
    'restlessness',
    'fighting',
    'writhing',
    'tremor',
    'stereotypy',
    'twitches / jerks',
    'straub',
    'opisthotonus',
    'convulsion'
]

# Initialize session state
if 'projects' not in st.session_state:
    st.session_state.projects = {}
if 'active_project' not in st.session_state:
    st.session_state.active_project = None
if 'experiments' not in st.session_state:
    st.session_state.experiments = {}
if 'selected_experiments' not in st.session_state:
    st.session_state.selected_experiments = []
if 'mode' not in st.session_state:
    st.session_state.mode = "General Behavior"
if 'selected_time' not in st.session_state:
    st.session_state.selected_time = 0
if 'global_min' not in st.session_state:
    st.session_state.global_min = 0
if 'global_max' not in st.session_state:
    st.session_state.global_max = 10
if 'worksheet_data' not in st.session_state:
    st.session_state.worksheet_data = {}
if 'save_status' not in st.session_state:
    st.session_state.save_status = {}

# Helper function to parse the scoring system
def parse_score(score_str):
    """Parse 0/4/8 scoring system with +/- modifiers"""
    if pd.isna(score_str):
        return np.nan
    
    # Convert to string if it's a number
    if isinstance(score_str, (int, float)):
        return float(score_str)
    
    # Extract base score and modifiers
    match = re.match(r'(\d+(?:\.\d+)?)([\+\-]*)', str(score_str))
    if not match:
        return np.nan
    
    base_score = float(match.group(1))
    modifiers = match.group(2)
    
    # Calculate numerical value
    value = base_score
    if modifiers:
        modifier_value = len(modifiers) * (1 if '+' in modifiers else -1)
        value += modifier_value
    
    return value

# Function to calculate mean score from mice data
def calculate_mean_score(mice_scores):
    """Calculate mean score from individual mice scores"""
    parsed_scores = [parse_score(score) for score in mice_scores if pd.notna(score)]
    if parsed_scores:
        return np.mean(parsed_scores)
    return np.nan

# Function to generate random data
def generate_random_data(mode, times, num_mice=8):
    """Generate random data based on the mode"""
    if mode == "Body Temperature":
        # Normal temp range: 36.5-37.5°C, with some variation
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_mice + 1):
            data[f'mouse_{i}'] = []
        
        for time in times:
            data['time'].append(time)
            data['observation'].append('body temperature')
            for i in range(1, num_mice + 1):
                # Generate realistic body temperature
                base_temp = np.random.normal(37.0, 0.5)
                # Add some time-based variation
                if time > 30:
                    base_temp += np.random.normal(0.2, 0.1)
                data[f'mouse_{i}'].append(f"{base_temp:.1f}")
        
        return pd.DataFrame(data)
    
    elif mode == "Convulsive Behaviors and Excitability":
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_mice + 1):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for obs in CONVULSIVE_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_mice + 1):
                    # 0/4 system with modifiers
                    if np.random.random() < 0.7:  # 70% normal
                        base = 0
                    else:
                        base = 4
                    modifier = np.random.choice(['', '+', '-', '++', '--'], p=[0.5, 0.2, 0.2, 0.05, 0.05])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    elif mode == "Autonomic and Sensorimotor Functions":
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_mice + 1):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for obs in AUTONOMIC_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_mice + 1):
                    # 0/4 system
                    if np.random.random() < 0.75:  # 75% normal
                        base = 0
                    else:
                        base = 4
                    modifier = np.random.choice(['', '+', '-'], p=[0.6, 0.2, 0.2])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    elif mode == "Reflex Capabilities":
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_mice + 1):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for obs in REFLEX_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_mice + 1):
                    # 0/4 system
                    if np.random.random() < 0.8:  # 80% normal
                        base = 0
                    else:
                        base = 4
                    modifier = np.random.choice(['', '+', '-', '++', '--'], p=[0.5, 0.2, 0.2, 0.05, 0.05])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    else:  # General Behavior
        behaviors = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_mice + 1):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for behavior in behaviors:
                data['time'].append(time)
                data['observation'].append(behavior)
                for i in range(1, num_mice + 1):
                    # 0/4/8 system - generate scores mostly in normal range
                    if np.random.random() < 0.7:  # 70% normal range
                        base = 4
                    else:
                        base = np.random.choice([0, 8])
                    modifier = np.random.choice(['', '+', '-', '++', '--'], p=[0.5, 0.2, 0.2, 0.05, 0.05])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

# Function to process data with onset/offset tracking
def process_data_with_episodes(df, mode):
    """Process data and track onset/offset of abnormal episodes"""
    results = []
    
    # Get appropriate observations based on mode
    if mode == "Autonomic and Sensorimotor Functions":
        observations = AUTONOMIC_OBSERVATIONS
    elif mode == "Reflex Capabilities":
        observations = REFLEX_OBSERVATIONS
    elif mode == "Convulsive Behaviors and Excitability":
        observations = CONVULSIVE_OBSERVATIONS
    elif mode == "Body Temperature":
        observations = ['body temperature']
    else:  # General Behavior
        observations = df['observation'].unique()
    
    for obs in observations:
        obs_df = df[df['observation'] == obs].sort_values('time')
        
        if obs_df.empty:
            continue
        
        # Track episodes
        onset_time = None
        in_episode = False
        
        for _, row in obs_df.iterrows():
            # Calculate mean score from all mice
            mice_scores = [row[f'mouse_{i}'] for i in range(1, 9) if f'mouse_{i}' in row]
            mean_score = calculate_mean_score(mice_scores)
            
            # Determine if abnormal based on mode
            is_abnormal = False
            if mode == "Body Temperature":
                # Abnormal if outside 36-38°C range
                is_abnormal = mean_score < 36 or mean_score > 38
            elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                # Abnormal if mean > 2
                is_abnormal = mean_score > 2
            else:  # General Behavior
                # Abnormal if mean < 2 or > 6
                is_abnormal = mean_score < 2 or mean_score > 6
            
            if is_abnormal and not in_episode:
                # Start of abnormal episode
                onset_time = row['time']
                in_episode = True
            elif not is_abnormal and in_episode:
                # End of abnormal episode
                results.append({
                    'Observation': obs,
                    'Onset Time': onset_time,
                    'Offset Time': row['time'],
                    'Duration': row['time'] - onset_time,
                    'Peak Score': mean_score
                })
                in_episode = False
                onset_time = None
        
        # Handle ongoing episode
        if in_episode and onset_time is not None:
            results.append({
                'Observation': obs,
                'Onset Time': onset_time,
                'Offset Time': obs_df['time'].max(),
                'Duration': obs_df['time'].max() - onset_time,
                'Peak Score': mean_score
            })
    
    return pd.DataFrame(results)

# Function to generate template data
def create_template(mode="General Behavior"):
    """Create template with individual mice columns"""
    if mode == "Body Temperature":
        times = [0, 15, 30, 45, 60]
        data = {
            'time': [],
            'observation': []
        }
        # Add mice columns
        for i in range(1, 9):
            data[f'mouse_{i}'] = []
        
        for time in times:
            data['time'].append(time)
            data['observation'].append('body temperature')
            for i in range(1, 9):
                # Normal temperature range
                temp = np.random.normal(37.0, 0.2)
                data[f'mouse_{i}'].append(f"{temp:.1f}")
        
        return pd.DataFrame(data)
    
    elif mode == "Convulsive Behaviors and Excitability":
        times = [0, 15, 30]
        data = {
            'time': [],
            'observation': []
        }
        # Add mice columns
        for i in range(1, 9):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for obs in CONVULSIVE_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                # Add scores for each mouse
                for i in range(1, 9):
                    # 0/4 system with modifiers
                    base = 0
                    modifier = random.choice(['', '+', '-'])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    elif mode == "Autonomic and Sensorimotor Functions":
        times = [0, 15, 30]
        data = {
            'time': [],
            'observation': []
        }
        # Add mice columns
        for i in range(1, 9):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for obs in AUTONOMIC_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                # Add scores for each mouse
                for i in range(1, 9):
                    # Start with normal (0) scores
                    base = 0
                    modifier = random.choice(['', '+', '-'])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    elif mode == "Reflex Capabilities":
        times = [0, 15, 30]
        data = {
            'time': [],
            'observation': []
        }
        # Add mice columns
        for i in range(1, 9):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for obs in REFLEX_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                # Add scores for each mouse
                for i in range(1, 9):
                    # 0/4 system with modifiers
                    base = random.choice([0, 4])
                    modifier = random.choice(['', '+', '-', '++', '--'])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    else:  # General Behavior
        behaviors = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
        times = [0, 15, 30]
        
        data = {
            'time': [],
            'observation': []
        }
        # Add mice columns
        for i in range(1, 9):
            data[f'mouse_{i}'] = []
        
        for time in times:
            for behavior in behaviors:
                data['time'].append(time)
                data['observation'].append(behavior)
                
                # Add scores for each mouse
                for i in range(1, 9):
                    # 0/4/8 system with modifiers
                    base = random.choice([0, 4, 8])
                    modifier = random.choice(['', '+', '-', '++', '--'])
                    data[f'mouse_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

# Function to create worksheet interface
def create_worksheet(mode, experiment_name):
    """Create an editable worksheet for data entry"""
    st.subheader(f"Data Entry Worksheet - {experiment_name}")
    
    # Create a unique key for this worksheet that includes mode
    worksheet_key = f"worksheet_{experiment_name}_{mode}"
    
    # Initialize worksheet data if not exists
    if worksheet_key not in st.session_state:
        if mode == "Autonomic and Sensorimotor Functions":
            observations = AUTONOMIC_OBSERVATIONS
        elif mode == "Reflex Capabilities":
            observations = REFLEX_OBSERVATIONS
        elif mode == "Convulsive Behaviors and Excitability":
            observations = CONVULSIVE_OBSERVATIONS
        elif mode == "Body Temperature":
            observations = ['body temperature']
        else:
            observations = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
        
        # Create initial data structure
        times = [0, 15, 30, 45, 60]
        data = []
        for time in times:
            for obs in observations:
                row = {'time': time, 'observation': obs}
                for i in range(1, 9):
                    if mode == "Body Temperature":
                        row[f'mouse_{i}'] = '37.0'
                    else:
                        row[f'mouse_{i}'] = '0'
                data.append(row)
        
        st.session_state[worksheet_key] = pd.DataFrame(data)
    
    # Get the dataframe from session state
    df = st.session_state[worksheet_key].copy()
    
    # Configure column settings with better formatting
    column_config = {
        'time': st.column_config.NumberColumn(
            'Time (min)', 
            min_value=0, 
            max_value=300, 
            step=5,
            format="%d min"
        ),
        'observation': st.column_config.TextColumn('Observation', disabled=True)
    }
    
    # Add mouse columns configuration
    for i in range(1, 9):
        if mode == "Body Temperature":
            column_config[f'mouse_{i}'] = st.column_config.TextColumn(
                f'Mouse {i}',
                help=f"Temperature for mouse {i} in Celsius (e.g., 37.2)",
                max_chars=5
            )
        else:
            column_config[f'mouse_{i}'] = st.column_config.TextColumn(
                f'Mouse {i}',
                help=f"Score for mouse {i}. Use appropriate scoring system for the mode",
                max_chars=5
            )
    
    # Create two tabs for different interaction modes
    tab1, tab2 = st.tabs(["📝 Edit with Save Button", "💾 Auto-Save Mode"])
    
    with tab1:
        st.markdown("**Manual Save Mode** - Make multiple edits then save all at once")
        
        # Check if there are unsaved changes
        temp_key = f"temp_{worksheet_key}"
        if temp_key in st.session_state and not df.equals(st.session_state[temp_key]):
            st.warning("⚠️ You have unsaved changes!")
        
        # Use a form to prevent constant reruns
        with st.form(key=f"form_{worksheet_key}"):
            # Create editable dataframe
            edited_df = st.data_editor(
                df,
                column_config=column_config,
                use_container_width=True,
                num_rows="dynamic",
                key=f"editor_{worksheet_key}_form",
                hide_index=True
            )
            
            # Store temp changes
            st.session_state[temp_key] = edited_df
            
            # Form submit button
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
            with col2:
                fill_random = st.form_submit_button("🎲 Fill Random Data", use_container_width=True)
            with col3:
                st.markdown("**Add timestep:**")
                new_timestep = st.number_input(
                    "Next timestep (min)", 
                    min_value=0,
                    max_value=300,
                    step=5,
                    value=edited_df['time'].max() + 5 if not edited_df.empty else 0,
                    key=f"new_time_{worksheet_key}",
                    label_visibility="collapsed"
                )
                add_timestep = st.form_submit_button("⏱️ Add", use_container_width=True)
            with col4:
                reset = st.form_submit_button("🔄 Reset", use_container_width=True)
            
            if submitted:
                # Update session state with edited data
                st.session_state[worksheet_key] = edited_df
                st.session_state.worksheet_data[experiment_name] = edited_df
                st.session_state.save_status[experiment_name] = "saved"
                st.success("✅ Changes saved successfully!")
                if temp_key in st.session_state:
                    del st.session_state[temp_key]
            
            if fill_random:
                # Generate random data
                times = sorted(edited_df['time'].unique())
                random_df = generate_random_data(mode, times)
                st.session_state[worksheet_key] = random_df
                st.rerun()
            
            if add_timestep:
                # Add new timestep with all observations
                new_rows = []
                observations = edited_df['observation'].unique()
                for obs in observations:
                    new_row = {'time': new_timestep, 'observation': obs}
                    for i in range(1, 9):
                        if mode == "Body Temperature":
                            new_row[f'mouse_{i}'] = '37.0'
                        else:
                            new_row[f'mouse_{i}'] = '0'
                    new_rows.append(new_row)
                
                # Append new rows
                new_df = pd.concat([edited_df, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state[worksheet_key] = new_df
                st.rerun()
            
            if reset:
                # Reset to original state
                if temp_key in st.session_state:
                    del st.session_state[temp_key]
                st.rerun()
    
    with tab2:
        st.markdown("**Auto-Save Mode** - Changes are saved instantly as you type")
        st.info("💡 Each edit is automatically saved. Best for quick, single-cell edits.")
        
        # Quick action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🎲 Fill Random Data", use_container_width=True, key=f"random_auto_{worksheet_key}"):
                times = sorted(st.session_state[worksheet_key]['time'].unique())
                random_df = generate_random_data(mode, times)
                st.session_state[worksheet_key] = random_df
                st.rerun()
        
        # Create editable dataframe without form (auto-saves)
        edited_df_auto = st.data_editor(
            st.session_state[worksheet_key],
            column_config=column_config,
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{worksheet_key}_auto",
            hide_index=True
        )
        
        # Auto-save the changes
        if not edited_df_auto.equals(st.session_state[worksheet_key]):
            st.session_state[worksheet_key] = edited_df_auto
            st.session_state.worksheet_data[experiment_name] = edited_df_auto
            st.session_state.save_status[experiment_name] = "saved"
        
        # Show save status with timestamp
        st.success(f"✅ Auto-saved at {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        # Quick actions - NEW TIMESTEP FUNCTIONALITY
        st.markdown("**Add new timestep:**")
        col1, col2 = st.columns([3, 2])
        with col1:
            new_timestep_auto = st.number_input(
                "Next timestep (min)", 
                min_value=0,
                max_value=300,
                step=5,
                value=edited_df_auto['time'].max() + 5 if not edited_df_auto.empty else 0,
                key=f"new_time_auto_{worksheet_key}",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("⏱️ Add Timestep", use_container_width=True):
                # Add rows for new timestep
                new_rows = []
                observations = edited_df_auto['observation'].unique()
                for obs in observations:
                    new_row = {'time': new_timestep_auto, 'observation': obs}
                    for i in range(1, 9):
                        if mode == "Body Temperature":
                            new_row[f'mouse_{i}'] = '37.0'
                        else:
                            new_row[f'mouse_{i}'] = '0'
                    new_rows.append(new_row)
                
                # Append new rows
                new_df = pd.concat([edited_df_auto, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state[worksheet_key] = new_df
                st.rerun()
    
    # Get the current dataframe (from whichever tab was used)
    current_df = st.session_state[worksheet_key]
    
    # Calculate and display mean scores (outside the tabs)
    st.subheader("📊 Mean Scores Summary")
    
    # Add a filter for time points
    unique_times = sorted(current_df['time'].unique())
    selected_times = st.multiselect(
        "Filter by time points:",
        unique_times,
        default=unique_times[:3] if len(unique_times) > 3 else unique_times
    )
    
    summary_data = []
    filtered_df = current_df[current_df['time'].isin(selected_times)] if selected_times else current_df
    
    for _, row in filtered_df.iterrows():
        mice_scores = [row[f'mouse_{i}'] for i in range(1, 9) if f'mouse_{i}' in row]
        mean_score = calculate_mean_score(mice_scores)
        
        # Count how many mice have valid scores
        valid_scores = sum(1 for score in mice_scores if pd.notna(score) and score != '')
        
        # Determine status based on mode and thresholds
        if pd.isna(mean_score):
            status = 'N/A'
        else:
            if mode == "Body Temperature":
                status = '🟢 Normal' if 36 <= mean_score <= 38 else '🔴 Abnormal'
            elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                status = '🟢 Normal' if mean_score <= 2 else '🔴 Abnormal'
            else:  # General Behavior
                if mean_score < 2 or mean_score > 6:
                    status = '🔴 Abnormal'
                else:
                    status = '🟢 Normal'
        
        summary_data.append({
            'Time': f"{int(row['time'])} min",
            'Observation': row['observation'],
            'Mean Score': f"{mean_score:.2f}" if not pd.isna(mean_score) else "N/A",
            'Valid Mice': f"{valid_scores}/8",
            'Status': status
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Display with custom styling
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small")
        }
    )
    
    # Display abnormal episodes
    if mode != "General Behavior":
        st.subheader("🚨 Abnormal Episodes (Onset/Offset)")
        episodes_df = process_data_with_episodes(current_df, mode)
        if not episodes_df.empty:
            st.dataframe(episodes_df, use_container_width=True, hide_index=True)
        else:
            st.info("No abnormal episodes detected")
    
    return current_df

# Template Section
with st.expander("📝 Download Data Templates", expanded=True):
    st.markdown("""
    ### Data Templates
    Download these templates to get started with the correct format for your experiments.
    Each template includes columns for individual mice (mouse_1 through mouse_8).
    """)
    
    # Mode selection for template
    template_mode = st.radio("Select Template Type", 
                            ["General Behavior", "Autonomic and Sensorimotor Functions", 
                             "Reflex Capabilities", "Body Temperature", 
                             "Convulsive Behaviors and Excitability"],
                            index=0,
                            horizontal=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CSV Template")
        template_csv = create_template(template_mode)
        st.dataframe(template_csv.head(5))
        
        # Convert to CSV
        csv = template_csv.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Download CSV Template",
            data=csv,
            file_name=f"fob_template_{template_mode.replace(' ', '_')}.csv",
            mime="text/csv",
            help="Download CSV template for experiment data"
        )
    
    with col2:
        st.subheader("Excel Template")
        template_excel = create_template(template_mode)
        st.dataframe(template_excel.head(5))
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            template_excel.to_excel(writer, index=False, sheet_name='FOB Data')
        
        st.download_button(
            label="Download Excel Template",
            data=output.getvalue(),
            file_name=f"fob_template_{template_mode.replace(' ', '_')}.xlsx",
            mime="application/vnd.ms-excel",
            help="Download Excel template for experiment data"
        )
    
    st.info("""
    **Template Format Requirements:**
    - **time**: Time point in minutes (e.g., 0, 5, 10, 15)
    - **observation**: Name of the behavior being observed
    - **mouse_1 to mouse_8**: Individual scores for each mouse
        - General Behavior: 0/4/8 with optional modifiers (e.g., "4++", "8-")
        - Autonomic/Reflex/Convulsive Functions: 0/4 with optional modifiers (e.g., "4+", "0-")
        - Body Temperature: Numerical values in Celsius (e.g., "37.2")
    """)
    
    if template_mode == "Body Temperature":
        st.warning("""
        **Body Temperature Specifics:**
        - Normal range: 36-38°C
        - Values outside this range are considered abnormal
        """)
    elif template_mode == "Convulsive Behaviors and Excitability":
        st.warning("""
        **Convulsive Behaviors Specifics:**
        - Mean score > 2 is considered abnormal
        - Valid observations: spontaneous activity, restlessness, fighting, writhing, tremor, 
          stereotypy, twitches/jerks, straub, opisthotonus, convulsion
        """)
    elif template_mode == "Autonomic and Sensorimotor Functions":
        st.warning("""
        **Autonomic & Sensory Function Specifics:**
        - Mean score > 2 is considered abnormal
        - Valid observations: piloerection, skin color, cyanosis, respiratory activity, irregular breathing, stertorous
        """)
    elif template_mode == "Reflex Capabilities":
        st.warning("""
        **Reflex Capabilities Specifics:**
        - Mean score > 2 is considered abnormal
        - Valid observations: startle response, touch reactivity, vocalization, abnormal gait, 
          corneal reflex, pinna reflex, catalepsy, grip reflex, pulling reflex, righting reflex, 
          body tone, pain response
        """)
    else:
        st.warning("""
        **General Behavior Specifics:**
        - Mean score < 2 or > 6 is considered abnormal
        - Normal range: 2-6
        """)

# Create Project Button
if st.button("Create a Project", key="create_project_btn", use_container_width=True):
    st.session_state.active_project = str(uuid.uuid4())
    st.session_state.projects[st.session_state.active_project] = {
        "name": f"Project {len(st.session_state.projects) + 1}"
    }

# Main Content Area
if st.session_state.active_project is None:
    st.info("Click 'Create a Project' to get started")
else:
    project = st.session_state.projects[st.session_state.active_project]
    st.header(f"Project: {project['name']}")
    
    # Mode Selection
    st.subheader("Select Analysis Mode")
    mode = st.radio("Choose mode:", 
                    ["General Behavior", "Autonomic and Sensorimotor Functions", 
                     "Reflex Capabilities", "Body Temperature", 
                     "Convulsive Behaviors and Excitability"],
                    horizontal=True)
    st.session_state.mode = mode
    
    # Two-column layout for worksheet and visualization
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Experiment Management
        st.subheader("Experiment Groups")
        
        # Add new experiment
        with st.expander("Add New Experiment", expanded=True):
            new_exp_name = st.text_input("Experiment Name")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Create Empty Worksheet") and new_exp_name:
                    if new_exp_name not in st.session_state.experiments:
                        st.session_state.experiments[new_exp_name] = True
                        # Initialize with proper key structure
                        worksheet_key = f"worksheet_{new_exp_name}_{mode}"
                        if mode == "Autonomic and Sensorimotor Functions":
                            observations = AUTONOMIC_OBSERVATIONS
                        elif mode == "Reflex Capabilities":
                            observations = REFLEX_OBSERVATIONS
                        elif mode == "Convulsive Behaviors and Excitability":
                            observations = CONVULSIVE_OBSERVATIONS
                        elif mode == "Body Temperature":
                            observations = ['body temperature']
                        else:
                            observations = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
                        
                        # Create initial data structure
                        times = [0, 15, 30, 45, 60]
                        data = []
                        for time in times:
                            for obs in observations:
                                row = {'time': time, 'observation': obs}
                                for i in range(1, 9):
                                    if mode == "Body Temperature":
                                        row[f'mouse_{i}'] = '37.0'
                                    else:
                                        row[f'mouse_{i}'] = '0'
                                data.append(row)
                        
                        st.session_state[worksheet_key] = pd.DataFrame(data)
                        st.success(f"Created experiment: {new_exp_name}")
                        st.rerun()
                    else:
                        st.error("Experiment name already exists")
            
            with col2:
                uploaded_file = st.file_uploader("Or Upload Data", type=["csv", "xlsx"])
                if st.button("Upload") and uploaded_file and new_exp_name:
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                        
                        # Validate columns
                        required_cols = ['time', 'observation'] + [f'mouse_{i}' for i in range(1, 9)]
                        if all(col in df.columns for col in required_cols):
                            worksheet_key = f"worksheet_{new_exp_name}_{mode}"
                            st.session_state[worksheet_key] = df
                            st.session_state.worksheet_data[new_exp_name] = df
                            st.session_state.experiments[new_exp_name] = True
                            st.success(f"Uploaded data for: {new_exp_name}")
                            st.rerun()
                        else:
                            st.error(f"File must contain columns: {', '.join(required_cols)}")
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
        
        # Select experiment to edit
        if st.session_state.experiments:
            selected_exp = st.selectbox("Select Experiment to Edit", 
                                       list(st.session_state.experiments.keys()))
            
            if selected_exp:
                st.info("💡 **Choose your editing mode**: Use 'Edit with Save Button' to batch your changes, or 'Auto-Save Mode' for instant saves.")
                
                # Display worksheet
                with st.container():
                    worksheet_df = create_worksheet(mode, selected_exp)
                
                # Export options (Save is now in the form)
                # Export current worksheet
                csv = worksheet_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Worksheet as CSV",
                    data=csv,
                    file_name=f"{selected_exp}_data.csv",
                    mime="text/csv"
                )
    
    with col_right:
        # Visualization Section
        st.subheader("Data Visualization")
        
        if st.session_state.experiments:
            # Select experiments to visualize with Select All option
            col_sel1, col_sel2 = st.columns([3, 1])
            
            with col_sel1:
                selected_for_viz = st.multiselect(
                    "Select experiments to visualize",
                    list(st.session_state.experiments.keys())
                )
            
            with col_sel2:
                if st.button("Select All", use_container_width=True):
                    st.session_state.selected_for_viz = list(st.session_state.experiments.keys())
                    st.rerun()
            
            # Use session state if "Select All" was clicked
            if 'selected_for_viz' in st.session_state:
                selected_for_viz = st.session_state.selected_for_viz
                # Clear the session state after using it
                del st.session_state.selected_for_viz
            
            if selected_for_viz:
                if mode == "General Behavior":
                    # Time selection
                    all_times = set()
                    for exp in selected_for_viz:
                        worksheet_key = f"worksheet_{exp}_{mode}"
                        if worksheet_key in st.session_state:
                            df = st.session_state[worksheet_key]
                            all_times.update(df['time'].unique())
                    
                    if all_times:
                        selected_time = st.selectbox("Select Time Point", sorted(list(all_times)))
                        
                        # Calculate means and stds for each experiment
                        overall_means = []
                        overall_stds = []
                        
                        for exp in selected_for_viz:
                            worksheet_key = f"worksheet_{exp}_{mode}"
                            if worksheet_key in st.session_state:
                                df = st.session_state[worksheet_key]
                                filtered = df[df['time'] == selected_time]
                                
                                if not filtered.empty:
                                    all_mean_scores = []
                                    for _, row in filtered.iterrows():
                                        mice_scores = [row[f'mouse_{i}'] for i in range(1, 9) if f'mouse_{i}' in row]
                                        mean_score = calculate_mean_score(mice_scores)
                                        if not pd.isna(mean_score):
                                            all_mean_scores.append(mean_score)
                                    
                                    if all_mean_scores:
                                        overall_means.append(np.mean(all_mean_scores))
                                        overall_stds.append(np.std(all_mean_scores))
                                    else:
                                        overall_means.append(0)
                                        overall_stds.append(0)
                                else:
                                    overall_means.append(0)
                                    overall_stds.append(0)
                        
                        # Create visualization
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        x_pos = range(len(selected_for_viz))
                        bars = ax.bar(
                            x_pos,
                            overall_means,
                            yerr=overall_stds,
                            color='#4cc9f0',  # Default blue color
                            capsize=5
                        )
                        
                        # Color bars red if abnormal (mean < 2 or mean > 6)
                        for i, mean in enumerate(overall_means):
                            if mean < 2 or mean > 6:  # Abnormal condition
                                bars[i].set_color('#ff6b6b')  # Red for abnormal
                        
                        ax.set_title(f"Mean ± Std Dev at Time {selected_time}")
                        ax.set_ylabel("Score (0-10 scale)")
                        ax.set_xticks(x_pos)
                        ax.set_xticklabels(selected_for_viz, rotation=45)
                        ax.set_ylim(0, 10)
                        
                        # Add horizontal lines for thresholds
                        ax.axhline(y=2, color='gray', linestyle='--', alpha=0.7)
                        ax.axhline(y=6, color='gray', linestyle='--', alpha=0.7)
                        ax.text(0.5, 2.1, 'Lower threshold', transform=ax.get_yaxis_transform(), color='gray')
                        ax.text(0.5, 6.1, 'Upper threshold', transform=ax.get_yaxis_transform(), color='gray')
                        
                        # Add value labels
                        for i, (mean, std) in enumerate(zip(overall_means, overall_stds)):
                            ax.text(i, mean + std + 0.2, f"{mean:.2f} ± {std:.2f}",
                                   ha='center', va='bottom')
                        
                        st.pyplot(fig)
                        
                        # Show abnormal episodes for General Behavior
                        st.subheader("🚨 Abnormal Episodes")
                        all_episodes = []
                        for exp in selected_for_viz:
                            worksheet_key = f"worksheet_{exp}_{mode}"
                            if worksheet_key in st.session_state:
                                df = st.session_state[worksheet_key]
                                episodes_df = process_data_with_episodes(df, mode)
                                if not episodes_df.empty:
                                    episodes_df['Experiment'] = exp
                                    all_episodes.append(episodes_df)
                        
                        if all_episodes:
                            combined_episodes = pd.concat(all_episodes, ignore_index=True)
                            st.dataframe(combined_episodes, use_container_width=True, hide_index=True)
                        else:
                            st.info("No abnormal episodes detected")
                
                elif mode == "Body Temperature":
                    st.info("**Normal Range**: 36-38°C. Values outside this range are considered abnormal.")
                    
                    for exp in selected_for_viz:
                        worksheet_key = f"worksheet_{exp}_{mode}"
                        if worksheet_key in st.session_state:
                            st.subheader(f"Experiment: {exp}")
                            
                            df = st.session_state[worksheet_key]
                            results_df = process_data_with_episodes(df, mode)
                            
                            if not results_df.empty:
                                st.markdown("**Abnormal Episodes**")
                                st.dataframe(results_df)
                            else:
                                st.info("No abnormal episodes detected (all temperatures within 36-38°C)")
                            
                            # Temperature timeline
                            times = sorted(df['time'].unique())
                            
                            if times:
                                mean_temps = []
                                std_temps = []
                                for time in times:
                                    time_df = df[df['time'] == time]
                                    if not time_df.empty:
                                        mice_scores = []
                                        for _, row in time_df.iterrows():
                                            scores = [row[f'mouse_{i}'] for i in range(1, 9) if f'mouse_{i}' in row]
                                            mice_scores.extend([parse_score(s) for s in scores if pd.notna(parse_score(s))])
                                        
                                        if mice_scores:
                                            mean_temps.append(np.mean(mice_scores))
                                            std_temps.append(np.std(mice_scores))
                                        else:
                                            mean_temps.append(37.0)
                                            std_temps.append(0)
                                
                                fig, ax = plt.subplots(figsize=(10, 6))
                                ax.errorbar(times, mean_temps, yerr=std_temps, 
                                           marker='o', linestyle='-', color='#1a3d6d',
                                           capsize=5, capthick=2)
                                
                                # Add normal range shading
                                ax.axhspan(36, 38, alpha=0.3, color='green', label='Normal range')
                                ax.axhline(y=36, color='red', linestyle='--', alpha=0.5)
                                ax.axhline(y=38, color='red', linestyle='--', alpha=0.5)
                                
                                ax.set_title(f"Body Temperature Over Time - {exp}")
                                ax.set_xlabel("Time (min)")
                                ax.set_ylabel("Temperature (°C)")
                                ax.set_ylim(35, 39)
                                ax.legend()
                                ax.grid(True, alpha=0.3)
                                
                                st.pyplot(fig)
                
                elif mode == "Convulsive Behaviors and Excitability":
                    st.info("**Abnormality Threshold**: Mean score > 2 is considered abnormal")
                    
                    for exp in selected_for_viz:
                        worksheet_key = f"worksheet_{exp}_{mode}"
                        if worksheet_key in st.session_state:
                            st.subheader(f"Experiment: {exp}")
                            
                            df = st.session_state[worksheet_key]
                            results_df = process_data_with_episodes(df, mode)
                            
                            if not results_df.empty:
                                st.markdown("**Abnormal Episodes (Onset/Offset)**")
                                st.dataframe(results_df)
                            else:
                                st.info("No abnormal episodes detected (all mean scores ≤ 2)")
                            
                            # Timeline visualization
                            times = sorted(df['time'].unique())
                            
                            if times:
                                cols = st.columns(3)
                                for i, obs in enumerate(CONVULSIVE_OBSERVATIONS):
                                    with cols[i % 3]:
                                        obs_df = df[df['observation'] == obs].sort_values('time')
                                        if not obs_df.empty:
                                            # Calculate mean scores
                                            mean_scores = []
                                            for _, row in obs_df.iterrows():
                                                mice_scores = [row[f'mouse_{i}'] for i in range(1, 9) if f'mouse_{i}' in row]
                                                mean_scores.append(calculate_mean_score(mice_scores))
                                            
                                            fig, ax = plt.subplots(figsize=(8, 3))
                                            ax.set_title(obs)
                                            ax.plot(obs_df['time'], mean_scores, 
                                                   marker='o', linestyle='-', color='#1a3d6d')
                                            ax.axhline(y=2, color='red', linestyle='--', alpha=0.5, 
                                                      label='Abnormal threshold')
                                            ax.set_xlabel("Time (min)")
                                            ax.set_ylabel("Mean Score")
                                            ax.set_ylim(0, 5)
                                            ax.legend()
                                            
                                            st.pyplot(fig)
                
                elif mode == "Autonomic and Sensorimotor Functions":
                    st.info("**Abnormality Threshold**: Mean score > 2 is considered abnormal")
                    
                    for exp in selected_for_viz:
                        worksheet_key = f"worksheet_{exp}_{mode}"
                        if worksheet_key in st.session_state:
                            st.subheader(f"Experiment: {exp}")
                            
                            df = st.session_state[worksheet_key]
                            results_df = process_data_with_episodes(df, mode)
                            
                            if not results_df.empty:
                                st.markdown("**Abnormal Episodes (Onset/Offset)**")
                                st.dataframe(results_df)
                            else:
                                st.info("No abnormal episodes detected (all mean scores ≤ 2)")
                            
                            # Timeline visualization
                            times = sorted(df['time'].unique())
                            
                            if times:
                                cols = st.columns(3)
                                for i, obs in enumerate(AUTONOMIC_OBSERVATIONS):
                                    with cols[i % 3]:
                                        obs_df = df[df['observation'] == obs].sort_values('time')
                                        if not obs_df.empty:
                                            # Calculate mean scores
                                            mean_scores = []
                                            for _, row in obs_df.iterrows():
                                                mice_scores = [row[f'mouse_{i}'] for i in range(1, 9) if f'mouse_{i}' in row]
                                                mean_scores.append(calculate_mean_score(mice_scores))
                                            
                                            fig, ax = plt.subplots(figsize=(8, 3))
                                            ax.set_title(obs)
                                            ax.plot(obs_df['time'], mean_scores, 
                                                   marker='o', linestyle='-', color='#1a3d6d')
                                            ax.axhline(y=2, color='red', linestyle='--', alpha=0.5, 
                                                      label='Abnormal threshold')
                                            ax.set_xlabel("Time (min)")
                                            ax.set_ylabel("Mean Score")
                                            ax.set_ylim(0, 5)
                                            ax.legend()
                                            
                                            st.pyplot(fig)
                
                else:  # Reflex Capabilities
                    st.info("**Abnormality Threshold**: Mean score > 2 is considered abnormal")
                    
                    for exp in selected_for_viz:
                        worksheet_key = f"worksheet_{exp}_{mode}"
                        if worksheet_key in st.session_state:
                            st.subheader(f"Experiment: {exp}")
                            
                            df = st.session_state[worksheet_key]
                            results_df = process_data_with_episodes(df, mode)
                            
                            if not results_df.empty:
                                st.markdown("**Abnormal Episodes (Onset/Offset)**")
                                st.dataframe(results_df)
                            else:
                                st.info("No abnormal episodes detected (all mean scores ≤ 2)")
                            
                            # Timeline visualization
                            times = sorted(df['time'].unique())
                            
                            if times:
                                cols = st.columns(3)
                                for i, obs in enumerate(REFLEX_OBSERVATIONS):
                                    with cols[i % 3]:
                                        obs_df = df[df['observation'] == obs].sort_values('time')
                                        if not obs_df.empty:
                                            # Calculate mean scores
                                            mean_scores = []
                                            for _, row in obs_df.iterrows():
                                                mice_scores = [row[f'mouse_{i}'] for i in range(1, 9) if f'mouse_{i}' in row]
                                                mean_scores.append(calculate_mean_score(mice_scores))
                                            
                                            fig, ax = plt.subplots(figsize=(8, 3))
                                            ax.set_title(obs)
                                            ax.plot(obs_df['time'], mean_scores, 
                                                   marker='o', linestyle='-', color='#1a3d6d')
                                            ax.axhline(y=2, color='red', linestyle='--', alpha=0.5, 
                                                      label='Abnormal threshold')
                                            ax.set_xlabel("Time (min)")
                                            ax.set_ylabel("Mean Score")
                                            ax.set_ylim(0, 5)
                                            ax.legend()
                                            
                                            st.pyplot(fig)
            else:
                st.info("Select experiments to visualize")
        else:
            st.info("Create an experiment to start visualization")

# Footer
st.markdown("---")
st.markdown("### About this Dashboard")
st.markdown("""
This interactive dashboard allows you to:
- Create projects and manage experiment groups
- Enter data for individual mice (up to 8 mice per experiment)
- **Fill worksheets with random data** for testing and demonstration
- **Select all experiments at once** for visualization
- Choose between manual save mode (batch edits) or auto-save mode (instant saves)
- Calculate mean scores across all mice automatically
- Visualize general behavior with normalized scores
- Analyze autonomic, sensorimotor, reflex, convulsive functions, and body temperature
- **Track onset and offset times** for all abnormal episodes
- Export and import data in CSV/Excel formats

**Scoring Thresholds:**
- **General Behavior**: 
  - Normal: 2-6
  - Abnormal: <2 or >6
- **Autonomic Functions**: 
  - Normal: ≤2 
  - Abnormal: >2
- **Reflex Capabilities**: 
  - Normal: ≤2 
  - Abnormal: >2
- **Convulsive Behaviors**: 
  - Normal: ≤2 
  - Abnormal: >2
- **Body Temperature**: 
  - Normal: 36-38°C
  - Abnormal: <36°C or >38°C


**Tips for Data Entry:**
- Use the "Edit with Save Button" tab to make multiple changes before saving
- Use the "Auto-Save Mode" tab for quick, single-cell edits
- Use "Fill Random Data" to quickly test the dashboard functionality
- Press Tab to move between cells horizontally
- Use Enter to move down to the next row
""")