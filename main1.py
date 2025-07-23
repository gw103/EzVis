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
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager
import platform

# 配置中文字体
def configure_chinese_fonts():
    """配置matplotlib支持中文显示"""
    system = platform.system()
    
    if system == "Windows":
        # Windows系统的中文字体
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'SimSun']
    elif system == "Darwin":  # macOS
        # macOS系统的中文字体
        chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Arial Unicode MS']
    else:  # Linux
        # Linux系统的中文字体
        chinese_fonts = ['WenQuanYi Micro Hei', 'DejaVu Sans', 'Liberation Sans']
    
    # 尝试设置可用的中文字体
    for font in chinese_fonts:
        try:
            # 检查字体是否可用
            if font in [f.name for f in font_manager.fontManager.ttflist]:
                plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                print(f"已设置中文字体: {font}")
                return True
        except:
            continue
    
    # 如果上述字体都不可用，尝试通用配置
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        return True
    except:
        print("警告: 无法配置中文字体，中文可能显示为方框")
        return False

# 在文件开头调用字体配置
configure_chinese_fonts()
# Language translations
TRANSLATIONS = {
    'en': {
        'page_title': '📊 FOB Test Analysis Dashboard',
        'main_title': 'FOB Test Analysis Dashboard',
        'main_subtitle': 'Visualize and compare Functional Observational Battery (FOB) test results across multiple groups',
        'language': 'Language',
        'create_project': '🆕 Create New Project',
        'configure_project': '📋 Configure New Project',
        'project_name': 'Project Name',
        'animal_type': 'Animal Type',
        'mouse': 'Mouse',
        'rat': 'Rat',
        'custom': 'Custom',
        'custom_animal_name': 'Custom Animal Name',
        'animals_per_group': 'Number of animals per group',
        'num_groups': 'Number of groups to create',
        'create': '✅ Create Project',
        'cancel': '❌ Cancel',
        'select_mode': 'Select Analysis Mode',
        'choose_mode': 'Choose mode:',
        'general_behavior': 'General Behavior',
        'autonomic_functions': 'Autonomic and Sensorimotor Functions',
        'reflex_capabilities': 'Reflex Capabilities',
        'body_temperature': 'Body Temperature',
        'convulsive_behaviors': 'Convulsive Behaviors and Excitability',
        'experiment_groups': 'Experiment Groups',
        'select_group_edit': 'Select Group to Edit',
        'data_worksheet': 'Data Entry Worksheet',
        'manual_save': '📝 Edit with Save Button',
        'auto_save': '💾 Auto-Save Mode',
        'save_changes': '💾 Save Changes',
        'fill_random': '🎲 Fill Random Data',
        'fill_all_random': '🎲 Fill ALL Groups with Random Data',
        'add_timestep': '⏱️ Add',
        'reset': '🔄 Reset',
        'export_csv': '📥 Export Worksheet as CSV',
        'mean_scores': '📊 Mean Scores Summary',
        'filter_time': 'Filter by time points:',
        'time': 'Time',
        'observation': 'Observation',
        'mean_score': 'Mean Score',
        'status': 'Status',
        'normal': '🟢 Normal',
        'abnormal': '🔴 Abnormal',
        'abnormal_episodes': '🚨 Abnormal Episodes (Onset/Offset)',
        'onset_time': 'Onset Time',
        'offset_time': 'Offset Time',
        'duration': 'Duration',
        'peak_score': 'Peak Score',
        'no_abnormal': 'No abnormal episodes detected',
        'comparison_group': '🏆 Select Comparison Group',
        'set_comparison': 'Set as Comparison Group',
        'is_comparison': '🏆 This is a COMPARISON GROUP',
        'data_analysis': 'Data Analysis & Reporting',
        'select_analyze': 'Select groups to analyze',
        'select_all': 'Select All',
        'comparative_report': '📊 Comparative Analysis Report',
        'group_summary': '📋 Group Summary',
        'group': 'Group',
        'total_episodes': 'Total Abnormal Episodes',
        'affected_obs': 'Affected Observations',
        'none': 'None',
        'episodes_by_group': '🚨 Abnormal Episodes by Group',
        'summary': 'Summary:',
        'avg_duration': 'Avg Duration',
        'max_peak': 'Max Peak Score',
        'no_episodes': '✅ No abnormal episodes detected in any group!',
        'comparative_viz': '📈 Comparative Visualization',
        'select_time_compare': 'Select Time Point for Comparison',
        'export_report': '💾 Export Report',
        'download_report': '📄 Download Complete Report',
        'download_templates': '📝 Download Data Templates',
        'template_type': 'Select Template Type',
        'csv_template': 'CSV Template',
        'excel_template': 'Excel Template',
        'download_csv_template': 'Download CSV Template',
        'download_excel_template': 'Download Excel Template',
        'about_title': 'About this Dashboard',
        'tips': 'Tips:',
        'unsaved_changes': '⚠️ You have unsaved changes!',
        'changes_saved': '✅ Changes saved successfully!',
        'auto_saved': '✅ Auto-saved at',
        'add_new_timestep': 'Add new timestep:',
        'next_timestep': 'Next timestep (min)',
        'valid': 'Valid',
        'report_title': 'FOB Test Analysis Report',
        'report_generated': 'Report Generated',
        'detailed_episodes': 'DETAILED ABNORMAL EPISODES',
        'project': 'Project',
        'analysis_mode': 'Analysis Mode',
        'total_groups': 'Total Groups Analyzed',
        'not_set': 'Not set',
        'start_instruction': '👆 Click \'Create New Project\' to get started',
        'edit_tip': '💡 **Choose your editing mode**: Use \'Edit with Save Button\' to batch your changes, or \'Auto-Save Mode\' for instant saves.',
        'no_groups': 'No groups created yet',
        'filling_all': '⏳ Filling all worksheets with random data...',
        'fill_complete': '✅ All worksheets filled with random data!',
        'confirm_fill_all': 'This will fill random data for ALL groups across ALL analysis modes. Continue?',
        'yes': 'Yes',
        'no': 'No',
        'download_plot': '📥 Download Plot',
        'abnormal_count': 'Abnormal Count',
        'binary_instruction': '🔍 **Instructions**: Click on any cell to toggle between Normal (default) and Abnormal (red). Each observation is assessed as either Normal or Abnormal for each animal.',
        'percentage_abnormal': '% Abnormal',
        'groups_to_plot': 'Groups to plot:',
        'select_groups_chart': 'Select groups to display in the chart:',
        'all_time_points': 'All Time Points'
    },
    'zh': {
        'page_title': '📊 FOB测试分析仪表板',
        'main_title': 'FOB测试分析仪表板',
        'main_subtitle': '可视化并比较多组功能观察电池（FOB）测试结果',
        'language': '语言',
        'create_project': '🆕 创建新项目',
        'configure_project': '📋 配置新项目',
        'project_name': '项目名称',
        'animal_type': '动物类型',
        'mouse': '小鼠',
        'rat': '大鼠',
        'custom': '自定义',
        'custom_animal_name': '自定义动物名称',
        'animals_per_group': '每组动物数量',
        'num_groups': '创建组数',
        'create': '✅ 创建项目',
        'cancel': '❌ 取消',
        'select_mode': '选择分析模式',
        'choose_mode': '选择模式：',
        'general_behavior': '一般行为',
        'autonomic_functions': '自主神经和感觉运动功能',
        'reflex_capabilities': '反射能力',
        'body_temperature': '体温',
        'convulsive_behaviors': '惊厥行为和兴奋性',
        'experiment_groups': '实验组',
        'select_group_edit': '选择要编辑的组',
        'data_worksheet': '数据录入工作表',
        'manual_save': '📝 编辑后保存',
        'auto_save': '💾 自动保存模式',
        'save_changes': '💾 保存更改',
        'fill_random': '🎲 填充随机数据',
        'fill_all_random': '🎲 为所有组填充随机数据',
        'add_timestep': '⏱️ 添加',
        'reset': '🔄 重置',
        'export_csv': '📥 导出工作表为CSV',
        'mean_scores': '📊 平均分数汇总',
        'filter_time': '按时间点筛选：',
        'time': '时间',
        'observation': '观察项',
        'mean_score': '平均分数',
        'status': '状态',
        'normal': '🟢 正常',
        'abnormal': '🔴 异常',
        'abnormal_episodes': '🚨 异常事件（起始/结束）',
        'onset_time': '起始时间',
        'offset_time': '结束时间',
        'duration': '持续时间',
        'peak_score': '峰值分数',
        'no_abnormal': '未检测到异常事件',
        'comparison_group': '🏆 选择对照组',
        'set_comparison': '设为对照组',
        'is_comparison': '🏆 这是对照组',
        'data_analysis': '数据分析与报告',
        'select_analyze': '选择要分析的组',
        'select_all': '全选',
        'comparative_report': '📊 对比分析报告',
        'group_summary': '📋 组别汇总',
        'group': '组别',
        'total_episodes': '异常事件总数',
        'affected_obs': '受影响的观察项',
        'none': '无',
        'episodes_by_group': '🚨 各组异常事件',
        'summary': '汇总：',
        'avg_duration': '平均持续时间',
        'max_peak': '最高峰值分数',
        'no_episodes': '✅ 所有组均未检测到异常事件！',
        'comparative_viz': '📈 对比可视化',
        'select_time_compare': '选择比较时间点',
        'export_report': '💾 导出报告',
        'download_report': '📄 下载完整报告',
        'download_templates': '📝 下载数据模板',
        'template_type': '选择模板类型',
        'csv_template': 'CSV模板',
        'excel_template': 'Excel模板',
        'download_csv_template': '下载CSV模板',
        'download_excel_template': '下载Excel模板',
        'about_title': '关于此仪表板',
        'tips': '提示：',
        'unsaved_changes': '⚠️ 您有未保存的更改！',
        'changes_saved': '✅ 更改已成功保存！',
        'auto_saved': '✅ 自动保存于',
        'add_new_timestep': '添加新时间点：',
        'next_timestep': '下一个时间点（分钟）',
        'valid': '有效',
        'report_title': 'FOB测试分析报告',
        'report_generated': '报告生成时间',
        'detailed_episodes': '详细异常事件',
        'project': '项目',
        'analysis_mode': '分析模式',
        'total_groups': '分析组总数',
        'not_set': '未设置',
        'start_instruction': '👆 点击"创建新项目"开始',
        'edit_tip': '💡 **选择编辑模式**：使用"编辑后保存"批量更改，或使用"自动保存模式"即时保存。',
        'no_groups': '尚未创建组',
        'filling_all': '⏳ 正在为所有工作表填充随机数据...',
        'fill_complete': '✅ 所有工作表已填充随机数据！',
        'confirm_fill_all': '这将为所有分析模式下的所有组填充随机数据。是否继续？',
        'yes': '是',
        'no': '否',
        'download_plot': '📥 下载图表',
        'abnormal_count': '异常计数',
        'binary_instruction': '🔍 **说明**：点击任意单元格在正常（默认）和异常（红色）之间切换。每个观察项对每只动物评估为正常或异常。',
        'percentage_abnormal': '异常百分比',
        'groups_to_plot': '要绘制的组：',
        'select_groups_chart': '选择要在图表中显示的组：',
        'all_time_points': '所有时间点'
    }
}

# Observation translations
OBSERVATION_TRANSLATIONS = {
    'en': {
        # Autonomic observations
        'piloerection': 'piloerection',
        'skin color': 'skin color',
        'cyanosis': 'cyanosis',
        'respiratory activity': 'respiratory activity',
        'irregular breathing': 'irregular breathing',
        'stertorous': 'stertorous',
        # Reflex observations
        'startle response': 'startle response',
        'touch reactivity': 'touch reactivity',
        'vocalization': 'vocalization',
        'abnormal gait': 'abnormal gait',
        'corneal reflex': 'corneal reflex',
        'pinna reflex': 'pinna reflex',
        'catalepsy': 'catalepsy',
        'grip reflex': 'grip reflex',
        'pulling reflex': 'pulling reflex',
        'righting reflex': 'righting reflex',
        'body tone': 'body tone',
        'pain response': 'pain response',
        # Convulsive observations
        'spontaneous activity': 'spontaneous activity',
        'restlessness': 'restlessness',
        'fighting': 'fighting',
        'writhing': 'writhing',
        'tremor': 'tremor',
        'stereotypy': 'stereotypy',
        'twitches / jerks': 'twitches / jerks',
        'straub': 'straub',
        'opisthotonus': 'opisthotonus',
        'convulsion': 'convulsion',
        # General behaviors
        'Locomotion': 'Locomotion',
        'Rearing': 'Rearing',
        'Grooming': 'Grooming',
        'Sniffing': 'Sniffing',
        'Freezing': 'Freezing',
        'body temperature': 'body temperature'
    },
    'zh': {
        # Autonomic observations
        'piloerection': '立毛',
        'skin color': '皮肤颜色',
        'cyanosis': '发绀',
        'respiratory activity': '呼吸活动',
        'irregular breathing': '呼吸不规则',
        'stertorous': '鼾声呼吸',
        # Reflex observations
        'startle response': '惊吓反应',
        'touch reactivity': '触觉反应',
        'vocalization': '发声',
        'abnormal gait': '步态异常',
        'corneal reflex': '角膜反射',
        'pinna reflex': '耳廓反射',
        'catalepsy': '僵直症',
        'grip reflex': '抓握反射',
        'pulling reflex': '牵拉反射',
        'righting reflex': '翻正反射',
        'body tone': '肌张力',
        'pain response': '疼痛反应',
        # Convulsive observations
        'spontaneous activity': '自发活动',
        'restlessness': '躁动不安',
        'fighting': '打斗',
        'writhing': '扭动',
        'tremor': '震颤',
        'stereotypy': '刻板行为',
        'twitches / jerks': '抽搐/痉挛',
        'straub': '竖尾反应',
        'opisthotonus': '角弓反张',
        'convulsion': '惊厥',
        # General behaviors
        'Locomotion': '运动',
        'Rearing': '直立',
        'Grooming': '理毛',
        'Sniffing': '嗅探',
        'Freezing': '僵直',
        'body temperature': '体温'
    }
}

# Initialize language
if 'language' not in st.session_state:
    st.session_state.language = 'en'

# Get translation function
def t(key):
    """Get translation for the current language"""
    return TRANSLATIONS[st.session_state.language].get(key, key)

def t_obs(key):
    """Get observation translation for the current language"""
    return OBSERVATION_TRANSLATIONS[st.session_state.language].get(key, key)

# Set up the page
st.set_page_config(
    page_title=t('page_title'),
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
        .binary-instruction {
            background-color: #e8f4ff;
            border: 1px solid #1a3d6d;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

set_custom_style()

# Sidebar for language selection
with st.sidebar:
    st.selectbox(
        t('language'),
        options=['en', 'zh'],
        format_func=lambda x: 'English' if x == 'en' else '中文',
        key='language'
    )

# App header
st.title(t('main_title'))
st.markdown(t('main_subtitle'))

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

ALL_MODES = [
    "General Behavior", 
    "Autonomic and Sensorimotor Functions", 
    "Reflex Capabilities", 
    "Body Temperature", 
    "Convulsive Behaviors and Excitability"
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

# Helper function to save plot as bytes
def save_plot_as_bytes(fig):
    """Save matplotlib figure as bytes for download"""
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    return img_buffer.getvalue()

# Helper function to parse the scoring system
def parse_score(score_str):
    """Parse 0/4/8 scoring system with +/- modifiers or Normal/Abnormal"""
    if pd.isna(score_str):
        return np.nan
    
    # Handle binary Normal/Abnormal
    if str(score_str).lower() in ['normal', 'abnormal']:
        return 0 if str(score_str).lower() == 'normal' else 1
    
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
    
    elif mode in ["Convulsive Behaviors and Excitability", "Autonomic and Sensorimotor Functions", "Reflex Capabilities"]:
        # Binary Normal/Abnormal system
        observations = []
        if mode == "Convulsive Behaviors and Excitability":
            observations = CONVULSIVE_OBSERVATIONS
        elif mode == "Autonomic and Sensorimotor Functions":
            observations = AUTONOMIC_OBSERVATIONS
        else:  # Reflex Capabilities
            observations = REFLEX_OBSERVATIONS
            
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in observations:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_animals + 1):
                    # 80% normal, 20% abnormal
                    if np.random.random() < 0.8:
                        data[f'{animal_type}_{i}'].append('Normal')
                    else:
                        data[f'{animal_type}_{i}'].append('Abnormal')
        
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

# Function to fill all worksheets with random data
def fill_all_worksheets_with_random_data():
    """Fill all worksheets for all groups and all modes with random data"""
    if st.session_state.active_project is None:
        st.error("No active project")
        return
    
    project = st.session_state.projects[st.session_state.active_project]
    animal_type = project.get('animal_type', 'mouse')
    if animal_type == 'custom':
        animal_type = project.get('custom_animal_name', 'animal')
    num_animals = project.get('num_animals', 8)
    
    # Get all groups for this project
    project_groups = [exp for exp in st.session_state.experiments.keys() 
                     if exp.startswith(project['name'])]
    
    filled_count = 0
    
    # Progress tracking
    progress_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    total_worksheets = len(project_groups) * len(ALL_MODES)
    current_worksheet = 0
    
    # For each group
    for group in project_groups:
        # For each mode
        for mode in ALL_MODES:
            current_worksheet += 1
            progress = current_worksheet / total_worksheets
            progress_bar.progress(progress)
            progress_placeholder.text(f"{t('filling_all')} ({current_worksheet}/{total_worksheets})")
            
            worksheet_key = f"worksheet_{group}_{mode}"
            
            # Generate appropriate observations for this mode
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
            
            # Check if worksheet exists, if not create it
            if worksheet_key not in st.session_state:
                times = [0, 15, 30, 45, 60]
                data = []
                for time in times:
                    for obs in observations:
                        row = {'time': time, 'observation': obs}
                        for i in range(1, num_animals + 1):
                            if mode == "Body Temperature":
                                row[f'{animal_type}_{i}'] = '37.0'
                            elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                                row[f'{animal_type}_{i}'] = 'Normal'
                            else:
                                row[f'{animal_type}_{i}'] = '0'
                        data.append(row)
                st.session_state[worksheet_key] = pd.DataFrame(data)
            
            # Get existing times from the worksheet
            existing_df = st.session_state[worksheet_key]
            times = sorted(existing_df['time'].unique())
            
            # Generate random data
            random_df = generate_random_data(mode, times, num_animals, animal_type)
            
            # Update the worksheet
            st.session_state[worksheet_key] = random_df
            st.session_state.worksheet_data[f"{group}_{mode}"] = random_df
            filled_count += 1
    
    # Clear progress indicators
    progress_placeholder.empty()
    progress_bar.empty()
    
    return filled_count

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
            
            if mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                # For binary modes, count percentage of abnormal
                abnormal_count = sum(1 for score in animal_scores if str(score).lower() == 'abnormal')
                mean_score = (abnormal_count / len(animal_scores)) * 100 if animal_scores else 0
                is_abnormal = abnormal_count > 0  # Any animal abnormal
            else:
                mean_score = calculate_mean_score(animal_scores)
                
                # Track peak score
                if not pd.isna(mean_score) and mean_score > peak_score:
                    peak_score = mean_score
                
                # Determine if abnormal based on mode
                is_abnormal = False
                if mode == "Body Temperature":
                    # Abnormal if outside 36-38°C range
                    is_abnormal = mean_score < 36 or mean_score > 38
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
                    t('observation'): t_obs(obs),
                    t('onset_time'): onset_time,
                    t('offset_time'): row['time'],
                    t('duration'): row['time'] - onset_time,
                    t('peak_score'): peak_score if mode not in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"] else f"{peak_score:.0f}%"
                })
                in_episode = False
                onset_time = None
                peak_score = 0
        
        # Handle ongoing episode
        if in_episode and onset_time is not None:
            results.append({
                t('observation'): t_obs(obs),
                t('onset_time'): onset_time,
                t('offset_time'): obs_df['time'].max(),
                t('duration'): obs_df['time'].max() - onset_time,
                t('peak_score'): peak_score if mode not in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"] else f"{peak_score:.0f}%"
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
    
    elif mode in ["Convulsive Behaviors and Excitability", "Autonomic and Sensorimotor Functions", "Reflex Capabilities"]:
        times = [0, 15, 30]
        observations = []
        if mode == "Convulsive Behaviors and Excitability":
            observations = CONVULSIVE_OBSERVATIONS
        elif mode == "Autonomic and Sensorimotor Functions":
            observations = AUTONOMIC_OBSERVATIONS
        else:
            observations = REFLEX_OBSERVATIONS
            
        data = {
            'time': [],
            'observation': []
        }
        # Add animal columns
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in observations:
                data['time'].append(time)
                data['observation'].append(obs)
                # Add scores for each animal - default to Normal
                for i in range(1, num_animals + 1):
                    data[f'{animal_type}_{i}'].append('Normal')
        
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
    st.subheader(f"{t('data_worksheet')} - {experiment_name}")
    
    # Get animal info from project
    animal_type = project_info.get('animal_type', 'mouse')
    if animal_type == 'custom':
        animal_type = project_info.get('custom_animal_name', 'animal')
    num_animals = project_info.get('num_animals', 8)
    
    # Show if this is a comparison group
    if experiment_name in st.session_state.comparison_groups.get(st.session_state.active_project, []):
        st.success(t('is_comparison'))
    
    # Show binary scoring instruction for relevant modes
    if mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
        st.markdown(f'<div class="binary-instruction">{t("binary_instruction")}</div>', unsafe_allow_html=True)
    
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
                    elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                        row[f'{animal_type}_{i}'] = 'Normal'
                    else:
                        row[f'{animal_type}_{i}'] = '0'
                data.append(row)
        
        st.session_state[worksheet_key] = pd.DataFrame(data)
    
    # Get the dataframe from session state
    df = st.session_state[worksheet_key].copy()
    
    # Configure column settings with better formatting
    column_config = {
        'time': st.column_config.NumberColumn(
            f"{t('time')} (min)", 
            min_value=0, 
            max_value=300, 
            step=5,
            format="%d min"
        ),
        'observation': st.column_config.TextColumn(t('observation'), disabled=True)
    }
    
    # Add animal columns configuration
    for i in range(1, num_animals + 1):
        if mode == "Body Temperature":
            column_config[f'{animal_type}_{i}'] = st.column_config.TextColumn(
                f'{t(animal_type).capitalize()} {i}',
                help=f"Temperature for {animal_type} {i} in Celsius (e.g., 37.2)",
                max_chars=5
            )
        elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
            column_config[f'{animal_type}_{i}'] = st.column_config.SelectboxColumn(
                f'{t(animal_type).capitalize()} {i}',
                help=f"Click to toggle between Normal and Abnormal for {animal_type} {i}",
                options=['Normal', 'Abnormal'],
                default='Normal'
            )
        else:
            column_config[f'{animal_type}_{i}'] = st.column_config.TextColumn(
                f'{t(animal_type).capitalize()} {i}',
                help=f"Score for {animal_type} {i}. Use appropriate scoring system for the mode",
                max_chars=5
            )
    
    # Create two tabs for different interaction modes
    tab1, tab2 = st.tabs([t('manual_save'), t('auto_save')])
    
    with tab1:
        st.markdown(f"**{t('manual_save')}**")
        
        # Check if there are unsaved changes
        temp_key = f"temp_{worksheet_key}"
        if temp_key in st.session_state and not df.equals(st.session_state[temp_key]):
            st.warning(t('unsaved_changes'))
        
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
                submitted = st.form_submit_button(t('save_changes'), use_container_width=True, type="primary")
            with col2:
                fill_random = st.form_submit_button(t('fill_random'), use_container_width=True)
            with col3:
                st.markdown(f"**{t('add_new_timestep')}**")
                new_timestep = st.number_input(
                    t('next_timestep'), 
                    min_value=0,
                    max_value=300,
                    step=5,
                    value=edited_df['time'].max() + 5 if not edited_df.empty else 0,
                    key=f"new_time_{worksheet_key}",
                    label_visibility="collapsed"
                )
                add_timestep = st.form_submit_button(t('add_timestep'), use_container_width=True)
            with col4:
                reset = st.form_submit_button(t('reset'), use_container_width=True)
            
            # Fix: Ensure state changes are properly handled
            if submitted:
                # Update session state with edited data
                st.session_state[worksheet_key] = edited_df.copy()
                st.session_state.worksheet_data[f"{experiment_name}_{mode}"] = edited_df.copy()
                st.session_state.save_status[experiment_name] = "saved"
                # Clear temp changes
                if temp_key in st.session_state:
                    del st.session_state[temp_key]
                st.success(t('changes_saved'))
                # Force rerun to reflect changes
                st.rerun()
            
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
                        elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                            new_row[f'{animal_type}_{i}'] = 'Normal'
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
        st.markdown(f"**{t('auto_save')}**")
        st.info(t('edit_tip'))
        
        # Quick action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button(t('fill_random'), use_container_width=True, key=f"random_auto_{worksheet_key}"):
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
            st.session_state[worksheet_key] = edited_df_auto.copy()
            st.session_state.worksheet_data[f"{experiment_name}_{mode}"] = edited_df_auto.copy()
            st.session_state.save_status[experiment_name] = "saved"
        
        # Show save status with timestamp
        st.success(f"{t('auto_saved')} {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        # Quick actions - NEW TIMESTEP FUNCTIONALITY
        st.markdown(f"**{t('add_new_timestep')}**")
        col1, col2 = st.columns([3, 2])
        with col1:
            new_timestep_auto = st.number_input(
                t('next_timestep'), 
                min_value=0,
                max_value=300,
                step=5,
                value=edited_df_auto['time'].max() + 5 if not edited_df_auto.empty else 0,
                key=f"new_time_auto_{worksheet_key}",
                label_visibility="collapsed"
            )
        with col2:
            if st.button(t('add_timestep'), use_container_width=True):
                # Add rows for new timestep
                new_rows = []
                observations = edited_df_auto['observation'].unique()
                for obs in observations:
                    new_row = {'time': new_timestep_auto, 'observation': obs}
                    for i in range(1, num_animals + 1):
                        if mode == "Body Temperature":
                            new_row[f'{animal_type}_{i}'] = '37.0'
                        elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                            new_row[f'{animal_type}_{i}'] = 'Normal'
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
    st.subheader(t('mean_scores'))
    
    # Add a filter for time points
    unique_times = sorted(current_df['time'].unique())
    selected_times = st.multiselect(
        t('filter_time'),
        unique_times,
        default=unique_times[:3] if len(unique_times) > 3 else unique_times
    )
    
    summary_data = []
    filtered_df = current_df[current_df['time'].isin(selected_times)] if selected_times else current_df
    
    for _, row in filtered_df.iterrows():
        animal_scores = [row[f'{animal_type}_{i}'] for i in range(1, num_animals + 1) 
                        if f'{animal_type}_{i}' in row]
        
        if mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
            # For binary modes, calculate percentage abnormal
            abnormal_count = sum(1 for score in animal_scores if str(score).lower() == 'abnormal')
            percent_abnormal = (abnormal_count / len(animal_scores)) * 100 if animal_scores else 0
            status = t('abnormal') if abnormal_count > 0 else t('normal')
            
            summary_data.append({
                t('time'): f"{int(row['time'])} min",
                t('observation'): t_obs(row['observation']),
                t('abnormal_count'): f"{abnormal_count}/{len(animal_scores)}",
                t('percentage_abnormal'): f"{percent_abnormal:.1f}%",
                t('status'): status
            })
        else:
            mean_score = calculate_mean_score(animal_scores)
            
            # Count how many animals have valid scores
            valid_scores = sum(1 for score in animal_scores if pd.notna(score) and score != '')
            
            # Determine status based on mode and thresholds
            if pd.isna(mean_score):
                status = 'N/A'
            else:
                if mode == "Body Temperature":
                    status = t('normal') if 36 <= mean_score <= 38 else t('abnormal')
                else:  # General Behavior
                    if mean_score < 2 or mean_score > 6:
                        status = t('abnormal')
                    else:
                        status = t('normal')
            
            summary_data.append({
                t('time'): f"{int(row['time'])} min",
                t('observation'): t_obs(row['observation']),
                t('mean_score'): f"{mean_score:.2f}" if not pd.isna(mean_score) else "N/A",
                f"{t('valid')} {t(animal_type).capitalize()}s": f"{valid_scores}/{num_animals}",
                t('status'): status
            })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Display with custom styling
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            t('status'): st.column_config.TextColumn(t('status'), width="small")
        }
    )
    
    # Display abnormal episodes
    st.subheader(t('abnormal_episodes'))
    episodes_df = process_data_with_episodes(current_df, mode, animal_type, num_animals)
    if not episodes_df.empty:
        st.dataframe(episodes_df, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_abnormal'))
    
    return current_df

# New function to create plots for all modes
def create_comparative_plot(selected_for_viz, mode_eng, project, comparison_group=None):
    """Create comparative plots for all analysis modes"""
    
    # Get animal info
    animal_type = project.get('animal_type', 'mouse')
    if animal_type == 'custom':
        animal_type = project.get('custom_animal_name', 'animal')
    num_animals = project.get('num_animals', 8)
    
    # Get all times across selected groups
    all_times = set()
    valid_groups = []
    
    for exp in selected_for_viz:
        worksheet_key = f"worksheet_{exp}_{mode_eng}"
        if worksheet_key in st.session_state:
            df = st.session_state[worksheet_key]
            if not df.empty:
                all_times.update(df['time'].unique())
                valid_groups.append(exp)
    
    if not all_times or not valid_groups:
        st.warning("No data available for visualization")
        return None
    
    # Create visualization based on mode
    if mode_eng == "General Behavior":
        # For General Behavior, still use bar plot with time selection
        selected_time = st.selectbox(
            t('select_time_compare'), 
            sorted(list(all_times)),
            key=f"time_select_{mode_eng}"
        )
        return create_general_behavior_plot(valid_groups, selected_time, mode_eng, animal_type, num_animals, comparison_group)
    else:
        # For all other modes, use line charts
        # Allow selection of which groups to plot
        st.markdown(f"**{t('select_groups_chart')}**")
        selected_groups_for_plot = st.multiselect(
            t('groups_to_plot'),
            valid_groups,
            default=valid_groups[:3] if len(valid_groups) > 3 else valid_groups,
            key=f"groups_select_{mode_eng}"
        )
        
        if not selected_groups_for_plot:
            st.warning("Please select at least one group to plot")
            return None
            
        if mode_eng == "Body Temperature":
            return create_body_temperature_line_plot(selected_groups_for_plot, mode_eng, animal_type, num_animals, comparison_group)
        elif mode_eng in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
            return create_binary_score_line_plot(selected_groups_for_plot, mode_eng, animal_type, num_animals, comparison_group)
    
    return None

def create_general_behavior_plot(valid_groups, selected_time, mode_eng, animal_type, num_animals, comparison_group):
    """Create plot for General Behavior mode"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    overall_means = []
    overall_stds = []
    group_names = []
    
    for exp in valid_groups:
        worksheet_key = f"worksheet_{exp}_{mode_eng}"
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
    
    if not overall_means:
        st.warning("No valid data for the selected time point")
        return None
    
    # Create bar plot
    x_pos = range(len(group_names))
    bars = ax.bar(x_pos, overall_means, yerr=overall_stds, capsize=5, alpha=0.8)
    
    # Color bars based on status
    for i, (mean, group) in enumerate(zip(overall_means, group_names)):
        if group == comparison_group:
            bars[i].set_color('#28a745')  # Green for comparison group
        elif mean < 2 or mean > 6:  # Abnormal
            bars[i].set_color('#ff6b6b')  # Red for abnormal
        else:
            bars[i].set_color('#4cc9f0')  # Blue for normal
    
    # Formatting
    ax.set_title(f"{t('general_behavior')} - {t('comparative_viz')} ({selected_time} min)", fontsize=14, fontweight='bold')
    ax.set_ylabel(f"{t('mean_score')} (0-10)", fontsize=12)
    ax.set_xlabel(t('group'), fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([g.split('_')[-1] for g in group_names], rotation=45, ha='right')
    ax.set_ylim(0, 10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add threshold lines
    ax.axhline(y=2, color='gray', linestyle='--', alpha=0.7, label='Lower threshold')
    ax.axhline(y=6, color='gray', linestyle='--', alpha=0.7, label='Upper threshold')
    
    # Add value labels
    for i, (mean, std) in enumerate(zip(overall_means, overall_stds)):
        ax.text(i, mean + std + 0.2, f"{mean:.2f}", ha='center', va='bottom', fontweight='bold')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#28a745', label=t('comparison_group')),
        Patch(facecolor='#4cc9f0', label=t('normal')),
        Patch(facecolor='#ff6b6b', label=t('abnormal'))
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    return fig

def create_body_temperature_line_plot(selected_groups, mode_eng, animal_type, num_animals, comparison_group):
    """Create line plot for Body Temperature mode"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Colors for different groups
    colors = plt.cm.tab10(np.linspace(0, 1, len(selected_groups)))
    
    for idx, group in enumerate(selected_groups):
        worksheet_key = f"worksheet_{group}_{mode_eng}"
        if worksheet_key in st.session_state:
            df = st.session_state[worksheet_key]
            
            # Get unique times and sort them
            times = sorted(df['time'].unique())
            mean_temps = []
            std_temps = []
            
            for time in times:
                time_df = df[df['time'] == time]
                all_temps = []
                
                for _, row in time_df.iterrows():
                    # Collect all animal temperatures
                    for i in range(1, num_animals + 1):
                        if f'{animal_type}_{i}' in row:
                            try:
                                temp = float(row[f'{animal_type}_{i}'])
                                all_temps.append(temp)
                            except (ValueError, TypeError):
                                continue
                
                if all_temps:
                    mean_temps.append(np.mean(all_temps))
                    std_temps.append(np.std(all_temps))
                else:
                    mean_temps.append(np.nan)
                    std_temps.append(0)
            
            # Plot line with error bars
            line_style = '-' if group != comparison_group else '--'
            line_width = 2 if group != comparison_group else 3
            marker = 'o' if group != comparison_group else 's'
            
            ax.errorbar(times, mean_temps, yerr=std_temps, 
                       label=group.split('_')[-1], 
                       color=colors[idx],
                       linestyle=line_style,
                       linewidth=line_width,
                       marker=marker,
                       markersize=8,
                       capsize=5,
                       alpha=0.8)
    
    # Add normal range
    ax.axhspan(36, 38, alpha=0.2, color='green', label='Normal range (36-38°C)')
    
    # Formatting
    ax.set_title(f"{t('body_temperature')} - {t('comparative_viz')} ({t('all_time_points')})", fontsize=16, fontweight='bold')
    ax.set_xlabel(f"{t('time')} (min)", fontsize=12)
    ax.set_ylabel("Temperature (°C)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Set y-axis limits
    ax.set_ylim(34, 40)
    
    plt.tight_layout()
    return fig

def create_binary_score_line_plot(selected_groups, mode_eng, animal_type, num_animals, comparison_group):
    """Create line plot for binary (Normal/Abnormal) scoring modes"""
    # Get observations for this mode
    if mode_eng == "Autonomic and Sensorimotor Functions":
        observations = AUTONOMIC_OBSERVATIONS
    elif mode_eng == "Reflex Capabilities":
        observations = REFLEX_OBSERVATIONS
    else:  # Convulsive Behaviors
        observations = CONVULSIVE_OBSERVATIONS
    
    # Create subplot for each observation
    n_obs = len(observations)
    n_cols = 3
    n_rows = (n_obs + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5*n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()
    
    # Colors for different groups
    colors = plt.cm.tab10(np.linspace(0, 1, len(selected_groups)))
    
    for obs_idx, obs in enumerate(observations):
        ax = axes[obs_idx]
        
        for group_idx, group in enumerate(selected_groups):
            worksheet_key = f"worksheet_{group}_{mode_eng}"
            if worksheet_key in st.session_state:
                df = st.session_state[worksheet_key]
                
                # Filter for this observation
                obs_df = df[df['observation'] == obs]
                times = sorted(obs_df['time'].unique())
                percentages = []
                
                for time in times:
                    time_df = obs_df[obs_df['time'] == time]
                    if not time_df.empty:
                        abnormal_count = 0
                        total_count = 0
                        
                        for _, row in time_df.iterrows():
                            for i in range(1, num_animals + 1):
                                if f'{animal_type}_{i}' in row:
                                    if str(row[f'{animal_type}_{i}']).lower() == 'abnormal':
                                        abnormal_count += 1
                                    total_count += 1
                        
                        percentage = (abnormal_count / total_count * 100) if total_count > 0 else 0
                        percentages.append(percentage)
                    else:
                        percentages.append(0)
                
                # Plot line
                line_style = '-' if group != comparison_group else '--'
                line_width = 2 if group != comparison_group else 3
                marker = 'o' if group != comparison_group else 's'
                
                ax.plot(times, percentages, 
                       label=group.split('_')[-1],
                       color=colors[group_idx],
                       linestyle=line_style,
                       linewidth=line_width,
                       marker=marker,
                       markersize=6,
                       alpha=0.8)
        
        # Formatting
        ax.set_title(t_obs(obs), fontsize=12, fontweight='bold')
        ax.set_xlabel(f"{t('time')} (min)", fontsize=10)
        ax.set_ylabel(f"{t('percentage_abnormal')} (%)", fontsize=10)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.3)
        
        # Add legend only to first subplot
        if obs_idx == 0:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    # Hide unused subplots
    for idx in range(n_obs, len(axes)):
        axes[idx].set_visible(False)
    
    # Overall title
    mode_title = mode_eng.replace("and Sensorimotor Functions", "")
    fig.suptitle(f"{mode_title} - {t('comparative_viz')} ({t('all_time_points')})", fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_body_temperature_line_plot(selected_groups, mode_eng, animal_type, num_animals, comparison_group):
    """Create line plot for Body Temperature mode"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Colors for different groups
    colors = plt.cm.tab10(np.linspace(0, 1, len(selected_groups)))
    
    for idx, group in enumerate(selected_groups):
        worksheet_key = f"worksheet_{group}_{mode_eng}"
        if worksheet_key in st.session_state:
            df = st.session_state[worksheet_key]
            
            # Get unique times and sort them
            times = sorted(df['time'].unique())
            mean_temps = []
            std_temps = []
            
            for time in times:
                time_df = df[df['time'] == time]
                all_temps = []
                
                for _, row in time_df.iterrows():
                    # Collect all animal temperatures
                    for i in range(1, num_animals + 1):
                        if f'{animal_type}_{i}' in row:
                            try:
                                temp = float(row[f'{animal_type}_{i}'])
                                all_temps.append(temp)
                            except (ValueError, TypeError):
                                continue
                
                if all_temps:
                    mean_temps.append(np.mean(all_temps))
                    std_temps.append(np.std(all_temps))
                else:
                    mean_temps.append(np.nan)
                    std_temps.append(0)
            
            # Plot line with error bars
            line_style = '-' if group != comparison_group else '--'
            line_width = 2 if group != comparison_group else 3
            marker = 'o' if group != comparison_group else 's'
            
            ax.errorbar(times, mean_temps, yerr=std_temps, 
                       label=group.split('_')[-1], 
                       color=colors[idx],
                       linestyle=line_style,
                       linewidth=line_width,
                       marker=marker,
                       markersize=8,
                       capsize=5,
                       alpha=0.8)
    
    # Add normal range
    ax.axhspan(36, 38, alpha=0.2, color='green', label='Normal range (36-38°C)')
    
    # Formatting
    ax.set_title(f"{t('body_temperature')} - {t('comparative_viz')}", fontsize=16, fontweight='bold')
    ax.set_xlabel(f"{t('time')} (min)", fontsize=12)
    ax.set_ylabel("Temperature (°C)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Set y-axis limits
    ax.set_ylim(34, 40)
    
    plt.tight_layout()
    return fig

def create_binary_score_line_plot(selected_groups, mode_eng, animal_type, num_animals, comparison_group):
    """Create line plot for binary (Normal/Abnormal) scoring modes"""
    # Get observations for this mode
    if mode_eng == "Autonomic and Sensorimotor Functions":
        observations = AUTONOMIC_OBSERVATIONS
    elif mode_eng == "Reflex Capabilities":
        observations = REFLEX_OBSERVATIONS
    else:  # Convulsive Behaviors
        observations = CONVULSIVE_OBSERVATIONS
    
    # Create subplot for each observation
    n_obs = len(observations)
    n_cols = 3
    n_rows = (n_obs + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5*n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()
    
    # Colors for different groups
    colors = plt.cm.tab10(np.linspace(0, 1, len(selected_groups)))
    
    for obs_idx, obs in enumerate(observations):
        ax = axes[obs_idx]
        
        for group_idx, group in enumerate(selected_groups):
            worksheet_key = f"worksheet_{group}_{mode_eng}"
            if worksheet_key in st.session_state:
                df = st.session_state[worksheet_key]
                
                # Filter for this observation
                obs_df = df[df['observation'] == obs]
                times = sorted(obs_df['time'].unique())
                percentages = []
                
                for time in times:
                    time_df = obs_df[obs_df['time'] == time]
                    if not time_df.empty:
                        abnormal_count = 0
                        total_count = 0
                        
                        for _, row in time_df.iterrows():
                            for i in range(1, num_animals + 1):
                                if f'{animal_type}_{i}' in row:
                                    if str(row[f'{animal_type}_{i}']).lower() == 'abnormal':
                                        abnormal_count += 1
                                    total_count += 1
                        
                        percentage = (abnormal_count / total_count * 100) if total_count > 0 else 0
                        percentages.append(percentage)
                    else:
                        percentages.append(0)
                
                # Plot line
                line_style = '-' if group != comparison_group else '--'
                line_width = 2 if group != comparison_group else 3
                marker = 'o' if group != comparison_group else 's'
                
                ax.plot(times, percentages, 
                       label=group.split('_')[-1],
                       color=colors[group_idx],
                       linestyle=line_style,
                       linewidth=line_width,
                       marker=marker,
                       markersize=6,
                       alpha=0.8)
        
        # Formatting
        ax.set_title(t_obs(obs), fontsize=12, fontweight='bold')
        ax.set_xlabel(f"{t('time')} (min)", fontsize=10)
        ax.set_ylabel(f"{t('percentage_abnormal')} (%)", fontsize=10)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.3)
        
        # Add legend only to first subplot
        if obs_idx == 0:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    # Hide unused subplots
    for idx in range(n_obs, len(axes)):
        axes[idx].set_visible(False)
    
    # Overall title
    mode_title = mode_eng.replace("and Sensorimotor Functions", "")
    fig.suptitle(f"{mode_title} - {t('comparative_viz')}", fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    return fig

# Template Section
with st.expander(t('download_templates'), expanded=False):
    st.markdown(f"""
    ### {t('download_templates')}
    """)
    
    # Mode selection for template
    template_mode = st.radio(t('template_type'), 
                            [t('general_behavior'), t('autonomic_functions'), 
                             t('reflex_capabilities'), t('body_temperature'), 
                             t('convulsive_behaviors')],
                            index=0,
                            horizontal=True)
    
    # Map back to English for internal use
    mode_map = {
        t('general_behavior'): "General Behavior",
        t('autonomic_functions'): "Autonomic and Sensorimotor Functions",
        t('reflex_capabilities'): "Reflex Capabilities",
        t('body_temperature'): "Body Temperature",
        t('convulsive_behaviors'): "Convulsive Behaviors and Excitability"
    }
    template_mode_eng = mode_map[template_mode]
    
    # Animal configuration for template
    col_temp1, col_temp2, col_temp3 = st.columns(3)
    with col_temp1:
        template_animal = st.selectbox(t('animal_type'), [t('mouse'), t('rat'), t('custom')], key="template_animal")
    with col_temp2:
        if template_animal == t('custom'):
            template_custom_name = st.text_input(t('custom_animal_name'), value="animal", key="template_custom")
        else:
            template_custom_name = None
    with col_temp3:
        template_num_animals = st.number_input(t('animals_per_group'), min_value=1, max_value=20, value=8, key="template_num")
    
    # Determine actual animal type for template
    if template_animal == t('mouse'):
        template_animal_type = "mouse"
    elif template_animal == t('rat'):
        template_animal_type = "rat"
    else:
        template_animal_type = template_custom_name or "animal"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(t('csv_template'))
        template_csv = create_template(template_mode_eng, template_num_animals, template_animal_type)
        st.dataframe(template_csv.head(5))
        
        # Convert to CSV
        csv = template_csv.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label=t('download_csv_template'),
            data=csv,
            file_name=f"fob_template_{template_mode_eng.replace(' ', '_')}_{template_animal_type}.csv",
            mime="text/csv",
            help="Download CSV template for experiment data"
        )
    
    with col2:
        st.subheader(t('excel_template'))
        template_excel = create_template(template_mode_eng, template_num_animals, template_animal_type)
        st.dataframe(template_excel.head(5))
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            template_excel.to_excel(writer, index=False, sheet_name='FOB Data')
        
        st.download_button(
            label=t('download_excel_template'),
            data=output.getvalue(),
            file_name=f"fob_template_{template_mode_eng.replace(' ', '_')}_{template_animal_type}.xlsx",
            mime="application/vnd.ms-excel",
            help="Download Excel template for experiment data"
        )

# Global fill random data button
if st.session_state.active_project is not None:
    project_groups = [exp for exp in st.session_state.experiments.keys() 
                     if exp.startswith(st.session_state.projects[st.session_state.active_project]['name'])]
    
    if project_groups:
        if st.button(t('fill_all_random'), use_container_width=True, type="secondary"):
            # Confirm dialog
            if 'confirm_fill_all' not in st.session_state:
                st.session_state.confirm_fill_all = True
                st.rerun()

        if 'confirm_fill_all' in st.session_state and st.session_state.confirm_fill_all:
            st.warning(t('confirm_fill_all'))
            col1, col2 = st.columns(2)
            with col1:
                if st.button(t('yes'), use_container_width=True):
                    filled_count = fill_all_worksheets_with_random_data()
                    st.success(t('fill_complete'))
                    del st.session_state.confirm_fill_all
                    st.rerun()
            with col2:
                if st.button(t('no'), use_container_width=True):
                    del st.session_state.confirm_fill_all
                    st.rerun()

# Project Creation Section
if st.button(t('create_project'), key="create_project_btn", use_container_width=True, type="primary"):
    st.session_state.show_project_creation = True

if 'show_project_creation' in st.session_state and st.session_state.show_project_creation:
    with st.container():
        st.subheader(t('configure_project'))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            project_name = st.text_input(t('project_name'), value=f"Project {len(st.session_state.projects) + 1}")
            animal_type = st.selectbox(t('animal_type'), [t('mouse'), t('rat'), t('custom')])
        
        with col2:
            if animal_type == t('custom'):
                custom_animal_name = st.text_input(t('custom_animal_name'), value="animal")
            else:
                custom_animal_name = None
            num_animals = st.number_input(t('animals_per_group'), min_value=1, max_value=20, value=8)
        
        with col3:
            num_groups = st.number_input(t('num_groups'), min_value=1, max_value=10, value=5)
            
        # Create project button
        if st.button(t('create'), use_container_width=True):
            project_id = str(uuid.uuid4())
            st.session_state.active_project = project_id
            
            # Map animal type back to English
            animal_type_map = {t('mouse'): 'mouse', t('rat'): 'rat', t('custom'): 'custom'}
            animal_type_eng = animal_type_map.get(animal_type, 'mouse')
            
            st.session_state.projects[project_id] = {
                "name": project_name,
                "animal_type": animal_type_eng,
                "custom_animal_name": custom_animal_name,
                "num_animals": num_animals,
                "num_groups": num_groups
            }
            
            # Create groups
            for i in range(1, num_groups + 1):
                group_name = f"{project_name}_Group_{i}"
                st.session_state.experiments[group_name] = True
            
            st.session_state.show_project_creation = False
            st.success(f"✅ {t('create')} '{project_name}' - {num_groups} groups")
            st.rerun()
        
        if st.button(t('cancel'), use_container_width=True):
            st.session_state.show_project_creation = False
            st.rerun()

# Main Content Area
if st.session_state.active_project is None:
    st.info(t('start_instruction'))
else:
    project = st.session_state.projects[st.session_state.active_project]
    animal_display = t(project['animal_type'])
    if project['animal_type'] == 'custom':
        animal_display = project.get('custom_animal_name', 'animal').capitalize()
    
    st.header(f"🔬 {project['name']} - {animal_display} ({project['num_animals']} {t('animals_per_group')})")
    
    # Mode Selection
    st.subheader(t('select_mode'))
    mode = st.radio(t('choose_mode'), 
                    [t('general_behavior'), t('autonomic_functions'), 
                     t('reflex_capabilities'), t('body_temperature'), 
                     t('convulsive_behaviors')],
                    horizontal=True)
    
    # Map mode back to English for internal use
    mode_map = {
        t('general_behavior'): "General Behavior",
        t('autonomic_functions'): "Autonomic and Sensorimotor Functions",
        t('reflex_capabilities'): "Reflex Capabilities",
        t('body_temperature'): "Body Temperature",
        t('convulsive_behaviors'): "Convulsive Behaviors and Excitability"
    }
    mode_eng = mode_map[mode]
    st.session_state.mode = mode_eng
    
    # Get project-specific groups
    project_groups = [exp for exp in st.session_state.experiments.keys() 
                     if exp.startswith(project['name'])]
    
    # Select comparison group
    if project_groups:
        with st.expander(t('comparison_group'), expanded=True):
            comparison_group = st.selectbox(
                t('comparison_group'),
                project_groups,
                index=0
            )
            
            if st.button(t('set_comparison')):
                if st.session_state.active_project not in st.session_state.comparison_groups:
                    st.session_state.comparison_groups[st.session_state.active_project] = []
                st.session_state.comparison_groups[st.session_state.active_project] = [comparison_group]
                st.success(f"✅ {comparison_group} {t('set_comparison')}")
                st.rerun()
            
            # Show current comparison group
            if st.session_state.active_project in st.session_state.comparison_groups:
                current_comp = st.session_state.comparison_groups[st.session_state.active_project]
                if current_comp:
                    st.info(f"{t('comparison_group')}: **{current_comp[0]}**")
    
    # Two-column layout for worksheet and visualization
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Group Management
        st.subheader(t('experiment_groups'))
        
        # Select group to edit
        if project_groups:
            selected_exp = st.selectbox(t('select_group_edit'), project_groups)
            
            if selected_exp:
                st.info(t('edit_tip'))
                
                # Display worksheet
                with st.container():
                    worksheet_df = create_worksheet(mode_eng, selected_exp, project)
                
                # Export options
                csv = worksheet_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=t('export_csv'),
                    data=csv,
                    file_name=f"{selected_exp}_data.csv",
                    mime="text/csv"
                )
    
    with col_right:
        # Visualization and Reporting Section
        st.subheader(t('data_analysis'))
        
        if project_groups:
            # Select groups to analyze
            col_sel1, col_sel2 = st.columns([3, 1])
            
            with col_sel1:
                selected_for_viz = st.multiselect(
                    t('select_analyze'),
                    project_groups,
                    default=project_groups
                )
            
            with col_sel2:
                if st.button(t('select_all'), use_container_width=True):
                    st.session_state.selected_for_viz = project_groups
                    st.rerun()
            
            # Use session state if "Select All" was clicked
            if 'selected_for_viz' in st.session_state:
                selected_for_viz = st.session_state.selected_for_viz
                del st.session_state.selected_for_viz
            
            if selected_for_viz:
                # Generate comprehensive report
                st.markdown(f"### {t('comparative_report')}")
                
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
                    worksheet_key = f"worksheet_{exp}_{mode_eng}"
                    if worksheet_key in st.session_state:
                        df = st.session_state[worksheet_key]
                        
                        # Get abnormal episodes
                        episodes_df = process_data_with_episodes(df, mode_eng, animal_type, num_animals)
                        if not episodes_df.empty:
                            all_abnormal_episodes[exp] = episodes_df
                        
                        # Collect comparison data
                        group_data = {
                            t('group'): exp,
                            t('is_comparison'): '✓' if exp == comp_group else '',
                            t('total_episodes'): len(episodes_df) if not episodes_df.empty else 0,
                            t('affected_obs'): ', '.join(episodes_df[t('observation')].unique()) if not episodes_df.empty else t('none')
                        }
                        comparison_data.append(group_data)
                
                # Display comparison summary
                st.markdown(f"#### {t('group_summary')}")
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(
                    comparison_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        t('is_comparison'): st.column_config.TextColumn(t('comparison_group'), width="small")
                    }
                )
                
                # Display detailed abnormal episodes by group
                st.markdown(f"#### {t('episodes_by_group')}")
                
                if all_abnormal_episodes:
                    # Create tabs for each group with episodes
                    tabs = st.tabs([f"{group} ({len(episodes)})" for group, episodes in all_abnormal_episodes.items()])
                    
                    for i, (group, episodes) in enumerate(all_abnormal_episodes.items()):
                        with tabs[i]:
                            if group == comp_group:
                                st.info(t('is_comparison'))
                            
                            # Add group name to episodes
                            episodes[t('group')] = group
                            
                            # Display episodes
                            st.dataframe(
                                episodes[[t('observation'), t('onset_time'), t('offset_time'), t('duration'), t('peak_score')]],
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Summary statistics for this group
                            st.markdown(f"**{t('summary')}**")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(t('total_episodes'), len(episodes))
                            with col2:
                                st.metric(t('avg_duration'), f"{episodes[t('duration')].mean():.1f} min" if len(episodes) > 0 else "N/A")
                            with col3:
                                if mode_eng in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                                    st.metric(t('max_peak'), episodes[t('peak_score')].max() if len(episodes) > 0 else "N/A")
                                else:
                                    st.metric(t('max_peak'), f"{episodes[t('peak_score')].max():.2f}" if len(episodes) > 0 else "N/A")
                else:
                    st.success(t('no_episodes'))
                
                # NEW: Comparative visualization for ALL modes
                st.markdown(f"#### {t('comparative_viz')}")
                
                # Create plot for the current mode
                fig = create_comparative_plot(selected_for_viz, mode_eng, project, comp_group)
                
                if fig is not None:
                    # Display the plot
                    st.pyplot(fig)
                    
                    # Add download button for the plot
                    plot_bytes = save_plot_as_bytes(fig)
                    st.download_button(
                        label=t('download_plot'),
                        data=plot_bytes,
                        file_name=f"{project['name']}_{mode_eng.replace(' ', '_')}_plot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                    
                    # Close the figure to free memory
                    plt.close(fig)
                
                # Export comprehensive report
                st.markdown(f"#### {t('export_report')}")
                
                # Prepare report data
                report_data = {
                    t('project'): project['name'],
                    t('animal_type'): animal_display,
                    t('animals_per_group'): project['num_animals'],
                    t('analysis_mode'): mode,
                    t('total_groups'): len(selected_for_viz),
                    t('comparison_group'): comp_group or t('not_set'),
                    t('report_generated'): datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Create detailed report
                report_lines = [
                    t('report_title'),
                    f"=" * 50,
                    f"{t('project')}: {report_data[t('project')]}",
                    f"{t('animal_type')}: {report_data[t('animal_type')]}",
                    f"{t('animals_per_group')}: {report_data[t('animals_per_group')]}",
                    f"{t('analysis_mode')}: {report_data[t('analysis_mode')]}",
                    f"{t('total_groups')}: {report_data[t('total_groups')]}",
                    f"{t('comparison_group')}: {report_data[t('comparison_group')]}",
                    f"{t('report_generated')}: {report_data[t('report_generated')]}",
                    f"",
                    t('group_summary').upper(),
                    f"-" * 50
                ]
                
                # Add group summaries
                for group_data in comparison_data:
                    report_lines.append(f"\n{t('group')}: {group_data[t('group')]}")
                    if group_data[t('is_comparison')]:
                        report_lines.append(f"({t('comparison_group').upper()})")
                    report_lines.append(f"{t('total_episodes')}: {group_data[t('total_episodes')]}")
                    report_lines.append(f"{t('affected_obs')}: {group_data[t('affected_obs')]}")
                
                # Add detailed episodes
                if all_abnormal_episodes:
                    report_lines.append(f"\n\n{t('detailed_episodes').upper()}")
                    report_lines.append(f"=" * 50)
                    
                    for group, episodes in all_abnormal_episodes.items():
                        report_lines.append(f"\n{group}:")
                        report_lines.append(f"-" * 30)
                        for _, episode in episodes.iterrows():
                            report_lines.append(f"  {t('observation')}: {episode[t('observation')]}")
                            report_lines.append(f"  {t('onset_time')}: {episode[t('onset_time')]} min")
                            report_lines.append(f"  {t('offset_time')}: {episode[t('offset_time')]} min")
                            report_lines.append(f"  {t('duration')}: {episode[t('duration')]} min")
                            report_lines.append(f"  {t('peak_score')}: {episode[t('peak_score')]}")
                            report_lines.append("")
                
                report_text = "\n".join(report_lines)
                
                st.download_button(
                    label=t('download_report'),
                    data=report_text,
                    file_name=f"{project['name']}_FOB_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            else:
                st.info(t('select_analyze'))
        else:
            st.info(t('no_groups'))

# Footer
st.markdown("---")
st.markdown(f"### {t('about_title')}")

# About section based on language
if st.session_state.language == 'zh':
    st.markdown("""
此增强型交互式仪表板允许您：
- **创建项目**，可自定义动物类型（小鼠、大鼠或自定义）
- **指定每组动物数量**（灵活的组大小）
- **一次创建多个组**（默认：每个项目5个组）
- **指定对照组**作为参考
- **一键为所有组的所有模式填充随机数据**
- 为具有可自定义组大小的单个动物输入数据
- **综合报告**所有组的异常参数
- **跟踪所有异常事件的起始和结束时间**
- **视觉比较组**，突出显示对照组
- **为所有分析模式生成图表**，支持下载
  - **一般行为**：在选定时间点比较组的条形图
  - **体温**：显示温度随时间变化趋势的折线图
  - **自主神经/反射/惊厥**：显示每种行为异常动物百分比随时间变化的折线图
- 导出包含所有异常事件的详细报告
- **完整的中文界面支持**

**评分阈值：**
- **一般行为**：正常：2-6，异常：<2 或 >6
- **自主神经功能**：点击单元格在正常/异常之间切换
- **反射能力**：点击单元格在正常/异常之间切换
- **惊厥行为**：点击单元格在正常/异常之间切换
- **体温**：正常：36-38°C，异常：<36°C 或 >38°C

**提示：**
- 对于自主神经、反射和惊厥模式：只需点击任何单元格即可在正常（默认）和异常（红色）之间切换
- 折线图显示体温、自主神经、反射和惊厥模式的行为趋势
- 选择要在折线图中显示的组以便更好地比较
- 在项目创建时创建多个组以提高效率
- 将一个组设置为对照组作为参考
- 使用综合报告识别组间差异
- 导出报告和图表用于文档记录和进一步分析
- 使用"填充所有组随机数据"快速测试功能
""")
else:
    st.markdown("""
This enhanced interactive dashboard allows you to:
- **Create projects** with customizable animal types (mice, rats, or custom)
- **Specify the number of animals** per group (flexible group sizes)
- **Create multiple groups at once** (default: 5 groups per project)
- **Designate a comparison/control group** for reference
- **Fill ALL groups across ALL modes with random data** with one click
- Enter data for individual animals with customizable group sizes
- **Comprehensive reporting** of abnormal parameters across all groups
- **Track onset and offset times** for all abnormal episodes
- **Compare groups visually** with highlighted comparison group
- **Generate plots for ALL analysis modes** with download capability
  - **General Behavior**: Bar charts comparing groups at selected time points
  - **Body Temperature**: Line charts showing temperature trends over time
  - **Autonomic/Reflex/Convulsive**: Line charts showing percentage of abnormal animals for each behavior over time
- Export detailed reports with all abnormal episodes
- **Full Chinese language support** with language switcher

**Scoring Thresholds:**
- **General Behavior**: Normal: 2-6, Abnormal: <2 or >6
- **Autonomic Functions**: Click cells to toggle between Normal/Abnormal
- **Reflex Capabilities**: Click cells to toggle between Normal/Abnormal
- **Convulsive Behaviors**: Click cells to toggle between Normal/Abnormal
- **Body Temperature**: Normal: 36-38°C, Abnormal: <36°C or >38°C

**Tips:**
- For Autonomic, Reflex, and Convulsive modes: Simply click any cell to toggle between Normal (default) and Abnormal (red)
- Line charts show behavior trends over time for Body Temperature, Autonomic, Reflex, and Convulsive modes
- Select which groups to display in line charts for better comparison
- Create multiple groups at project creation for efficient setup
- Set one group as the comparison group for reference
- Use the comprehensive report to identify differences between groups
- Export reports and plots for documentation and further analysis
- Use "Fill ALL Groups with Random Data" to quickly test functionality
- Download individual plots for presentations and publications
- All plots are automatically generated based on the selected analysis mode
""")