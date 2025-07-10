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
        .css-1d391kg {
            padding-top: 1rem;
            padding-bottom: 1rem;
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
        .experiment-card {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
            background-color: #f9f9f9;
        }
        .template-section {
            background-color: #e8f4ff;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
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

# Constants for autonomic mode
AUTONOMIC_OBSERVATIONS = [
    'piloerection',
    'skin color',
    'cyanosis',
    'respiratory activity',
    'irregular breathing',
    'stertorous'
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
    st.session_state.mode = "Individual Behavior"
if 'fob_plot_type' not in st.session_state:
    st.session_state.fob_plot_type = None
if 'selected_time' not in st.session_state:
    st.session_state.selected_time = 0
if 'selected_behavior' not in st.session_state:
    st.session_state.selected_behavior = ""
if 'global_min' not in st.session_state:
    st.session_state.global_min = 0
if 'global_max' not in st.session_state:
    st.session_state.global_max = 10

# Helper function to parse the scoring system
def parse_score(score_str):
    """Parse 0/4/8 scoring system with +/- modifiers"""
    if pd.isna(score_str):
        return np.nan
    
    # Convert to string if it's a number
    if isinstance(score_str, (int, float)):
        return float(score_str)
    
    # Extract base score and modifiers
    match = re.match(r'(\d+)([\+\-]*)', str(score_str))
    if not match:
        return np.nan
    
    base_score = int(match.group(1))
    modifiers = match.group(2)
    
    # Calculate numerical value
    value = base_score
    if modifiers:
        modifier_value = len(modifiers) * (1 if '+' in modifiers else -1)
        value += modifier_value
    
    return value

# Function to extract base score for autonomic mode
def extract_base_score(score_str):
    """Extract base score (0 or 4) for autonomic mode"""
    if pd.isna(score_str):
        return 0
    if isinstance(score_str, str):
        match = re.match(r'(\d+)', str(score_str))
        if match:
            base = int(match.group(1))
            return base
        return 0
    elif isinstance(score_str, (int, float)):
        return 4 if score_str >= 4 else 0
    return 0

# Function to generate template data
def create_template(mode="Individual Behavior"):
    if mode == "Autonomic and Sensorimotor Functions":
        times = [0, 15, 30]
        data = {
            'time': [],
            'observation': [],
            'score': []
        }
        
        for time in times:
            for obs in AUTONOMIC_OBSERVATIONS:
                data['time'].append(time)
                data['observation'].append(obs)
                # Start with normal (0) scores
                base = 0
                modifier = random.choice(['', '+', '-'])
                data['score'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)
    else:
        behaviors = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
        times = [0, 15, 30]
        
        data = {
            'time': [],
            'observation': [],
            'score': []
        }
        
        for time in times:
            for behavior in behaviors:
                data['time'].append(time)
                data['observation'].append(behavior)
                
                # Mix of numerical and 0/4/8 scores
                if random.random() > 0.5:
                    # Numerical score (0-10)
                    data['score'].append(round(random.uniform(0, 10), 1))
                else:
                    # 0/4/8 system with modifiers
                    base = random.choice([0, 4, 8])
                    modifier = random.choice(['', '+', '-', '++', '--'])
                    data['score'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

# Function to generate autonomic data
def generate_autonomic_data(num_timesteps=5):
    """Generate autonomic data with at least 5 timesteps"""
    times = list(range(0, num_timesteps * 5, 5))  # 0, 5, 10, 15, 20 minutes
    data = {
        'time': [],
        'observation': [],
        'score': []
    }
    
    for obs in AUTONOMIC_OBSERVATIONS:
        # Start with normal state
        scores = ['0'] * num_timesteps
        
        # Determine if this observation will have an abnormal episode
        if random.random() > 0.3:  # 70% chance of having an abnormal episode
            # Randomly select start and end times for abnormality
            start_idx = random.randint(1, num_timesteps-2)
            end_idx = random.randint(start_idx+1, num_timesteps-1)
            
            # Set abnormal scores
            for i in range(start_idx, end_idx):
                base = 4
                modifier = random.choice(['', '+', '-', '++', '--'])
                scores[i] = f"{base}{modifier}"
                
                # Add transition scores
                if i == start_idx and random.random() > 0.5:
                    scores[i-1] = random.choice(['0+', '0++', '4-', '4--'])
                if i == end_idx-1 and random.random() > 0.5:
                    scores[i+1] = random.choice(['0+', '0++', '4-', '4--'])
        
        # Add to data
        for i, time_val in enumerate(times):
            data['time'].append(time_val)
            data['observation'].append(obs)
            data['score'].append(scores[i])
    
    return pd.DataFrame(data)

# Function to generate random experiment data
def generate_random_experiment():
    if st.session_state.mode == "Autonomic and Sensorimotor Functions":
        return generate_autonomic_data(num_timesteps=random.randint(5, 8))
    else:
        behaviors = ['Locomotion', 'Rearing', 'Grooming', 'Sniffing', 'Freezing']
        times = [0, 15, 30, 45, 60]
        
        data = {
            'time': [],
            'observation': [],
            'score': []
        }
        
        for time in times:
            for behavior in behaviors:
                if random.random() > 0.3:  # Skip some data points randomly
                    data['time'].append(time)
                    data['observation'].append(behavior)
                    
                    # Randomly choose score format
                    if random.random() > 0.5:
                        # Numerical score (0-10)
                        data['score'].append(round(random.uniform(0, 10), 1))
                    else:
                        # 0/4/8 system with modifiers
                        base = random.choice([0, 4, 8])
                        modifier = random.choice(['', '+', '-', '++', '--'])
                        data['score'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

# Function to normalize data to 0-10 scale
def normalize_data(df):
    if df.empty:
        return df
    
    # Get global min/max if not set
    if 'global_min' not in st.session_state or 'global_max' not in st.session_state:
        all_scores = []
        for exp in st.session_state.experiments.values():
            exp['numerical_score'] = exp['score'].apply(parse_score)
            all_scores.extend(exp['numerical_score'].dropna().tolist())
        
        if all_scores:
            st.session_state.global_min = min(all_scores)
            st.session_state.global_max = max(all_scores)
        else:
            st.session_state.global_min = 0
            st.session_state.global_max = 10
    
    # Apply normalization
    df['normalized_score'] = df['numerical_score'].apply(
        lambda x: (x - st.session_state.global_min) * 10 / 
                  (st.session_state.global_max - st.session_state.global_min)
    )
    return df

# Function to process autonomic data
def process_autonomic_data(df):
    """Process autonomic data to find start and end times for abnormalities"""
    # Extract base scores
    df['base_score'] = df['score'].apply(extract_base_score)
    
    # Get all unique times
    all_times = sorted(df['time'].unique())
    if not all_times:
        return pd.DataFrame()
    
    results = []
    
    for obs in AUTONOMIC_OBSERVATIONS:
        obs_df = df[df['observation'] == obs].sort_values('time')
        
        if obs_df.empty:
            # No data for this observation
            results.append({
                'Observation': obs,
                'Start Time': 0,
                'End Time': all_times[-1] if all_times else 0,
                'Duration': all_times[-1] if all_times else 0
            })
            continue
        
        start_time = None
        end_time = None
        in_episode = False
        
        # Track through time points
        for _, row in obs_df.iterrows():
            if row['base_score'] == 4 and not in_episode:
                # Start of an abnormal episode
                start_time = row['time']
                in_episode = True
            elif row['base_score'] == 0 and in_episode:
                # End of an abnormal episode
                end_time = row['time']
                in_episode = False
                # Add episode to results
                results.append({
                    'Observation': obs,
                    'Start Time': start_time,
                    'End Time': end_time,
                    'Duration': end_time - start_time
                })
                start_time = None
                end_time = None
        
        # Handle ongoing episode at the end
        if in_episode and start_time is not None:
            results.append({
                'Observation': obs,
                'Start Time': start_time,
                'End Time': all_times[-1],
                'Duration': all_times[-1] - start_time
            })
        
        # Handle no abnormalities
        if start_time is None and end_time is None:
            results.append({
                'Observation': obs,
                'Start Time': 0,
                'End Time': all_times[-1],
                'Duration': 0
            })
    
    return pd.DataFrame(results)

# Template Section
with st.expander("📝 Download Data Templates", expanded=True):
    st.markdown("""
    ### Data Templates
    Download these templates to get started with the correct format for your experiments.
    Each template includes sample data that demonstrates the required format.
    """)
    
    # Mode selection for template
    template_mode = st.radio("Select Template Type", 
                            ["Individual Behavior", "General Behavior", "Autonomic and Sensorimotor Functions"],
                            index=0,
                            horizontal=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CSV Template")
        template_csv = create_template(template_mode)
        st.dataframe(template_csv.head(8))
        
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
        st.dataframe(template_excel.head(8))
        
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
    - **score**: Can be either:
        - Numerical value (e.g., 3.5)
        - 0/4/8 base score with optional modifiers (e.g., "4++", "8-", "0")
    """)
    
    if template_mode == "Autonomic and Sensorimotor Functions":
        st.warning("""
        **Autonomic & Sensory Function Specifics:**
        - Only these 6 observations are valid:
          - piloerection
          - skin color
          - cyanosis
          - respiratory activity
          - irregular breathing
          - stertorous
        - Score system: 0 (normal) to 4 (abnormal) with +/- modifiers
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
    
    # Experiment Management
    with st.expander("Manage Experiment Groups", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add Experiment Group")
            uploaded_file = st.file_uploader("Upload CSV/XLSX for new group", 
                                            type=["csv", "xlsx"], 
                                            key="group_uploader")
            group_name = st.text_input("Group Name", key="group_name")
            
            if st.button("Add Group") and group_name and uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    # Validate required columns
                    if not all(col in df.columns for col in ['time', 'observation', 'score']):
                        st.error("File must contain columns: 'time', 'observation', 'score'")
                    else:
                        # Add numerical score column
                        df['numerical_score'] = df['score'].apply(parse_score)
                        st.session_state.experiments[group_name] = df
                        st.success(f"Added group: {group_name}")
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
        
        with col2:
            st.subheader("Generate Random Group")
            if st.button("Generate Random Experiment Data"):
                group_name = f"Group {len(st.session_state.experiments) + 1}"
                df = generate_random_experiment()
                df['numerical_score'] = df['score'].apply(parse_score)
                st.session_state.experiments[group_name] = df
                st.success(f"Generated random group: {group_name}")
    
    # Display existing groups
    if st.session_state.experiments:
        st.subheader("Experiment Groups")
        groups = list(st.session_state.experiments.keys())
        cols = st.columns(3)
        
        for i, group in enumerate(groups):
            with cols[i % 3]:
                with st.expander(f"🔬 {group}"):
                    df = st.session_state.experiments[group]
                    st.write(f"Observations: {len(df)}")
                    st.dataframe(df.head(5))
                    
                    if st.button(f"❌ Remove {group}", key=f"remove_{group}"):
                        del st.session_state.experiments[group]
                        if group in st.session_state.selected_experiments:
                            st.session_state.selected_experiments.remove(group)
                        st.rerun()
    
    # Visualization Mode Selection in Sidebar
    st.sidebar.header("Visualization Mode")
    options = ["Individual Behavior", "General Behavior", "Autonomic and Sensorimotor Functions"]
    st.session_state.mode = st.sidebar.radio(
        "Select Mode",
        options=options,
        index=options.index(st.session_state.mode)  # Dynamically sets index
    )
    
    # Visualization Controls
    if st.session_state.experiments:
        st.sidebar.header("Visualization Settings")
        st.session_state.selected_experiments = st.sidebar.multiselect(
            "Select groups to visualize",
            list(st.session_state.experiments.keys()),
            st.session_state.selected_experiments
        )
        
        if st.session_state.selected_experiments:
            # Get all times from selected experiments
            all_times = set()
            for group in st.session_state.selected_experiments:
                df = st.session_state.experiments[group]
                all_times.update(df['time'].unique())
            
            if all_times:
                st.session_state.selected_time = st.sidebar.selectbox(
                    "Select Time", 
                    sorted(list(all_times)))
            
            # Individual Behavior Mode
            if st.session_state.mode == "Individual Behavior":
                # Get all behaviors from selected experiments
                all_behaviors = set()
                for group in st.session_state.selected_experiments:
                    df = st.session_state.experiments[group]
                    all_behaviors.update(df['observation'].unique())
                
                if all_behaviors:
                    st.session_state.selected_behavior = st.sidebar.selectbox(
                        "Select Behavior", 
                        sorted(list(all_behaviors)))
            
            # Customization options
            if st.session_state.mode != "Autonomic and Sensorimotor Functions":
                st.sidebar.subheader("Customization")
                fig_width = st.sidebar.slider("Figure width", 6, 20, 12)
                fig_height = st.sidebar.slider("Figure height", 4, 15, 6)
                palette = st.sidebar.selectbox("Color palette", ["viridis", "plasma", "coolwarm", "Set2", "tab10"])
    
    # Visualization Section
    if st.session_state.selected_experiments:
        st.header("Data Visualization")
        
        if st.session_state.mode == "Individual Behavior":
            # Individual Behavior Visualization
            if not st.session_state.selected_behavior:
                st.info("Please select a behavior from the sidebar")
            else:
                # Calculate means and stds for each group
                means = []
                stds = []
                
                for group in st.session_state.selected_experiments:
                    df = st.session_state.experiments[group]
                    filtered = df[
                        (df['time'] == st.session_state.selected_time) & 
                        (df['observation'] == st.session_state.selected_behavior)
                    ]
                    
                    if not filtered.empty:
                        scores = filtered['numerical_score'].dropna()
                        means.append(scores.mean())
                        stds.append(scores.std() if len(scores) > 1 else 0)
                    else:
                        means.append(0)
                        stds.append(0)
                
                # Create plots
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(fig_width, fig_height))
                
                # Group Means Plot
                ax1.bar(st.session_state.selected_experiments, means, color=sns.color_palette(palette))
                ax1.set_title(f"Mean of {st.session_state.selected_behavior}\nat Time {st.session_state.selected_time}")
                ax1.set_ylabel("Score")
                ax1.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for i, v in enumerate(means):
                    ax1.text(i, v + 0.1, f"{v:.2f}", ha='center')
                
                # Group Stds Plot
                ax2.bar(st.session_state.selected_experiments, stds, color=sns.color_palette(palette))
                ax2.set_title(f"Std Dev of {st.session_state.selected_behavior}\nat Time {st.session_state.selected_time}")
                ax2.set_ylabel("Standard Deviation")
                ax2.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for i, v in enumerate(stds):
                    ax2.text(i, v + 0.1, f"{v:.2f}", ha='center')
                
                st.pyplot(fig)
        
        elif st.session_state.mode == "General Behavior":
            # Normalize data
            normalized_dfs = {}
            for group in st.session_state.selected_experiments:
                df = st.session_state.experiments[group].copy()
                normalized_dfs[group] = normalize_data(df)
            
            # Calculate means and stds for each group
            overall_means = []
            overall_stds = []
            
            for group in st.session_state.selected_experiments:
                df = normalized_dfs[group]
                filtered = df[df['time'] == st.session_state.selected_time]
                
                if not filtered.empty:
                    scores = filtered['normalized_score'].dropna()
                    overall_means.append(scores.mean())
                    overall_stds.append(scores.std() if len(scores) > 1 else 0)
                else:
                    overall_means.append(0)
                    overall_stds.append(0)
            
            # Create a single plot with error bars
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            
            # Plot means with error bars (std)
            x_pos = range(len(st.session_state.selected_experiments))
            bars = ax.bar(
                x_pos,
                overall_means,
                yerr=overall_stds,  # Add error bars for std
                color=sns.color_palette(palette),
                capsize=5  # Add caps to error bars
            )
            
            ax.set_title(f"Mean ± Std Dev at Time {st.session_state.selected_time}")
            ax.set_ylabel("Normalized Score (0-10)")
            ax.set_xticks(x_pos)
            ax.set_xticklabels(st.session_state.selected_experiments, rotation=45)
            ax.set_ylim(0, 10)
            
            # Add value labels (mean ± std)
            for i, (mean, std) in enumerate(zip(overall_means, overall_stds)):
                ax.text(
                    i,
                    mean + 0.2,  # Slightly above the bar
                    f"{mean:.2f} ± {std:.2f}",
                    ha='center',
                    va='bottom'
                )
            
            st.pyplot(fig)
            
            # Show normalization info
            st.info(f"Data normalized to 0-10 scale (Original range: {st.session_state.global_min:.2f} to {st.session_state.global_max:.2f})")
        
        else:  # Autonomic and Sensorimotor Functions
            st.header("Autonomic and Sensorimotor Functions Analysis")
            st.info("""
            **Scoring System:**
            - **0**: Normal
            - **4**: Abnormal (with +/- modifiers)
            - Records start time when abnormality first appears
            - Records end time when returns to normal
            """)
            
            for group in st.session_state.selected_experiments:
                st.subheader(f"Group: {group}")
                
                # Process autonomic data
                df = st.session_state.experiments[group]
                results_df = process_autonomic_data(df)
                
                if results_df.empty:
                    st.warning("No autonomic data found for this group")
                    continue
                
                # Display results in a table with styling
                st.markdown("**Abnormality Episodes**")
                
                # Apply styling based on duration
                def highlight_duration(row):
                    if row['Duration'] > 0:
                        return ['background-color: #ffcccc'] * len(row)
                    return [''] * len(row)
                
                styled_df = results_df.style.apply(highlight_duration, axis=1)
                st.dataframe(styled_df)
                
                # Plot timeline for each observation
                st.markdown("**Timeline Visualization**")
                
                # Get unique times
                times = sorted(df['time'].unique())
                if not times:
                    continue
                
                # Create a grid of charts
                cols = st.columns(3)
                for i, obs in enumerate(AUTONOMIC_OBSERVATIONS):
                    with cols[i % 3]:
                        obs_df = df[df['observation'] == obs].sort_values('time')
                        if obs_df.empty:
                            continue
                        
                        fig, ax = plt.subplots(figsize=(8, 2))
                        ax.set_title(obs)
                        ax.set_xlim(times[0] - 1, times[-1] + 1)
                        ax.set_ylim(-0.5, 4.5)
                        ax.set_yticks([0, 4])
                        ax.set_yticklabels(["Normal", "Abnormal"])
                        ax.set_xlabel("Time (min)")
                        
                        # Plot scores
                        ax.plot(obs_df['time'], obs_df['base_score'], 
                                marker='o', linestyle='-', color='#1a3d6d')
                        
                        # Highlight abnormal regions
                        abnormal_df = results_df[results_df['Observation'] == obs]
                        for _, row in abnormal_df.iterrows():
                            if row['Duration'] > 0:
                                ax.axvspan(
                                    row['Start Time'], 
                                    row['End Time'], 
                                    alpha=0.2, 
                                    color='red'
                                )
                        
                        st.pyplot(fig)
    
    else:
        st.info("Select at least one experiment group to visualize")

# Footer
st.markdown("---")
st.markdown("### About this Dashboard")
st.markdown("""
This interactive dashboard allows you to:
- Create projects and add experiment groups
- Upload CSV/XLSX files or generate random experiment data
- Visualize individual behaviors with mean and standard deviation
- Analyze general behavior with normalized scores
- Compare multiple experimental groups
- Analyze autonomic and sensorimotor functions with timeline visualization
""")