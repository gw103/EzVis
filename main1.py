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
        .comparison-group {
            background-color: #d4edda;
            border: 2px solid #28a745;
        }
        </style>
    """, unsafe_allow_html=True)

set_custom_style()

# App header
st.title("FOB Test Analysis Dashboard")
st.markdown("Visualize and compare Functional Observational Battery (FOB) test results across multiple groups")

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
if 'comparison_groups' not in st.session_state:
    st.session_state.comparison_groups = {}

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

# Function to calculate mean score from animal data
def calculate_mean_score(animal_scores):
    """Calculate mean score from individual animal scores"""
    parsed_scores = [parse_score(score) for score in animal_scores if pd.notna(score)]
    if parsed_scores:
        return np.mean(parsed_scores)
    return np.nan

# Function to generate random data
def generate_random_data(mode, times, num_animals=8, animal_type="mouse"):
    """Generate random data based on the mode"""
    if mode == "Body Temperature":
        # Normal temp range varies by animal type
        if animal_type == "rat":
            base_temp_mean = 37.5
        elif animal_type == "mouse":
            base_temp_mean = 37.0
        else:
            base_temp_mean = 37.2  # Default for custom animals
            
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            data['time'].append(time)
            data['observation'].append('body temperature')
            for i in range(1, num_animals + 1):
                # Generate realistic body temperature
                base_temp = np.random.normal(base_temp_mean, 0.5)
                # Add some time-based variation
                if time > 30:
                    base_temp += np.random.normal(0.2, 0.1)
                data[f'{animal_type}_{i}'].append(f"{base_temp:.1f}")
        
        return pd.DataFrame(data)
    
    elif mode == "Convulsive Behaviors and Excitability":
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in CONVULSIVE_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_animals + 1):
                    # 0/4 system with modifiers
                    if np.random.random() < 0.7:  # 70% normal
                        base = 0
                    else:
                        base = 4
                    modifier = np.random.choice(['', '+', '-', '++', '--'], p=[0.5, 0.2, 0.2, 0.05, 0.05])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    elif mode == "Autonomic and Sensorimotor Functions":
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in AUTONOMIC_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_animals + 1):
                    # 0/4 system
                    if np.random.random() < 0.75:  # 75% normal
                        base = 0
                    else:
                        base = 4
                    modifier = np.random.choice(['', '+', '-'], p=[0.6, 0.2, 0.2])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    elif mode == "Reflex Capabilities":
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in REFLEX_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_animals + 1):
                    # 0/4 system
                    if np.random.random() < 0.8:  # 80% normal
                        base = 0
                    else:
                        base = 4
                    modifier = np.random.choice(['', '+', '-', '++', '--'], p=[0.5, 0.2, 0.2, 0.05, 0.05])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    else:  # General Behavior
        behaviors = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for behavior in behaviors:
                data['time'].append(time)
                data['observation'].append(behavior)
                for i in range(1, num_animals + 1):
                    # 0/4/8 system - generate scores mostly in normal range
                    if np.random.random() < 0.7:  # 70% normal range
                        base = 4
                    else:
                        base = np.random.choice([0, 8])
                    modifier = np.random.choice(['', '+', '-', '++', '--'], p=[0.5, 0.2, 0.2, 0.05, 0.05])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

# Function to process data with onset/offset tracking
def process_data_with_episodes(df, mode, animal_type="mouse", num_animals=8):
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
        peak_score = 0
        
        for _, row in obs_df.iterrows():
            # Calculate mean score from all animals
            animal_scores = [row[f'{animal_type}_{i}'] for i in range(1, num_animals + 1) 
                           if f'{animal_type}_{i}' in row]
            mean_score = calculate_mean_score(animal_scores)
            
            # Track peak score
            if not pd.isna(mean_score) and mean_score > peak_score:
                peak_score = mean_score
            
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
                peak_score = mean_score
            elif not is_abnormal and in_episode:
                # End of abnormal episode
                results.append({
                    'Observation': obs,
                    'Onset Time': onset_time,
                    'Offset Time': row['time'],
                    'Duration': row['time'] - onset_time,
                    'Peak Score': peak_score
                })
                in_episode = False
                onset_time = None
                peak_score = 0
        
        # Handle ongoing episode
        if in_episode and onset_time is not None:
            results.append({
                'Observation': obs,
                'Onset Time': onset_time,
                'Offset Time': obs_df['time'].max(),
                'Duration': obs_df['time'].max() - onset_time,
                'Peak Score': peak_score
            })
    
    return pd.DataFrame(results)

# Function to generate template data
def create_template(mode="General Behavior", num_animals=8, animal_type="mouse"):
    """Create template with individual animal columns"""
    if mode == "Body Temperature":
        times = [0, 15, 30, 45, 60]
        data = {
            'time': [],
            'observation': []
        }
        # Add animal columns
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            data['time'].append(time)
            data['observation'].append('body temperature')
            for i in range(1, num_animals + 1):
                # Normal temperature range
                temp = np.random.normal(37.0, 0.2)
                data[f'{animal_type}_{i}'].append(f"{temp:.1f}")
        
        return pd.DataFrame(data)
    
    elif mode == "Convulsive Behaviors and Excitability":
        times = [0, 15, 30]
        data = {
            'time': [],
            'observation': []
        }
        # Add animal columns
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in CONVULSIVE_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                # Add scores for each animal
                for i in range(1, num_animals + 1):
                    # 0/4 system with modifiers
                    base = 0
                    modifier = random.choice(['', '+', '-'])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    
    elif mode == "Autonomic and Sensorimotor Functions":
        times = [0, 15, 30]
        data = {
            'time': [],
            'observation': []
        }
        # Add animal columns
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in AUTONOMIC_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                # Add scores for each animal
                for i in range(1, num_animals + 1):
                    # Start with normal (0) scores
                    base = 0
                    modifier = random.choice(['', '+', '-'])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    elif mode == "Reflex Capabilities":
        times = [0, 15, 30]
        data = {
            'time': [],
            'observation': []
        }
        # Add animal columns
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in REFLEX_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                # Add scores for each animal
                for i in range(1, num_animals + 1):
                    # 0/4 system with modifiers
                    base = random.choice([0, 4])
                    modifier = random.choice(['', '+', '-', '++', '--'])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    else:  # General Behavior
        behaviors = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
        times = [0, 15, 30]
        
        data = {
            'time': [],
            'observation': []
        }
        # Add animal columns
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for behavior in behaviors:
                data['time'].append(time)
                data['observation'].append(behavior)
                
                # Add scores for each animal
                for i in range(1, num_animals + 1):
                    # 0/4/8 system with modifiers
                    base = random.choice([0, 4, 8])
                    modifier = random.choice(['', '+', '-', '++', '--'])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

# Function to create worksheet interface
def create_worksheet(mode, experiment_name, project_info):
    """Create an editable worksheet for data entry"""
    st.subheader(f"Data Entry Worksheet - {experiment_name}")
    
    # Get animal info from project
    animal_type = project_info.get('animal_type', 'mouse')
    if animal_type == 'custom':
        animal_type = project_info.get('custom_animal_name', 'animal')
    num_animals = project_info.get('num_animals', 8)
    
    # Show if this is a comparison group
    if experiment_name in st.session_state.comparison_groups.get(st.session_state.active_project, []):
        st.success(f"🏆 This is a COMPARISON GROUP")
    
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
                for i in range(1, num_animals + 1):
                    if mode == "Body Temperature":
                        row[f'{animal_type}_{i}'] = '37.0'
                    else:
                        row[f'{animal_type}_{i}'] = '0'
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
    
    # Add animal columns configuration
    for i in range(1, num_animals + 1):
        if mode == "Body Temperature":
            column_config[f'{animal_type}_{i}'] = st.column_config.TextColumn(
                f'{animal_type.capitalize()} {i}',
                help=f"Temperature for {animal_type} {i} in Celsius (e.g., 37.2)",
                max_chars=5
            )
        else:
            column_config[f'{animal_type}_{i}'] = st.column_config.TextColumn(
                f'{animal_type.capitalize()} {i}',
                help=f"Score for {animal_type} {i}. Use appropriate scoring system for the mode",
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
                random_df = generate_random_data(mode, times, num_animals, animal_type)
                st.session_state[worksheet_key] = random_df
                st.rerun()
            
            if add_timestep:
                # Add new timestep with all observations
                new_rows = []
                observations = edited_df['observation'].unique()
                for obs in observations:
                    new_row = {'time': new_timestep, 'observation': obs}
                    for i in range(1, num_animals + 1):
                        if mode == "Body Temperature":
                            new_row[f'{animal_type}_{i}'] = '37.0'
                        else:
                            new_row[f'{animal_type}_{i}'] = '0'
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
                random_df = generate_random_data(mode, times, num_animals, animal_type)
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
                    for i in range(1, num_animals + 1):
                        if mode == "Body Temperature":
                            new_row[f'{animal_type}_{i}'] = '37.0'
                        else:
                            new_row[f'{animal_type}_{i}'] = '0'
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
        animal_scores = [row[f'{animal_type}_{i}'] for i in range(1, num_animals + 1) 
                        if f'{animal_type}_{i}' in row]
        mean_score = calculate_mean_score(animal_scores)
        
        # Count how many animals have valid scores
        valid_scores = sum(1 for score in animal_scores if pd.notna(score) and score != '')
        
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
            f'Valid {animal_type.capitalize()}s': f"{valid_scores}/{num_animals}",
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
        episodes_df = process_data_with_episodes(current_df, mode, animal_type, num_animals)
        if not episodes_df.empty:
            st.dataframe(episodes_df, use_container_width=True, hide_index=True)
        else:
            st.info("No abnormal episodes detected")
    
    return current_df

# Template Section
with st.expander("📝 Download Data Templates", expanded=False):
    st.markdown("""
    ### Data Templates
    Download these templates to get started with the correct format for your experiments.
    """)
    
    # Mode selection for template
    template_mode = st.radio("Select Template Type", 
                            ["General Behavior", "Autonomic and Sensorimotor Functions", 
                             "Reflex Capabilities", "Body Temperature", 
                             "Convulsive Behaviors and Excitability"],
                            index=0,
                            horizontal=True)
    
    # Animal configuration for template
    col_temp1, col_temp2, col_temp3 = st.columns(3)
    with col_temp1:
        template_animal = st.selectbox("Template Animal Type", ["Mouse", "Rat", "Custom"], key="template_animal")
    with col_temp2:
        if template_animal == "Custom":
            template_custom_name = st.text_input("Custom Animal Name", value="animal", key="template_custom")
        else:
            template_custom_name = None
    with col_temp3:
        template_num_animals = st.number_input("Animals per Group", min_value=1, max_value=20, value=8, key="template_num")
    
    # Determine actual animal type for template
    if template_animal == "Mouse":
        template_animal_type = "mouse"
    elif template_animal == "Rat":
        template_animal_type = "rat"
    else:
        template_animal_type = template_custom_name or "animal"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CSV Template")
        template_csv = create_template(template_mode, template_num_animals, template_animal_type)
        st.dataframe(template_csv.head(5))
        
        # Convert to CSV
        csv = template_csv.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Download CSV Template",
            data=csv,
            file_name=f"fob_template_{template_mode.replace(' ', '_')}_{template_animal_type}.csv",
            mime="text/csv",
            help="Download CSV template for experiment data"
        )
    
    with col2:
        st.subheader("Excel Template")
        template_excel = create_template(template_mode, template_num_animals, template_animal_type)
        st.dataframe(template_excel.head(5))
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            template_excel.to_excel(writer, index=False, sheet_name='FOB Data')
        
        st.download_button(
            label="Download Excel Template",
            data=output.getvalue(),
            file_name=f"fob_template_{template_mode.replace(' ', '_')}_{template_animal_type}.xlsx",
            mime="application/vnd.ms-excel",
            help="Download Excel template for experiment data"
        )
    
    st.info(f"""
    **Template Format Requirements:**
    - **time**: Time point in minutes (e.g., 0, 5, 10, 15)
    - **observation**: Name of the behavior being observed
    - **{template_animal_type}_1 to {template_animal_type}_{template_num_animals}**: Individual scores for each {template_animal_type}
        - General Behavior: 0/4/8 with optional modifiers (e.g., "4++", "8-")
        - Autonomic/Reflex/Convulsive Functions: 0/4 with optional modifiers (e.g., "4+", "0-")
        - Body Temperature: Numerical values in Celsius (e.g., "37.2")
    """)

# Project Creation Section
if st.button("🆕 Create New Project", key="create_project_btn", use_container_width=True, type="primary"):
    st.session_state.show_project_creation = True

if 'show_project_creation' in st.session_state and st.session_state.show_project_creation:
    with st.container():
        st.subheader("📋 Configure New Project")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            project_name = st.text_input("Project Name", value=f"Project {len(st.session_state.projects) + 1}")
            animal_type = st.selectbox("Animal Type", ["Mouse", "Rat", "Custom"])
        
        with col2:
            if animal_type == "Custom":
                custom_animal_name = st.text_input("Custom Animal Name", value="animal")
            else:
                custom_animal_name = None
            num_animals = st.number_input("Number of animals per group", min_value=1, max_value=20, value=8)
        
        with col3:
            num_groups = st.number_input("Number of groups to create", min_value=1, max_value=10, value=5)
            
        # Create project button
        if st.button("✅ Create Project", use_container_width=True):
            project_id = str(uuid.uuid4())
            st.session_state.active_project = project_id
            st.session_state.projects[project_id] = {
                "name": project_name,
                "animal_type": animal_type.lower(),
                "custom_animal_name": custom_animal_name,
                "num_animals": num_animals,
                "num_groups": num_groups
            }
            
            # Create groups
            for i in range(1, num_groups + 1):
                group_name = f"{project_name}_Group_{i}"
                st.session_state.experiments[group_name] = True
            
            st.session_state.show_project_creation = False
            st.success(f"✅ Created project '{project_name}' with {num_groups} groups!")
            st.rerun()
        
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_project_creation = False
            st.rerun()

# Main Content Area
if st.session_state.active_project is None:
    st.info("👆 Click 'Create New Project' to get started")
else:
    project = st.session_state.projects[st.session_state.active_project]
    animal_display = project['animal_type'].capitalize()
    if project['animal_type'] == 'custom':
        animal_display = project.get('custom_animal_name', 'animal').capitalize()
    
    st.header(f"🔬 {project['name']} - {animal_display} ({project['num_animals']} per group)")
    
    # Mode Selection
    st.subheader("Select Analysis Mode")
    mode = st.radio("Choose mode:", 
                    ["General Behavior", "Autonomic and Sensorimotor Functions", 
                     "Reflex Capabilities", "Body Temperature", 
                     "Convulsive Behaviors and Excitability"],
                    horizontal=True)
    st.session_state.mode = mode
    
    # Get project-specific groups
    project_groups = [exp for exp in st.session_state.experiments.keys() 
                     if exp.startswith(project['name'])]
    
    # Select comparison group
    if project_groups:
        with st.expander("🏆 Select Comparison Group", expanded=True):
            comparison_group = st.selectbox(
                "Which group should be the comparison/control group?",
                project_groups,
                index=0
            )
            
            if st.button("Set as Comparison Group"):
                if st.session_state.active_project not in st.session_state.comparison_groups:
                    st.session_state.comparison_groups[st.session_state.active_project] = []
                st.session_state.comparison_groups[st.session_state.active_project] = [comparison_group]
                st.success(f"✅ {comparison_group} set as comparison group")
                st.rerun()
            
            # Show current comparison group
            if st.session_state.active_project in st.session_state.comparison_groups:
                current_comp = st.session_state.comparison_groups[st.session_state.active_project]
                if current_comp:
                    st.info(f"Current comparison group: **{current_comp[0]}**")
    
    # Two-column layout for worksheet and visualization
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Group Management
        st.subheader("Experiment Groups")
        
        # Select group to edit
        if project_groups:
            selected_exp = st.selectbox("Select Group to Edit", project_groups)
            
            if selected_exp:
                st.info("💡 **Choose your editing mode**: Use 'Edit with Save Button' to batch your changes, or 'Auto-Save Mode' for instant saves.")
                
                # Display worksheet
                with st.container():
                    worksheet_df = create_worksheet(mode, selected_exp, project)
                
                # Export options
                csv = worksheet_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Worksheet as CSV",
                    data=csv,
                    file_name=f"{selected_exp}_data.csv",
                    mime="text/csv"
                )
    
    with col_right:
        # Visualization and Reporting Section
        st.subheader("Data Analysis & Reporting")
        
        if project_groups:
            # Select groups to analyze
            col_sel1, col_sel2 = st.columns([3, 1])
            
            with col_sel1:
                selected_for_viz = st.multiselect(
                    "Select groups to analyze",
                    project_groups,
                    default=project_groups
                )
            
            with col_sel2:
                if st.button("Select All", use_container_width=True):
                    st.session_state.selected_for_viz = project_groups
                    st.rerun()
            
            # Use session state if "Select All" was clicked
            if 'selected_for_viz' in st.session_state:
                selected_for_viz = st.session_state.selected_for_viz
                del st.session_state.selected_for_viz
            
            if selected_for_viz:
                # Generate comprehensive report
                st.markdown("### 📊 Comparative Analysis Report")
                
                # Collect all abnormal episodes across groups
                all_abnormal_episodes = {}
                comparison_data = []
                
                # Get animal info
                animal_type = project.get('animal_type', 'mouse')
                if animal_type == 'custom':
                    animal_type = project.get('custom_animal_name', 'animal')
                num_animals = project.get('num_animals', 8)
                
                # Identify comparison group
                comp_group = None
                if st.session_state.active_project in st.session_state.comparison_groups:
                    comp_groups = st.session_state.comparison_groups[st.session_state.active_project]
                    if comp_groups and comp_groups[0] in selected_for_viz:
                        comp_group = comp_groups[0]
                
                # Analyze each group
                for exp in selected_for_viz:
                    worksheet_key = f"worksheet_{exp}_{mode}"
                    if worksheet_key in st.session_state:
                        df = st.session_state[worksheet_key]
                        
                        # Get abnormal episodes
                        episodes_df = process_data_with_episodes(df, mode, animal_type, num_animals)
                        if not episodes_df.empty:
                            all_abnormal_episodes[exp] = episodes_df
                        
                        # Collect comparison data
                        group_data = {
                            'Group': exp,
                            'Is Comparison': '✓' if exp == comp_group else '',
                            'Total Abnormal Episodes': len(episodes_df) if not episodes_df.empty else 0,
                            'Affected Observations': ', '.join(episodes_df['Observation'].unique()) if not episodes_df.empty else 'None'
                        }
                        comparison_data.append(group_data)
                
                # Display comparison summary
                st.markdown("#### 📋 Group Summary")
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(
                    comparison_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Is Comparison": st.column_config.TextColumn("Comparison Group", width="small")
                    }
                )
                
                # Display detailed abnormal episodes by group
                st.markdown("#### 🚨 Abnormal Episodes by Group")
                
                if all_abnormal_episodes:
                    # Create tabs for each group with episodes
                    tabs = st.tabs([f"{group} ({len(episodes)})" for group, episodes in all_abnormal_episodes.items()])
                    
                    for i, (group, episodes) in enumerate(all_abnormal_episodes.items()):
                        with tabs[i]:
                            if group == comp_group:
                                st.info("🏆 This is the comparison group")
                            
                            # Add group name to episodes
                            episodes['Group'] = group
                            
                            # Display episodes
                            st.dataframe(
                                episodes[['Observation', 'Onset Time', 'Offset Time', 'Duration', 'Peak Score']],
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Summary statistics for this group
                            st.markdown("**Summary:**")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Episodes", len(episodes))
                            with col2:
                                st.metric("Avg Duration", f"{episodes['Duration'].mean():.1f} min" if len(episodes) > 0 else "N/A")
                            with col3:
                                st.metric("Max Peak Score", f"{episodes['Peak Score'].max():.2f}" if len(episodes) > 0 else "N/A")
                else:
                    st.success("✅ No abnormal episodes detected in any group!")
                
                # Comparative visualization
                if mode == "General Behavior":
                    st.markdown("#### 📈 Comparative Visualization")
                    
                    # Time selection
                    all_times = set()
                    for exp in selected_for_viz:
                        worksheet_key = f"worksheet_{exp}_{mode}"
                        if worksheet_key in st.session_state:
                            df = st.session_state[worksheet_key]
                            all_times.update(df['time'].unique())
                    
                    if all_times:
                        selected_time = st.selectbox("Select Time Point for Comparison", sorted(list(all_times)))
                        
                        # Calculate means and stds for each group
                        overall_means = []
                        overall_stds = []
                        group_names = []
                        
                        for exp in selected_for_viz:
                            worksheet_key = f"worksheet_{exp}_{mode}"
                            if worksheet_key in st.session_state:
                                df = st.session_state[worksheet_key]
                                filtered = df[df['time'] == selected_time]
                                
                                if not filtered.empty:
                                    all_mean_scores = []
                                    for _, row in filtered.iterrows():
                                        animal_scores = [row[f'{animal_type}_{i}'] for i in range(1, num_animals + 1) 
                                                       if f'{animal_type}_{i}' in row]
                                        mean_score = calculate_mean_score(animal_scores)
                                        if not pd.isna(mean_score):
                                            all_mean_scores.append(mean_score)
                                    
                                    if all_mean_scores:
                                        overall_means.append(np.mean(all_mean_scores))
                                        overall_stds.append(np.std(all_mean_scores))
                                        group_names.append(exp)
                        
                        if overall_means:
                            # Create visualization
                            fig, ax = plt.subplots(figsize=(12, 6))
                            
                            x_pos = range(len(group_names))
                            bars = ax.bar(
                                x_pos,
                                overall_means,
                                yerr=overall_stds,
                                capsize=5
                            )
                            
                            # Color bars based on status
                            for i, (mean, group) in enumerate(zip(overall_means, group_names)):
                                if group == comp_group:
                                    bars[i].set_color('#28a745')  # Green for comparison group
                                elif mean < 2 or mean > 6:  # Abnormal
                                    bars[i].set_color('#ff6b6b')  # Red for abnormal
                                else:
                                    bars[i].set_color('#4cc9f0')  # Blue for normal
                            
                            ax.set_title(f"Group Comparison at Time {selected_time} min")
                            ax.set_ylabel("Score (0-10 scale)")
                            ax.set_xticks(x_pos)
                            ax.set_xticklabels([g.split('_')[-1] for g in group_names], rotation=45)
                            ax.set_ylim(0, 10)
                            
                            # Add thresholds
                            ax.axhline(y=2, color='gray', linestyle='--', alpha=0.7)
                            ax.axhline(y=6, color='gray', linestyle='--', alpha=0.7)
                            
                            # Add value labels
                            for i, (mean, std) in enumerate(zip(overall_means, overall_stds)):
                                ax.text(i, mean + std + 0.2, f"{mean:.2f}",
                                       ha='center', va='bottom')
                            
                            # Add legend
                            from matplotlib.patches import Patch
                            legend_elements = [
                                Patch(facecolor='#28a745', label='Comparison Group'),
                                Patch(facecolor='#4cc9f0', label='Normal'),
                                Patch(facecolor='#ff6b6b', label='Abnormal')
                            ]
                            ax.legend(handles=legend_elements, loc='upper right')
                            
                            st.pyplot(fig)
                
                # Export comprehensive report
                st.markdown("#### 💾 Export Report")
                
                # Prepare report data
                report_data = {
                    'Project': project['name'],
                    'Animal Type': animal_display,
                    'Animals per Group': project['num_animals'],
                    'Analysis Mode': mode,
                    'Total Groups': len(selected_for_viz),
                    'Comparison Group': comp_group or 'Not set',
                    'Report Generated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Create detailed report
                report_lines = [
                    f"FOB Test Analysis Report",
                    f"=" * 50,
                    f"Project: {report_data['Project']}",
                    f"Animal Type: {report_data['Animal Type']}",
                    f"Animals per Group: {report_data['Animals per Group']}",
                    f"Analysis Mode: {report_data['Analysis Mode']}",
                    f"Total Groups Analyzed: {report_data['Total Groups']}",
                    f"Comparison Group: {report_data['Comparison Group']}",
                    f"Report Generated: {report_data['Report Generated']}",
                    f"",
                    f"SUMMARY OF ABNORMAL EPISODES",
                    f"-" * 50
                ]
                
                # Add group summaries
                for group_data in comparison_data:
                    report_lines.append(f"\nGroup: {group_data['Group']}")
                    if group_data['Is Comparison']:
                        report_lines.append("(COMPARISON GROUP)")
                    report_lines.append(f"Total Abnormal Episodes: {group_data['Total Abnormal Episodes']}")
                    report_lines.append(f"Affected Observations: {group_data['Affected Observations']}")
                
                # Add detailed episodes
                if all_abnormal_episodes:
                    report_lines.append(f"\n\nDETAILED ABNORMAL EPISODES")
                    report_lines.append(f"=" * 50)
                    
                    for group, episodes in all_abnormal_episodes.items():
                        report_lines.append(f"\n{group}:")
                        report_lines.append(f"-" * 30)
                        for _, episode in episodes.iterrows():
                            report_lines.append(f"  Observation: {episode['Observation']}")
                            report_lines.append(f"  Onset: {episode['Onset Time']} min")
                            report_lines.append(f"  Offset: {episode['Offset Time']} min")
                            report_lines.append(f"  Duration: {episode['Duration']} min")
                            report_lines.append(f"  Peak Score: {episode['Peak Score']:.2f}")
                            report_lines.append("")
                
                report_text = "\n".join(report_lines)
                
                st.download_button(
                    label="📄 Download Complete Report",
                    data=report_text,
                    file_name=f"{project['name']}_FOB_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            else:
                st.info("Select groups to analyze")
        else:
            st.info("No groups created yet")

# Footer
st.markdown("---")
st.markdown("### About this Dashboard")
st.markdown(f"""
This enhanced interactive dashboard allows you to:
- **Create projects** with customizable animal types (mice, rats, or custom)
- **Specify the number of animals** per group (flexible group sizes)
- **Create multiple groups at once** (default: 5 groups per project)
- **Designate a comparison/control group** for reference
- Enter data for individual animals with customizable group sizes
- **Comprehensive reporting** of abnormal parameters across all groups
- **Track onset and offset times** for all abnormal episodes
- **Compare groups visually** with highlighted comparison group
- Export detailed reports with all abnormal episodes

**Scoring Thresholds:**
- **General Behavior**: Normal: 2-6, Abnormal: <2 or >6
- **Autonomic Functions**: Normal: ≤2, Abnormal: >2
- **Reflex Capabilities**: Normal: ≤2, Abnormal: >2
- **Convulsive Behaviors**: Normal: ≤2, Abnormal: >2
- **Body Temperature**: Normal: 36-38°C, Abnormal: <36°C or >38°C

**Tips:**
- Create multiple groups at project creation for efficient setup
- Set one group as the comparison group for reference
- Use the comprehensive report to identify differences between groups
- Export reports for documentation and further analysis
""")