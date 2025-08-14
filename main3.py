# main.py
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
import hashlib
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError  # <-- include NoCredentialsError
import pickle
import hmac

# ====================== AWS CONFIGURATION ======================
# Set these as environment variables or in Streamlit secrets
AWS_ACCESS_KEY_ID = st.secrets.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = st.secrets.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = st.secrets.get("AWS_REGION", "us-east-2")
S3_BUCKET_NAME = st.secrets.get("S3_BUCKET_NAME", "fob-dashboard-storage")

# ====================== USER AUTHENTICATION ======================
def get_user_db_path():
    """Get path for user database from S3"""
    return "user_database/users.json"

def load_user_database():
    """Load user database from S3"""
    s3_client = get_s3_client()
    if not s3_client:
        return {}
    
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=get_user_db_path())
        users = json.loads(response['Body'].read().decode('utf-8'))
        return users
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {}
        else:
            st.error(f"Error loading user database: {str(e)}")
            return {}

def save_user_database(users):
    """Save user database to S3"""
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=get_user_db_path(),
            Body=json.dumps(users).encode('utf-8'),
            ContentType='application/json'
        )
        return True
    except Exception as e:
        st.error(f"Error saving user database: {str(e)}")
        return False

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against provided password"""
    return stored_password == hash_password(provided_password)

def register_user(username, password, email, name):
    """Register a new user"""
    users = load_user_database()
    
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        "password": hash_password(password),
        "email": email,
        "name": name,
        "created_at": datetime.datetime.now().isoformat(),
        "last_login": None,
        "projects": []
    }
    
    if save_user_database(users):
        return True, "Registration successful"
    return False, "Failed to save user"

def authenticate_user(username, password):
    """Authenticate user"""
    users = load_user_database()
    
    if username not in users:
        return False, "Username not found"
    
    if verify_password(users[username]["password"], password):
        users[username]["last_login"] = datetime.datetime.now().isoformat()
        save_user_database(users)
        return True, users[username]
    
    return False, "Incorrect password"

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

# ====================== S3 CLIENT (single, verified) ======================
def get_s3_client():
    """Get S3 client with credentials and verify connection"""
    try:
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            st.error("⚠️ AWS credentials not configured! Please add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to Streamlit secrets.")
            return None
            
        client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Ensure bucket exists / is accessible
        try:
            client.head_bucket(Bucket=S3_BUCKET_NAME)
        except ClientError as e:
            error_code = e.response['Error'].get('Code', '')
            if error_code in ('404', 'NoSuchBucket'):
                st.info(f"Creating S3 bucket: {S3_BUCKET_NAME}")
                try:
                    if AWS_REGION == 'us-east-1':
                        client.create_bucket(Bucket=S3_BUCKET_NAME)
                    else:
                        client.create_bucket(
                            Bucket=S3_BUCKET_NAME,
                            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                        )
                    st.success(f"✅ Created S3 bucket: {S3_BUCKET_NAME}")
                except ClientError as create_error:
                    st.error(f"❌ Failed to create bucket: {str(create_error)}")
                    return None
            elif error_code == '403':
                st.error(f"❌ Access denied to bucket {S3_BUCKET_NAME}. Check your AWS permissions.")
                return None
            else:
                st.error(f"❌ Error accessing bucket: {str(e)}")
                return None
                
        return client
        
    except NoCredentialsError:
        st.error("❌ AWS credentials not found. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        return None
    except Exception as e:
        st.error(f"❌ Failed to connect to AWS S3: {str(e)}")
        return None

# ====================== PROJECT HELPERS ======================
def get_user_folder(username):
    """Base S3 folder path for the user"""
    return f"user_data/{username}"

def get_active_project_name():
    """Safely get the active project's *name* (not the UUID), fallback 'General'."""
    try:
        pid = st.session_state.get('active_project')
        if pid and pid in st.session_state.get('projects', {}):
            return st.session_state.projects[pid].get('name') or "General"
    except Exception:
        pass
    return "General"

def _sanitize(name: str, default: str):
    safe = "".join(c for c in (name or "") if c.isalnum() or c in (" ", "-", "_")).strip()
    return safe or default

# ====================== S3 STORAGE FUNCTIONS (project-scoped) ======================
def save_figure_to_s3(fig, username, figure_name, project_name=None):
    """Save matplotlib figure to S3 under user_data/<user>/projects/<project>/figures/"""
    s3_client = get_s3_client()
    if not s3_client:
        st.error("Cannot save: S3 client not available")
        return None, None
    
    try:
        # Buffer the figure
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Paths
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = _sanitize(figure_name, "plot")
        proj = _sanitize(project_name or get_active_project_name(), "Project")
        file_key = f"{get_user_folder(username)}/projects/{proj}/figures/{safe_name}_{timestamp}.png"
        
        # Upload
        st.info("📤 Uploading figure to S3...")
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=img_buffer.getvalue(),
            ContentType='image/png',
            Metadata={
                'username': username,
                'figure_name': safe_name,
                'project': proj,
                'upload_time': timestamp
            }
        )
        
        # Verify
        try:
            s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
            st.success("✅ Figure saved successfully to cloud!")
        except ClientError:
            st.error("⚠️ Upload verification failed")
            return None, None
        
        # Presigned URL
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET_NAME, 'Key': file_key},
                ExpiresIn=3600
            )
            return url, file_key
        except ClientError as e:
            st.warning(f"Could not generate download URL: {str(e)}")
            return None, file_key
            
    except ClientError as e:
        st.error(f"❌ AWS S3 Error: {str(e)}")
        return None, None
    except Exception as e:
        st.error(f"❌ Error saving figure: {str(e)}")
        import traceback
        st.error(f"Debug info: {traceback.format_exc()}")
        return None, None

def save_dataframe_to_s3(df, username, file_name, project_name=None):
    """Save dataframe CSV to S3 under user_data/<user>/projects/<project>/data/.
    On success: shows a 1-hour presigned URL and returns the S3 object key.
    """
    s3_client = get_s3_client()
    if not s3_client:
        st.error("Cannot save: S3 client not available")
        return None

    try:
        # ---- Build CSV in memory
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # ---- Paths / names
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = _sanitize(file_name, "data")
        proj = _sanitize(project_name or get_active_project_name(), "Project")
        file_key = f"{get_user_folder(username)}/projects/{proj}/data/{safe_name}_{timestamp}.csv"
        download_filename = f"{safe_name}_{timestamp}.csv"

        # ---- Upload
        st.info("📤 Uploading data to S3…")
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=csv_buffer.getvalue(),
            ContentType="text/csv",
            ContentDisposition=f'attachment; filename="{download_filename}"',
            Metadata={
                "username": username,
                "file_name": safe_name,
                "project": proj,
                "upload_time": timestamp,
                "rows": str(len(df)),
                "columns": str(len(df.columns)),
            },
        )

        # ---- Verify upload
        try:
            response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
            file_size = response.get("ContentLength", 0)
            etag = response.get("ETag", "").strip('"')
            st.success(f"✅ Data saved successfully to cloud! ({file_size:,} bytes)")
            st.caption(f"ETag: {etag}")

            # ---- Give a direct download link (1 hour)
            try:
                url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": S3_BUCKET_NAME, "Key": file_key},
                    ExpiresIn=3600,
                )
                st.markdown(f"📥 **Download now:** [{download_filename}]({url}) — _link valid for 1 hour_")
            except ClientError as e:
                st.warning(f"Could not create download link: {e}")

            # (Optional) Show the S3 URI so users can copy it
            st.code(f"s3://{S3_BUCKET_NAME}/{file_key}", language="bash")

            return file_key

        except ClientError as e:
            st.error("⚠️ Upload verification failed")
            st.error(str(e))
            return None

    except ClientError as e:
        st.error(f"❌ AWS S3 Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Error saving data: {str(e)}")
        import traceback
        st.error(f"Debug info: {traceback.format_exc()}")
        return None


def save_project_state(username, project_data):
    """Save project state (kept user-wide; not per-project file)"""
    s3_client = get_s3_client()
    if not s3_client:
        st.error("Cannot save: S3 client not available")
        return False
    
    try:
        data_buffer = BytesIO()
        pickle.dump(project_data, data_buffer)
        data_buffer.seek(0)
        
        file_key = f"{get_user_folder(username)}/projects/project_state.pkl"
        
        # Backup any existing
        backup_key = f"{get_user_folder(username)}/projects/project_state_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        try:
            s3_client.copy_object(
                Bucket=S3_BUCKET_NAME,
                CopySource={'Bucket': S3_BUCKET_NAME, 'Key': file_key},
                Key=backup_key
            )
        except ClientError:
            pass
        
        st.info("📤 Saving project state to cloud...")
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=data_buffer.getvalue(),
            ContentType='application/octet-stream',
            Metadata={
                'username': username,
                'save_time': datetime.datetime.now().isoformat(),
                'projects_count': str(len(project_data.get('projects', {}))),
                'worksheets_count': str(len(project_data.get('worksheets', {})))
            }
        )
        
        # Verify
        try:
            s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
            st.success("✅ Project state saved successfully!")
            return True
        except ClientError:
            st.error("⚠️ Save verification failed")
            return False
            
    except Exception as e:
        st.error(f"❌ Error saving project state: {str(e)}")
        import traceback
        st.error(f"Debug info: {traceback.format_exc()}")
        return False

def load_project_state(username):
    """Load project state from S3"""
    s3_client = get_s3_client()
    if not s3_client:
        st.error("Cannot load: S3 client not available")
        return None
    
    try:
        file_key = f"{get_user_folder(username)}/projects/project_state.pkl"
        
        st.info("📥 Loading project state from cloud...")
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        
        metadata = response.get('Metadata', {})
        if metadata.get('save_time'):
            st.info(f"Loading state saved at: {metadata.get('save_time')}")
        
        data = pickle.loads(response['Body'].read())
        if not isinstance(data, dict):
            st.error("Invalid project data format")
            return None
            
        st.success("✅ Project state loaded successfully!")
        return data
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            st.info("No saved project state found in cloud")
            return None
        else:
            st.error(f"❌ Error loading project state: {str(e)}")
            return None
    except Exception as e:
        st.error(f"❌ Error loading project state: {str(e)}")
        import traceback
        st.error(f"Debug info: {traceback.format_exc()}")
        return None

def list_user_files(username, file_type="figures", project_name=None):
    """List user's files from S3 within a project folder"""
    s3_client = get_s3_client()
    if not s3_client:
        return []
    
    try:
        proj = _sanitize(project_name or get_active_project_name(), "Project")
        prefix = f"{get_user_folder(username)}/projects/{proj}/{file_type}/"
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=prefix
        )
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'name': obj['Key'].split('/')[-1],
                    'modified': obj['LastModified'],
                    'size': obj['Size']
                })
        return files
    except Exception as e:
        st.error(f"Error listing files: {str(e)}")
        return []

# ====================== DASHBOARD CONFIGURATION ======================

# Configure Chinese fonts
def configure_chinese_fonts():
    """Configure matplotlib to support Chinese display"""
    system = platform.system()
    
    if system == "Windows":
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'SimSun']
    elif system == "Darwin":
        chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Arial Unicode MS']
    else:
        chinese_fonts = ['WenQuanYi Micro Hei', 'DejaVu Sans', 'Liberation Sans']
    
    for font in chinese_fonts:
        try:
            if font in [f.name for f in font_manager.fontManager.ttflist]:
                plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
                plt.rcParams['axes.unicode_minus'] = False
                return True
        except:
            continue
    
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    return True

configure_chinese_fonts()

# Language translations
TRANSLATIONS = {
    'en': {
        'page_title': '📊 FOB Test',
        'main_title': 'FOB Test',
        'main_subtitle': 'Visualize and compare Functional Observational Battery (FOB) test results',
        'language': 'Language',
        'login': 'Login',
        'register': 'Register',
        'username': 'Username',
        'password': 'Password',
        'email': 'Email',
        'name': 'Full Name',
        'logout': 'Logout',
        'welcome': 'Welcome',
        'my_files': 'My Files',
        'saved_figures': 'Saved Figures',
        'saved_data': 'Saved Data',
        'download': 'Download',
        'delete': 'Delete',
        'save_to_cloud': '☁️ Save to Cloud',
        'load_from_cloud': '☁️ Load from Cloud',
        'save_plot_to_cloud': '☁️ Save Plot to Cloud',
        'save_data_to_cloud': '☁️ Save Data to Cloud',
        'enter_name': 'Enter name (optional):',
        'plot_name': 'Plot name (optional):',
        'data_name': 'Data file name (optional):',
        'export_options': 'Export Options:',
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
        'body_weight': 'Body Weight',
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
        'weight_summary': '⚖️ Weight Change Summary',
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
        'about_title': 'About FOB Test',
        'tips': 'Tips:',
        'unsaved_changes': '⚠️ You have unsaved changes!',
        'changes_saved': '✅ Changes saved successfully!',
        'auto_saved': '✅ Auto-saved at',
        'add_new_timestep': 'Add new timestep:',
        'next_timestep': 'Next timestep (min)',
        'valid': 'Valid',
        'report_title': 'FOB Test Report',
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
        'binary_instruction': '🔍 **Instructions**: Click on any cell to toggle between Normal (default) and Abnormal (red).',
        'percentage_abnormal': '% Abnormal',
        'groups_to_plot': 'Groups to plot:',
        'select_groups_chart': 'Select groups to display in the chart:',
        'all_time_points': 'All Time Points',
        'before_experiment': 'Before Experiment',
        'after_experiment': 'After Experiment',
        'weight_change': 'Weight Change',
        'weight_g': 'Weight (g)',
        'percent_change': '% Change',
        'weight_instruction': '⚖️ **Instructions**: Enter the weight (in grams) for each animal before and after the experiment.',
        'mean_weight': 'Mean Weight',
        'weight_loss': 'Weight Loss',
        'weight_gain': 'Weight Gain',
        'no_change': 'No Change',
        'animal': 'Animal',
        'change_g': 'Change (g)',
        'initial_weight': 'Initial Weight',
        'final_weight': 'Final Weight'
    },
    'zh': {
        'page_title': '📊 FOB测试',
        'main_title': 'FOB测试',
        'main_subtitle': '可视化并比较功能观察电池（FOB）测试结果',
        'language': '语言',
        'login': '登录',
        'register': '注册',
        'username': '用户名',
        'password': '密码',
        'email': '电子邮件',
        'name': '全名',
        'logout': '退出',
        'welcome': '欢迎',
        'my_files': '我的文件',
        'saved_figures': '保存的图表',
        'saved_data': '保存的数据',
        'download': '下载',
        'delete': '删除',
        'save_to_cloud': '☁️ 保存到云端',
        'load_from_cloud': '☁️ 从云端加载',
        'save_plot_to_cloud': '☁️ 保存图表到云端',
        'save_data_to_cloud': '☁️ 保存数据到云端',
        'enter_name': '输入名称（可选）：',
        'plot_name': '图表名称（可选）：',
        'data_name': '数据文件名称（可选）：',
        'export_options': '导出选项：',
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
        'body_weight': '体重',
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
        'weight_summary': '⚖️ 体重变化汇总',
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
        'about_title': '关于FOB测试',
        'tips': '提示：',
        'unsaved_changes': '⚠️ 您有未保存的更改！',
        'changes_saved': '✅ 更改已成功保存！',
        'auto_saved': '✅ 自动保存于',
        'add_new_timestep': '添加新时间点：',
        'next_timestep': '下一个时间点（分钟）',
        'valid': '有效',
        'report_title': 'FOB测试报告',
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
        'binary_instruction': '🔍 **说明**：点击任意单元格在正常（默认）和异常（红色）之间切换。',
        'percentage_abnormal': '异常百分比',
        'groups_to_plot': '要绘制的组：',
        'select_groups_chart': '选择要在图表中显示的组：',
        'all_time_points': '所有时间点',
        'before_experiment': '实验前',
        'after_experiment': '实验后',
        'weight_change': '体重变化',
        'weight_g': '体重 (克)',
        'percent_change': '变化百分比',
        'weight_instruction': '⚖️ **说明**：输入每只动物实验前和实验后的体重（以克为单位）。',
        'mean_weight': '平均体重',
        'weight_loss': '体重减轻',
        'weight_gain': '体重增加',
        'no_change': '无变化',
        'animal': '动物',
        'change_g': '变化 (克)',
        'initial_weight': '初始体重',
        'final_weight': '最终体重'
    }
}

# Observation translations
OBSERVATION_TRANSLATIONS = {
    'en': {
        'spontaneous exploration': 'spontaneous exploration',
        'grooming': 'grooming',
        'smelling its congeners': 'smelling its congeners',
        'normal resting state': 'normal resting state',
        'alertness': 'alertness',
        'distending / oedema': 'distending / oedema',
        'bad condition': 'bad condition',
        'moribund': 'moribund',
        'dead': 'dead',
        'piloerection': 'piloerection',
        'skin color': 'skin color',
        'cyanosis': 'cyanosis',
        'respiratory activity': 'respiratory activity',
        'irregular breathing': 'irregular breathing',
        'stertorous': 'stertorous',
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
        'body temperature': 'body temperature',
        'body weight': 'body weight'
    },
    'zh': {
        'spontaneous exploration': '自发探索',
        'grooming': '理毛',
        'smelling its congeners': '嗅探同类',
        'normal resting state': '正常休息状态',
        'alertness': '警觉性',
        'distending / oedema': '肿胀/水肿',
        'bad condition': '状态不佳',
        'moribund': '濒死',
        'dead': '死亡',
        'piloerection': '立毛',
        'skin color': '皮肤颜色',
        'cyanosis': '发绀',
        'respiratory activity': '呼吸活动',
        'irregular breathing': '呼吸不规则',
        'stertorous': '鼾声呼吸',
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
        'body temperature': '体温',
        'body weight': '体重'
    }
}

# Initialize language
if 'language' not in st.session_state:
    st.session_state.language = 'en'

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
        .auth-container {
            background-color: white;
            border: 2px solid #1a3d6d;
            border-radius: 10px;
            padding: 30px;
            margin: 20px auto;
            max-width: 400px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .file-manager {
            background-color: #f0f8ff;
            border: 1px solid #1a3d6d;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
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
        .weight-table {
            margin-top: 20px;
        }
        .weight-loss {
            color: #ff4444;
            font-weight: bold;
        }
        .weight-gain {
            color: #00aa00;
            font-weight: bold;
        }
        .no-change {
            color: #666666;
        }
        </style>
    """, unsafe_allow_html=True)

set_custom_style()

# Constants for modes
GENERAL_BEHAVIOR_OBSERVATIONS = [
    'spontaneous exploration', 'grooming', 'smelling its congeners',
    'normal resting state', 'alertness', 'distending / oedema',
    'bad condition', 'moribund', 'dead'
]

AUTONOMIC_OBSERVATIONS = [
    'piloerection', 'skin color', 'cyanosis',
    'respiratory activity', 'irregular breathing', 'stertorous'
]

REFLEX_OBSERVATIONS = [
    'startle response', 'touch reactivity', 'vocalization', 'abnormal gait',
    'corneal reflex', 'pinna reflex', 'catalepsy', 'grip reflex',
    'pulling reflex', 'righting reflex', 'body tone', 'pain response'
]

CONVULSIVE_OBSERVATIONS = [
    'spontaneous activity', 'restlessness', 'fighting', 'writhing',
    'tremor', 'stereotypy', 'twitches / jerks', 'straub',
    'opisthotonus', 'convulsion'
]

ALL_MODES = [
    "General Behavior", "Autonomic and Sensorimotor Functions",
    "Reflex Capabilities", "Body Temperature", "Body Weight",
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

# ====================== HELPER FUNCTIONS ======================

def save_plot_as_bytes(fig):
    """Save matplotlib figure as bytes for download"""
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    return img_buffer.getvalue()

def save_plot_to_cloud_with_name(fig, username, figure_name, project_name=None):
    """Save plot to cloud under project folder with user-specified name"""
    if not figure_name:
        figure_name = f"plot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    proj = project_name or get_active_project_name()
    with st.spinner(f"Saving '{figure_name}' to cloud (project: {proj})..."):
        url, key = save_figure_to_s3(fig, username, figure_name, project_name=proj)
        
    if url and key:
        st.success(f"✅ Figure '{figure_name}' saved to cloud!")
        if url:
            st.markdown(f"📥 [Download Link]({url}) (valid for 1 hour)")
        st.info(f"📍 Saved as: {key}")

        # 👇 Print the directory (prefix)
        folder = key.rsplit('/', 1)[0] + '/'
        st.write("📁 Directory:")
        st.code(f"s3://{S3_BUCKET_NAME}/{folder}", language="bash")

        # (optional) also show the full object path
        st.write("🔑 Full object key:")
        st.code(f"s3://{S3_BUCKET_NAME}/{key}", language="bash")
        return True

    else:
        st.error("❌ Failed to save figure to cloud")
        st.info("Please check: 1) AWS credentials in Streamlit secrets, 2) S3 bucket permissions, 3) Internet connection")
        return False

def save_data_to_cloud_with_name(df, username, data_name, project_name=None):
    """Save data to cloud under project folder with user-specified name"""
    if not data_name:
        data_name = f"data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    proj = project_name or get_active_project_name()
    with st.spinner(f"Saving '{data_name}' to cloud (project: {proj})..."):
        key = save_dataframe_to_s3(df, username, data_name, project_name=proj)
        
    if key:
        st.success(f"✅ Data '{data_name}' saved to cloud!")
        st.info(f"📍 Saved as: {key}")
        st.info(f"📊 Data shape: {len(df)} rows × {len(df.columns)} columns")

        # 👇 Print the directory (prefix)
        folder = key.rsplit('/', 1)[0] + '/'
        st.write("📁 Directory:")
        st.code(f"s3://{S3_BUCKET_NAME}/{folder}", language="bash")

        # (optional) also show the full object path
        st.write("🔑 Full object key:")
        st.code(f"s3://{S3_BUCKET_NAME}/{key}", language="bash")
        return True

    else:
        st.error("❌ Failed to save data to cloud")
        st.info("Please check: 1) AWS credentials in Streamlit secrets, 2) S3 bucket permissions, 3) Internet connection")
        return False

def parse_score(score_str):
    """Parse 0/4/8 scoring system with +/- modifiers or Normal/Abnormal"""
    if pd.isna(score_str):
        return np.nan
    
    if str(score_str).lower() in ['normal', 'abnormal']:
        return 0 if str(score_str).lower() == 'normal' else 1
    
    if isinstance(score_str, (int, float)):
        return float(score_str)
    
    match = re.match(r'(\d+(?:\.\d+)?)([\+\-]*)', str(score_str))
    if not match:
        return np.nan
    
    base_score = float(match.group(1))
    modifiers = match.group(2)
    
    value = base_score
    if modifiers:
        modifier_value = len(modifiers) * (1 if '+' in modifiers else -1)
        value += modifier_value
    
    return value

def calculate_mean_score(animal_scores):
    """Calculate mean score from individual animal scores"""
    parsed_scores = [parse_score(score) for score in animal_scores if pd.notna(score)]
    if parsed_scores:
        return np.mean(parsed_scores)
    return np.nan

def generate_random_data(mode, times, num_animals=8, animal_type="mouse"):
    """Generate random data based on the mode"""
    if mode == "Body Temperature":
        if animal_type == "rat":
            base_temp_mean = 37.5
        elif animal_type == "mouse":
            base_temp_mean = 37.0
        else:
            base_temp_mean = 37.2
            
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
                base_temp = np.random.normal(base_temp_mean, 0.5)
                if time > 30:
                    base_temp += np.random.normal(0.2, 0.1)
                data[f'{animal_type}_{i}'].append(f"{base_temp:.1f}")
        
        return pd.DataFrame(data)
    
    elif mode == "Body Weight":
        if animal_type == "rat":
            base_weight_mean = 250
        elif animal_type == "mouse":
            base_weight_mean = 25
        else:
            base_weight_mean = 100
            
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time_label in ['before', 'after']:
            data['time'].append(time_label)
            data['observation'].append('body weight')
            for i in range(1, num_animals + 1):
                if time_label == 'before':
                    weight = np.random.normal(base_weight_mean, base_weight_mean * 0.1)
                else:
                    initial_weight = float(data[f'{animal_type}_{i}'][0])
                    if np.random.random() < 0.9:
                        weight_change = np.random.uniform(-0.05, -0.01) * initial_weight
                    else:
                        weight_change = np.random.uniform(0, 0.02) * initial_weight
                    weight = initial_weight + weight_change
                data[f'{animal_type}_{i}'].append(f"{weight:.1f}")
        
        return pd.DataFrame(data)
    
    elif mode in ["Convulsive Behaviors and Excitability", "Autonomic and Sensorimotor Functions", "Reflex Capabilities"]:
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
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in observations:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_animals + 1):
                    if np.random.random() < 0.8:
                        data[f'{animal_type}_{i}'].append('Normal')
                    else:
                        data[f'{animal_type}_{i}'].append('Abnormal')
        
        return pd.DataFrame(data)
    
    else:  # General Behavior
        behaviors = GENERAL_BEHAVIOR_OBSERVATIONS
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
                    if np.random.random() < 0.7:
                        base = 4
                    else:
                        base = np.random.choice([0, 8])
                    modifier = np.random.choice(['', '+', '-', '++', '--'], p=[0.5, 0.2, 0.2, 0.05, 0.05])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

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
    
    project_groups = [exp for exp in st.session_state.experiments.keys() 
                     if exp.startswith(project['name'])]
    
    filled_count = 0
    
    progress_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    total_worksheets = len(project_groups) * len(ALL_MODES)
    current_worksheet = 0
    
    for group in project_groups:
        for mode in ALL_MODES:
            current_worksheet += 1
            progress = current_worksheet / total_worksheets
            progress_bar.progress(progress)
            progress_placeholder.text(f"{t('filling_all')} ({current_worksheet}/{total_worksheets})")
            
            worksheet_key = f"worksheet_{group}_{mode}"
            
            if mode == "Autonomic and Sensorimotor Functions":
                observations = AUTONOMIC_OBSERVATIONS
            elif mode == "Reflex Capabilities":
                observations = REFLEX_OBSERVATIONS
            elif mode == "Convulsive Behaviors and Excitability":
                observations = CONVULSIVE_OBSERVATIONS
            elif mode == "Body Temperature":
                observations = ['body temperature']
            elif mode == "Body Weight":
                observations = ['body weight']
            else:
                observations = GENERAL_BEHAVIOR_OBSERVATIONS
            
            if worksheet_key not in st.session_state:
                if mode == "Body Weight":
                    times = ['before', 'after']
                else:
                    times = [0, 15, 30, 45, 60]
                
                data = []
                for time in times:
                    for obs in observations:
                        row = {'time': time, 'observation': obs}
                        for i in range(1, num_animals + 1):
                            if mode == "Body Temperature":
                                row[f'{animal_type}_{i}'] = '37.0'
                            elif mode == "Body Weight":
                                row[f'{animal_type}_{i}'] = '25.0' if animal_type == 'mouse' else '250.0'
                            elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                                row[f'{animal_type}_{i}'] = 'Normal'
                            else:
                                row[f'{animal_type}_{i}'] = '0'
                        data.append(row)
                st.session_state[worksheet_key] = pd.DataFrame(data)
            
            existing_df = st.session_state[worksheet_key]
            if mode == "Body Weight":
                times = ['before', 'after']
            else:
                times = sorted(existing_df['time'].unique())
            
            random_df = generate_random_data(mode, times, num_animals, animal_type)
            
            st.session_state[worksheet_key] = random_df
            st.session_state.worksheet_data[f"{group}_{mode}"] = random_df
            filled_count += 1
    
    progress_placeholder.empty()
    progress_bar.empty()
    
    return filled_count

def process_data_with_episodes(df, mode, animal_type="mouse", num_animals=8):
    """Process data and track onset/offset of abnormal episodes"""
    results = []
    
    if mode == "Body Weight":
        return pd.DataFrame(results)
    
    if mode == "Autonomic and Sensorimotor Functions":
        observations = AUTONOMIC_OBSERVATIONS
    elif mode == "Reflex Capabilities":
        observations = REFLEX_OBSERVATIONS
    elif mode == "Convulsive Behaviors and Excitability":
        observations = CONVULSIVE_OBSERVATIONS
    elif mode == "Body Temperature":
        observations = ['body temperature']
    else:
        observations = df['observation'].unique()
    
    for obs in observations:
        obs_df = df[df['observation'] == obs].sort_values('time')
        
        if obs_df.empty:
            continue
        
        onset_time = None
        in_episode = False
        peak_score = 0
        
        for _, row in obs_df.iterrows():
            animal_scores = [row[f'{animal_type}_{i}'] for i in range(1, num_animals + 1) 
                           if f'{animal_type}_{i}' in row]
            
            if mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                abnormal_count = sum(1 for score in animal_scores if str(score).lower() == 'abnormal')
                mean_score = (abnormal_count / len(animal_scores)) * 100 if animal_scores else 0
                is_abnormal = abnormal_count > 0
            else:
                mean_score = calculate_mean_score(animal_scores)
                
                if not pd.isna(mean_score) and mean_score > peak_score:
                    peak_score = mean_score
                
                is_abnormal = False
                if mode == "Body Temperature":
                    is_abnormal = mean_score < 36 or mean_score > 38
                else:
                    is_abnormal = mean_score < 2 or mean_score > 6
            
            if is_abnormal and not in_episode:
                onset_time = row['time']
                in_episode = True
                peak_score = mean_score
            elif not is_abnormal and in_episode:
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
        
        if in_episode and onset_time is not None:
            results.append({
                t('observation'): t_obs(obs),
                t('onset_time'): onset_time,
                t('offset_time'): obs_df['time'].max(),
                t('duration'): obs_df['time'].max() - onset_time,
                t('peak_score'): peak_score if mode not in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"] else f"{peak_score:.0f}%"
            })
    
    return pd.DataFrame(results)

def create_template(mode="General Behavior", num_animals=8, animal_type="mouse"):
    """Create template with individual animal columns"""
    if mode == "Body Temperature":
        times = [0, 15, 30, 45, 60]
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
                temp = np.random.normal(37.0, 0.2)
                data[f'{animal_type}_{i}'].append(f"{temp:.1f}")
        
        return pd.DataFrame(data)
    
    elif mode == "Body Weight":
        data = {
            'time': [],
            'observation': []
        }
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time_label in ['before', 'after']:
            data['time'].append(time_label)
            data['observation'].append('body weight')
            for i in range(1, num_animals + 1):
                if animal_type == "mouse":
                    weight = 25.0 if time_label == 'before' else 24.5
                elif animal_type == "rat":
                    weight = 250.0 if time_label == 'before' else 245.0
                else:
                    weight = 100.0 if time_label == 'before' else 98.0
                data[f'{animal_type}_{i}'].append(f"{weight:.1f}")
        
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
        for i in range(1, num_animals + 1):
            data[f'{animal_type}_{i}'] = []
        
        for time in times:
            for obs in observations:
                data['time'].append(time)
                data['observation'].append(obs)
                for i in range(1, num_animals + 1):
                    data[f'{animal_type}_{i}'].append('Normal')
        
        return pd.DataFrame(data)
    
    else:
        behaviors = GENERAL_BEHAVIOR_OBSERVATIONS
        times = [0, 15, 30]
        
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
                    base = random.choice([0, 4, 8])
                    modifier = random.choice(['', '+', '-', '++', '--'])
                    data[f'{animal_type}_{i}'].append(f"{base}{modifier}")
        
        return pd.DataFrame(data)

def create_worksheet(mode, experiment_name, project_info):
    """Create an editable worksheet for data entry"""
    st.subheader(f"{t('data_worksheet')} - {experiment_name}")
    
    animal_type = project_info.get('animal_type', 'mouse')
    if animal_type == 'custom':
        animal_type = project_info.get('custom_animal_name', 'animal')
    num_animals = project_info.get('num_animals', 8)
    
    if experiment_name in st.session_state.comparison_groups.get(st.session_state.active_project, []):
        st.success(t('is_comparison'))
    
    if mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
        st.markdown(f'<div class="binary-instruction">{t("binary_instruction")}</div>', unsafe_allow_html=True)
    elif mode == "Body Weight":
        st.markdown(f'<div class="binary-instruction">{t("weight_instruction")}</div>', unsafe_allow_html=True)
    
    worksheet_key = f"worksheet_{experiment_name}_{mode}"
    
    if worksheet_key not in st.session_state:
        if mode == "Autonomic and Sensorimotor Functions":
            observations = AUTONOMIC_OBSERVATIONS
        elif mode == "Reflex Capabilities":
            observations = REFLEX_OBSERVATIONS
        elif mode == "Convulsive Behaviors and Excitability":
            observations = CONVULSIVE_OBSERVATIONS
        elif mode == "Body Temperature":
            observations = ['body temperature']
        elif mode == "Body Weight":
            observations = ['body weight']
        else:
            observations = GENERAL_BEHAVIOR_OBSERVATIONS
        
        if mode == "Body Weight":
            times = ['before', 'after']
        else:
            times = [0, 15, 30, 45, 60]
        
        data = []
        for time in times:
            for obs in observations:
                row = {'time': time, 'observation': obs}
                for i in range(1, num_animals + 1):
                    if mode == "Body Temperature":
                        row[f'{animal_type}_{i}'] = '37.0'
                    elif mode == "Body Weight":
                        if animal_type == 'mouse':
                            row[f'{animal_type}_{i}'] = '25.0'
                        elif animal_type == 'rat':
                            row[f'{animal_type}_{i}'] = '250.0'
                        else:
                            row[f'{animal_type}_{i}'] = '100.0'
                    elif mode in ["Autonomic and Sensorimotor Functions", "Reflex Capabilities", "Convulsive Behaviors and Excitability"]:
                        row[f'{animal_type}_{i}'] = 'Normal'
                    else:
                        row[f'{animal_type}_{i}'] = '0'
                data.append(row)
        
        st.session_state[worksheet_key] = pd.DataFrame(data)
    
    df = st.session_state[worksheet_key].copy()
    
    if mode == "Body Weight":
        column_config = {
            'time': st.column_config.SelectboxColumn(
                t('time'),
                options=['before', 'after'],
                default='before',
                disabled=True
            ),
            'observation': st.column_config.TextColumn(t('observation'), disabled=True)
        }
    else:
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
    
    for i in range(1, num_animals + 1):
        if mode == "Body Temperature":
            column_config[f'{animal_type}_{i}'] = st.column_config.TextColumn(
                f'{t(animal_type).capitalize()} {i}',
                help=f"Temperature for {animal_type} {i} in Celsius (e.g., 37.2)",
                max_chars=5
            )
        elif mode == "Body Weight":
            column_config[f'{animal_type}_{i}'] = st.column_config.TextColumn(
                f'{t(animal_type).capitalize()} {i}',
                help=f"Weight for {animal_type} {i} in grams",
                max_chars=6
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
    
    tab1, tab2 = st.tabs([t('manual_save'), t('auto_save')])
    
    with tab1:
        st.markdown(f"**{t('manual_save')}**")
        
        temp_key = f"temp_{worksheet_key}"
        if temp_key in st.session_state and not df.equals(st.session_state[temp_key]):
            st.warning(t('unsaved_changes'))
        
        with st.form(key=f"form_{worksheet_key}"):
            edited_df = st.data_editor(
                df,
                column_config=column_config,
                use_container_width=True,
                num_rows="dynamic" if mode != "Body Weight" else "fixed",
                key=f"editor_{worksheet_key}_form",
                hide_index=True
            )
            
            st.session_state[temp_key] = edited_df
            
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                submitted = st.form_submit_button(t('save_changes'), use_container_width=True, type="primary")
            with col2:
                fill_random = st.form_submit_button(t('fill_random'), use_container_width=True)
            
            if mode != "Body Weight":
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
            else:
                add_timestep = False
                
            with col4:
                reset = st.form_submit_button(t('reset'), use_container_width=True)
            
            if submitted:
                st.session_state[worksheet_key] = edited_df.copy()
                st.session_state.worksheet_data[f"{experiment_name}_{mode}"] = edited_df.copy()
                st.session_state.save_status[experiment_name] = "saved"
                if temp_key in st.session_state:
                    del st.session_state[temp_key]
                st.success(t('changes_saved'))
                st.rerun()
            
            if fill_random:
                if mode == "Body Weight":
                    times = ['before', 'after']
                else:
                    times = sorted(edited_df['time'].unique())
                random_df = generate_random_data(mode, times, num_animals, animal_type)
                st.session_state[worksheet_key] = random_df
                st.rerun()
            
            if add_timestep and mode != "Body Weight":
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
                
                new_df = pd.concat([edited_df, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state[worksheet_key] = new_df
                st.rerun()
            
            if reset:
                if temp_key in st.session_state:
                    del st.session_state[temp_key]
                st.rerun()
    
    with tab2:
        st.markdown(f"**{t('auto_save')}**")
        st.info(t('edit_tip'))
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button(t('fill_random'), use_container_width=True, key=f"random_auto_{worksheet_key}"):
                if mode == "Body Weight":
                    times = ['before', 'after']
                else:
                    times = sorted(st.session_state[worksheet_key]['time'].unique())
                random_df = generate_random_data(mode, times, num_animals, animal_type)
                st.session_state[worksheet_key] = random_df
                st.rerun()
        
        edited_df_auto = st.data_editor(
            st.session_state[worksheet_key],
            column_config=column_config,
            use_container_width=True,
            num_rows="dynamic" if mode != "Body Weight" else "fixed",
            key=f"editor_{worksheet_key}_auto",
            hide_index=True
        )
        
        if not edited_df_auto.equals(st.session_state[worksheet_key]):
            st.session_state[worksheet_key] = edited_df_auto.copy()
            st.session_state.worksheet_data[f"{experiment_name}_{mode}"] = edited_df_auto.copy()
            st.session_state.save_status[experiment_name] = "saved"
        
        st.success(f"{t('auto_saved')} {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        if mode != "Body Weight":
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
                    
                    new_df = pd.concat([edited_df_auto, pd.DataFrame(new_rows)], ignore_index=True)
                    st.session_state[worksheet_key] = new_df
                    st.rerun()
    
    current_df = st.session_state[worksheet_key]
    
    if mode == "Body Weight":
        st.subheader(t('weight_summary'))
        
        weight_data = []
        before_df = current_df[current_df['time'] == 'before']
        after_df = current_df[current_df['time'] == 'after']
        
        if not before_df.empty and not after_df.empty:
            for i in range(1, num_animals + 1):
                animal_col = f'{animal_type}_{i}'  # <-- fix: was a list before
                if animal_col in before_df.columns:
                    try:
                        before_weight = float(before_df.iloc[0][animal_col])
                        after_weight = float(after_df.iloc[0][animal_col])
                        change = after_weight - before_weight
                        percent_change = (change / before_weight) * 100
                        
                        status = t('weight_loss') if change < 0 else (t('weight_gain') if change > 0 else t('no_change'))
                        
                        weight_data.append({
                            t('animal'): f'{t(animal_type).capitalize()} {i}',
                            f"{t('before_experiment')} (g)": f"{before_weight:.1f}",
                            f"{t('after_experiment')} (g)": f"{after_weight:.1f}",
                            f"{t('change_g')}": f"{change:.1f}",
                            t('percent_change'): f"{percent_change:.2f}%",
                            t('status'): status
                        })
                    except (ValueError, TypeError):
                        continue
        
        if weight_data:
            weight_df = pd.DataFrame(weight_data)
            st.dataframe(
                weight_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    t('status'): st.column_config.TextColumn(t('status'), width="small")
                }
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                before_key = f"{t('before_experiment')} (g)"
                mean_initial = np.mean([float(row[before_key]) for row in weight_data])
                st.metric(f"{t('mean_weight')} - {t('before_experiment')}", f"{mean_initial:.1f} g")
            with col2:
                after_key = f"{t('after_experiment')} (g)"
                mean_final = np.mean([float(row[after_key]) for row in weight_data])
                st.metric(f"{t('mean_weight')} - {t('after_experiment')}", f"{mean_final:.1f} g")
            with col3:
                change_key = t('change_g')
                mean_change = np.mean([float(row[change_key]) for row in weight_data])
                st.metric(f"{t('mean_weight')} {t('weight_change')}", f"{mean_change:.1f} g")
    else:
        st.subheader(t('mean_scores'))
        
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
                
                valid_scores = sum(1 for score in animal_scores if pd.notna(score) and score != '')
                
                if pd.isna(mean_score):
                    status = 'N/A'
                else:
                    if mode == "Body Temperature":
                        status = t('normal') if 36 <= mean_score <= 38 else t('abnormal')
                    else:
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
        
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                t('status'): st.column_config.TextColumn(t('status'), width="small")
            }
        )
        
        st.subheader(t('abnormal_episodes'))
        episodes_df = process_data_with_episodes(current_df, mode, animal_type, num_animals)
        if not episodes_df.empty:
            st.dataframe(episodes_df, use_container_width=True, hide_index=True)
        else:
            st.info(t('no_abnormal'))
    
    return current_df

def create_comparative_plot(selected_for_viz, mode_eng, project, comparison_group=None):
    """Create comparative plots for all analysis modes"""
    
    animal_type = project.get('animal_type', 'mouse')
    if animal_type == 'custom':
        animal_type = project.get('custom_animal_name', 'animal')
    num_animals = project.get('num_animals', 8)
    
    all_times = set()
    valid_groups = []
    
    for exp in selected_for_viz:
        worksheet_key = f"worksheet_{exp}_{mode_eng}"
        if worksheet_key in st.session_state:
            df = st.session_state[worksheet_key]
            if not df.empty:
                if mode_eng != "Body Weight":
                    all_times.update(df['time'].unique())
                valid_groups.append(exp)
    
    if not valid_groups:
        st.warning("No data available for visualization")
        return None
    
    if mode_eng == "General Behavior":
        selected_time = st.selectbox(
            t('select_time_compare'), 
            sorted(list(all_times)),
            key=f"time_select_{mode_eng}"
        )
        return create_general_behavior_plot(valid_groups, selected_time, mode_eng, animal_type, num_animals, comparison_group)
    elif mode_eng == "Body Weight":
        return create_body_weight_comparison_plot(valid_groups, mode_eng, animal_type, num_animals, comparison_group)
    else:
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

def create_body_weight_comparison_plot(valid_groups, mode_eng, animal_type, num_animals, comparison_group):
    """Create comparison plot for Body Weight mode"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    group_names = []
    before_means = []
    before_stds = []
    after_means = []
    after_stds = []
    percent_changes = []
    
    for group in valid_groups:
        worksheet_key = f"worksheet_{group}_{mode_eng}"
        if worksheet_key in st.session_state:
            df = st.session_state[worksheet_key]
            
            before_df = df[df['time'] == 'before']
            after_df = df[df['time'] == 'after']
            
            if not before_df.empty and not after_df.empty:
                before_weights = []
                after_weights = []
                changes = []
                
                for i in range(1, num_animals + 1):
                    animal_col = f'{animal_type}_{i}'
                    if animal_col in before_df.columns:
                        try:
                            before_weight = float(before_df.iloc[0][animal_col])
                            after_weight = float(after_df.iloc[0][animal_col])
                            before_weights.append(before_weight)
                            after_weights.append(after_weight)
                            changes.append(((after_weight - before_weight) / before_weight) * 100)
                        except (ValueError, TypeError):
                            continue
                
                if before_weights and after_weights:
                    group_names.append(group.split('_')[-1])
                    before_means.append(np.mean(before_weights))
                    before_stds.append(np.std(before_weights))
                    after_means.append(np.mean(after_weights))
                    after_stds.append(np.std(after_weights))
                    percent_changes.append(np.mean(changes))
    
    if not group_names:
        st.warning("No valid weight data found")
        return None
    
    x = np.arange(len(group_names))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, before_means, width, yerr=before_stds, 
                   label=t('before_experiment'), capsize=5, alpha=0.8, color='#3498db')
    bars2 = ax.bar(x + width/2, after_means, width, yerr=after_stds,
                   label=t('after_experiment'), capsize=5, alpha=0.8, color='#e74c3c')
    
    for i, group in enumerate(group_names):
        full_group = f"{st.session_state.projects[st.session_state.active_project]['name']}_Group_{group}"
        if full_group == comparison_group:
            bars1[i].set_color('#28a745')
            bars2[i].set_color('#1e7e34')
    
    for i, (before, after) in enumerate(zip(before_means, after_means)):
        ax.text(i - width/2, before + before_stds[i] + 0.5, f"{before:.1f}", 
                ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.text(i + width/2, after + after_stds[i] + 0.5, f"{after:.1f}", 
                ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        change_color = 'red' if percent_changes[i] < 0 else 'green'
        y_pos = max(before + before_stds[i], after + after_stds[i]) + 3
        ax.text(i, y_pos, f"{percent_changes[i]:+.1f}%", 
                ha='center', va='bottom', fontsize=11, fontweight='bold', 
                color=change_color, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor=change_color))
    
    ax.set_xlabel(t('group'), fontsize=14)
    ax.set_ylabel(f"{t('weight_g')}", fontsize=14)
    ax.set_title(f"{t('body_weight')} - {t('before_experiment')} vs {t('after_experiment')} {t('comparative_viz')}", 
                 fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(group_names, fontsize=12)
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')
    
    if min(before_means + after_means) < 0:
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    if min(before_means + after_means) >= 0:
        ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    return fig

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
    
    x_pos = range(len(group_names))
    bars = ax.bar(x_pos, overall_means, yerr=overall_stds, capsize=5, alpha=0.8)
    
    for i, (mean, group) in enumerate(zip(overall_means, group_names)):
        if group == comparison_group:
            bars[i].set_color('#28a745')
        elif mean < 2 or mean > 6:
            bars[i].set_color('#ff6b6b')
        else:
            bars[i].set_color('#4cc9f0')
    
    ax.set_title(f"{t('general_behavior')} - {t('comparative_viz')} ({selected_time} min)", fontsize=14, fontweight='bold')
    ax.set_ylabel(f"{t('mean_score')} (0-10)", fontsize=12)
    ax.set_xlabel(t('group'), fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([g.split('_')[-1] for g in group_names], rotation=45, ha='right')
    ax.set_ylim(0, 10)
    ax.grid(True, alpha=0.3, axis='y')
    
    ax.axhline(y=2, color='gray', linestyle='--', alpha=0.7, label='Lower threshold')
    ax.axhline(y=6, color='gray', linestyle='--', alpha=0.7, label='Upper threshold')
    
    for i, (mean, std) in enumerate(zip(overall_means, overall_stds)):
        ax.text(i, mean + std + 0.2, f"{mean:.2f}", ha='center', va='bottom', fontweight='bold')
    
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
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(selected_groups)))
    
    for idx, group in enumerate(selected_groups):
        worksheet_key = f"worksheet_{group}_{mode_eng}"
        if worksheet_key in st.session_state:
            df = st.session_state[worksheet_key]
            
            times = sorted(df['time'].unique())
            mean_temps = []
            std_temps = []
            
            for time in times:
                time_df = df[df['time'] == time]
                all_temps = []
                
                for _, row in time_df.iterrows():
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
    
    ax.axhspan(36, 38, alpha=0.2, color='green', label='Normal range (36-38°C)')
    
    ax.set_title(f"{t('body_temperature')} - {t('comparative_viz')} ({t('all_time_points')})", fontsize=16, fontweight='bold')
    ax.set_xlabel(f"{t('time')} (min)", fontsize=12)
    ax.set_ylabel("Temperature (°C)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    ax.set_ylim(34, 40)
    
    plt.tight_layout()
    return fig

def create_binary_score_line_plot(selected_groups, mode_eng, animal_type, num_animals, comparison_group):
    """Create line plot for binary (Normal/Abnormal) scoring modes"""
    if mode_eng == "Autonomic and Sensorimotor Functions":
        observations = AUTONOMIC_OBSERVATIONS
    elif mode_eng == "Reflex Capabilities":
        observations = REFLEX_OBSERVATIONS
    else:
        observations = CONVULSIVE_OBSERVATIONS
    
    n_obs = len(observations)
    n_cols = 3
    n_rows = (n_obs + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5*n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(selected_groups)))
    
    for obs_idx, obs in enumerate(observations):
        ax = axes[obs_idx]
        
        for group_idx, group in enumerate(selected_groups):
            worksheet_key = f"worksheet_{group}_{mode_eng}"
            if worksheet_key in st.session_state:
                df = st.session_state[worksheet_key]
                
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
        
        ax.set_title(t_obs(obs), fontsize=12, fontweight='bold')
        ax.set_xlabel(f"{t('time')} (min)", fontsize=10)
        ax.set_ylabel(f"{t('percentage_abnormal')} (%)", fontsize=10)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.3)
        
        if obs_idx == 0:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    for idx in range(n_obs, len(axes)):
        axes[idx].set_visible(False)
    
    mode_title = mode_eng.replace("and Sensorimotor Functions", "")
    fig.suptitle(f"{mode_title} - {t('comparative_viz')} ({t('all_time_points')})", fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    return fig

# ====================== AUTHENTICATION UI ======================
def show_auth_page():
    """Show authentication page"""
    st.markdown("<h1 style='text-align: center;'>🐭 FOB Test</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Secure Cloud-Based Analysis Platform</h3>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs([t('login'), t('register')])
    
    with tab1:
        with st.form("login_form"):
            st.subheader(t('login'))
            username = st.text_input(t('username'))
            password = st.text_input(t('password'), type="password")
            submit = st.form_submit_button(t('login'), use_container_width=True)
            
            if submit:
                if username and password:
                    success, result = authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_data = result
                        st.success(f"{t('welcome')}, {result['name']}!")
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        with st.form("register_form"):
            st.subheader(t('register'))
            new_username = st.text_input(t('username'), key="reg_username")
            new_password = st.text_input(t('password'), type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            email = st.text_input(t('email'))
            name = st.text_input(t('name'))
            submit_reg = st.form_submit_button(t('register'), use_container_width=True)
            
            if submit_reg:
                if new_username and new_password and email and name:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = register_user(new_username, new_password, email, name)
                        if success:
                            st.success(message + " Please login.")
                        else:
                            st.error(message)
                else:
                    st.error("Please fill all fields")

# ====================== MAIN DASHBOARD ======================
def show_dashboard():
    """Show main dashboard for authenticated users"""
    
    with st.sidebar:
        st.markdown(f"### {t('welcome')}, {st.session_state.user_data['name']}!")
        st.markdown(f"**{t('username')}:** {st.session_state.username}")
        
        st.markdown("---")
        
        st.selectbox(
            t('language'),
            options=['en', 'zh'],
            format_func=lambda x: 'English' if x == 'en' else '中文',
            key='language'
        )
        
        st.markdown("---")
        st.markdown("### ☁️ Cloud Storage")
        
        if st.button(t('save_to_cloud'), use_container_width=True):
            project_data = {
                'projects': st.session_state.get('projects', {}),
                'active_project': st.session_state.get('active_project', None),
                'experiments': st.session_state.get('experiments', {}),
                'worksheets': {k: v for k, v in st.session_state.items() if k.startswith('worksheet_')},
                'comparison_groups': st.session_state.get('comparison_groups', {})
            }
            if save_project_state(st.session_state.username, project_data):
                st.success("Project state saved to cloud!")
        
        if st.button(t('load_from_cloud'), use_container_width=True):
            saved_data = load_project_state(st.session_state.username)
            if saved_data:
                st.session_state.projects = saved_data.get('projects', {})
                st.session_state.active_project = saved_data.get('active_project', None)
                st.session_state.experiments = saved_data.get('experiments', {})
                st.session_state.comparison_groups = saved_data.get('comparison_groups', {})
                for key, value in saved_data.get('worksheets', {}).items():
                    st.session_state[key] = value
                st.success("Project state loaded from cloud!")
                st.rerun()
            else:
                st.info("No saved state found")
        
        st.markdown("---")
        st.markdown("### 📁 " + t('my_files'))

        current_project_name = get_active_project_name()
        st.caption(f"Listing files for project: **{current_project_name}**")

        with st.expander(t('saved_figures')):
            figures = list_user_files(st.session_state.username, "figures", project_name=current_project_name)
            if figures:
                for fig in figures:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(fig['name'])
                    with col2:
                        if st.button("📥", key=f"dl_{fig['key']}"):
                            s3_client = get_s3_client()
                            if s3_client:
                                url = s3_client.generate_presigned_url(
                                    'get_object',
                                    Params={'Bucket': S3_BUCKET_NAME, 'Key': fig['key']},
                                    ExpiresIn=3600
                                )
                                st.markdown(f"[Download]({url})")
            else:
                st.info("No saved figures")
        
        with st.expander(t('saved_data')):
            data_files = list_user_files(st.session_state.username, "data", project_name=current_project_name)
            if data_files:
                for file in data_files:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(file['name'])
                    with col2:
                        if st.button("📥", key=f"dl_data_{file['key']}"):
                            s3_client = get_s3_client()
                            if s3_client:
                                url = s3_client.generate_presigned_url(
                                    'get_object',
                                    Params={'Bucket': S3_BUCKET_NAME, 'Key': file['key']},
                                    ExpiresIn=3600
                                )
                                st.markdown(f"[Download]({url})")
            else:
                st.info("No saved data files")
        
        st.markdown("---")
        
        if st.button(t('logout'), use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.title(t('main_title'))
    st.markdown(t('main_subtitle'))
    
    # Template Section
    with st.expander(t('download_templates'), expanded=False):
        st.markdown(f"### {t('download_templates')}")
        
        template_mode = st.radio(t('template_type'), 
                                [t('general_behavior'), t('autonomic_functions'), 
                                 t('reflex_capabilities'), t('body_temperature'),
                                 t('body_weight'), t('convulsive_behaviors')],
                                index=0,
                                horizontal=True)
        
        mode_map = {
            t('general_behavior'): "General Behavior",
            t('autonomic_functions'): "Autonomic and Sensorimotor Functions",
            t('reflex_capabilities'): "Reflex Capabilities",
            t('body_temperature'): "Body Temperature",
            t('body_weight'): "Body Weight",
            t('convulsive_behaviors'): "Convulsive Behaviors and Excitability"
        }
        template_mode_eng = mode_map[template_mode]
        
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
                
            if st.button(t('create'), use_container_width=True):
                project_id = str(uuid.uuid4())
                st.session_state.active_project = project_id
                
                animal_type_map = {t('mouse'): 'mouse', t('rat'): 'rat', t('custom'): 'custom'}
                animal_type_eng = animal_type_map.get(animal_type, 'mouse')
                
                st.session_state.projects[project_id] = {
                    "name": project_name,
                    "animal_type": animal_type_eng,
                    "custom_animal_name": custom_animal_name,
                    "num_animals": num_animals,
                    "num_groups": num_groups
                }
                
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
        
        st.subheader(t('select_mode'))
        mode = st.radio(t('choose_mode'), 
                        [t('general_behavior'), t('autonomic_functions'), 
                         t('reflex_capabilities'), t('body_temperature'),
                         t('body_weight'), t('convulsive_behaviors')],
                        horizontal=True)
        
        mode_map = {
            t('general_behavior'): "General Behavior",
            t('autonomic_functions'): "Autonomic and Sensorimotor Functions",
            t('reflex_capabilities'): "Reflex Capabilities",
            t('body_temperature'): "Body Temperature",
            t('body_weight'): "Body Weight",
            t('convulsive_behaviors'): "Convulsive Behaviors and Excitability"
        }
        mode_eng = mode_map[mode]
        st.session_state.mode = mode_eng
        
        project_groups = [exp for exp in st.session_state.experiments.keys() 
                         if exp.startswith(project['name'])]
        
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
                
                if st.session_state.active_project in st.session_state.comparison_groups:
                    current_comp = st.session_state.comparison_groups[st.session_state.active_project]
                    if current_comp:
                        st.info(f"{t('comparison_group')}: **{current_comp[0]}**")
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader(t('experiment_groups'))
            
            if project_groups:
                selected_exp = st.selectbox(t('select_group_edit'), project_groups)
                
                if selected_exp:
                    st.info(t('edit_tip'))
                    
                    with st.container():
                        worksheet_df = create_worksheet(mode_eng, selected_exp, project)
                    
                    # Export with cloud save option
                    st.markdown("---")
                    st.markdown(f"**{t('export_options')}**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv = worksheet_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=t('export_csv'),
                            data=csv,
                            file_name=f"{selected_exp}_data.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        if st.session_state.get('authenticated', False):
                            with st.expander(t('save_data_to_cloud')):
                                default_data_name = f"{selected_exp}_{mode_eng.replace(' ', '_')}_data"
                                ns = f"{selected_exp}_{mode_eng}".replace(" ", "_")
                                data_name = st.text_input(
                                    t('data_name'),
                                    value=default_data_name,
                                    key=f"data_name_{ns}"
                                )
                                if st.button(t('save_to_cloud'), key=f"save_data_{ns}"):
                                    save_data_to_cloud_with_name(
                                        worksheet_df,
                                        st.session_state.username,
                                        data_name,
                                        project_name=project['name']
                                    )

                                        
        with col_right:
            st.subheader(t('data_analysis'))
            
            if project_groups:
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
                
                if 'selected_for_viz' in st.session_state:
                    selected_for_viz = st.session_state.selected_for_viz
                    del st.session_state.selected_for_viz
                
                if selected_for_viz:
                    st.markdown(f"### {t('comparative_report')}")
                    
                    animal_type = project.get('animal_type', 'mouse')
                    if animal_type == 'custom':
                        animal_type = project.get('custom_animal_name', 'animal')
                    num_animals = project.get('num_animals', 8)
                    
                    comp_group = None
                    if st.session_state.active_project in st.session_state.comparison_groups:
                        comp_groups = st.session_state.comparison_groups[st.session_state.active_project]
                        if comp_groups and comp_groups[0] in selected_for_viz:
                            comp_group = comp_groups[0]
                    
                    if mode_eng == "Body Weight":
                        weight_change_data = []
                        
                        for exp in selected_for_viz:
                            worksheet_key = f"worksheet_{exp}_{mode_eng}"
                            if worksheet_key in st.session_state:
                                df = st.session_state[worksheet_key]
                                
                                before_df = df[df['time'] == 'before']
                                after_df = df[df['time'] == 'after']
                                
                                if not before_df.empty and not after_df.empty:
                                    total_change = 0
                                    percent_changes = []
                                    
                                    for i in range(1, num_animals + 1):
                                        animal_col = f'{animal_type}_{i}'
                                        if animal_col in before_df.columns:
                                            try:
                                                before_weight = float(before_df.iloc[0][animal_col])
                                                after_weight = float(after_df.iloc[0][animal_col])
                                                change = after_weight - before_weight
                                                percent_change = (change / before_weight) * 100
                                                total_change += change
                                                percent_changes.append(percent_change)
                                            except (ValueError, TypeError):
                                                continue
                                    
                                    if percent_changes:
                                        mean_change = total_change / len(percent_changes)
                                        mean_percent = np.mean(percent_changes)
                                        
                                        status = t('weight_loss') if mean_change < 0 else (t('weight_gain') if mean_change > 0 else t('no_change'))
                                        
                                        weight_change_data.append({
                                            t('group'): exp,
                                            t('is_comparison'): '✓' if exp == comp_group else '',
                                            f"{t('mean_weight')} {t('change_g')}": f"{mean_change:.2f}",
                                            f"{t('mean_weight')} {t('percent_change')}": f"{mean_percent:.2f}%",
                                            t('status'): status
                                        })
                        
                        if weight_change_data:
                            st.markdown(f"#### {t('group_summary')}")
                            weight_summary_df = pd.DataFrame(weight_change_data)
                            st.dataframe(
                                weight_summary_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    t('is_comparison'): st.column_config.TextColumn(t('comparison_group'), width="small")
                                }
                            )
                    
                    else:
                        all_abnormal_episodes = {}
                        comparison_data = []
                        
                        for exp in selected_for_viz:
                            worksheet_key = f"worksheet_{exp}_{mode_eng}"
                            if worksheet_key in st.session_state:
                                df = st.session_state[worksheet_key]
                                
                                episodes_df = process_data_with_episodes(df, mode_eng, animal_type, num_animals)
                                if not episodes_df.empty:
                                    all_abnormal_episodes[exp] = episodes_df
                                
                                group_data = {
                                    t('group'): exp,
                                    t('is_comparison'): '✓' if exp == comp_group else '',
                                    t('total_episodes'): len(episodes_df) if not episodes_df.empty else 0,
                                    t('affected_obs'): ', '.join(episodes_df[t('observation')].unique()) if not episodes_df.empty else t('none')
                                }
                                comparison_data.append(group_data)
                        
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
                        
                        st.markdown(f"#### {t('episodes_by_group')}")
                        
                        if all_abnormal_episodes:
                            tabs = st.tabs([f"{group} ({len(episodes)})" for group, episodes in all_abnormal_episodes.items()])
                            
                            for i, (group, episodes) in enumerate(all_abnormal_episodes.items()):
                                with tabs[i]:
                                    if group == comp_group:
                                        st.info(t('is_comparison'))
                                    
                                    episodes[t('group')] = group
                                    
                                    st.dataframe(
                                        episodes[[t('observation'), t('onset_time'), t('offset_time'), t('duration'), t('peak_score')]],
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                    
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
                    
                    st.markdown(f"#### {t('comparative_viz')}")
                    
                    fig = create_comparative_plot(selected_for_viz, mode_eng, project, comp_group)
                    
                    if fig is not None:
                        st.pyplot(fig)
                        
                        # User-controlled save options
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 2, 2])
                        
                        with col1:
                            # Local download
                            plot_bytes = save_plot_as_bytes(fig)
                            st.download_button(
                                label=t('download_plot'),
                                data=plot_bytes,
                                file_name=f"{project['name']}_{mode_eng.replace(' ', '_')}_plot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png",
                                use_container_width=True
                            )
                        
                        with col2:
                            # Cloud save with custom name (project folder)
                            if st.session_state.get('authenticated', False):
                                with st.expander(t('save_plot_to_cloud')):
                                    default_name = f"{project['name']}_{mode_eng.replace(' ', '_')}_plot"
                                    ns_plot = f"{project['name']}_{mode_eng}".replace(" ", "_")
                                    plot_name = st.text_input(
                                        t('plot_name'),
                                        value=default_name,
                                        key=f"plot_name_{ns_plot}"
                                    )
                                    if st.button(t('save_to_cloud'), key=f"save_plot_{ns_plot}"):
                                        save_plot_to_cloud_with_name(
                                            fig,
                                            st.session_state.username,
                                            plot_name,
                                            project_name=project['name']
                                        )

                        
                        plt.close(fig)
                    
                    st.markdown(f"#### {t('export_report')}")
                    
                    report_data = {
                        t('project'): project['name'],
                        t('animal_type'): animal_display,
                        t('animals_per_group'): project['num_animals'],
                        t('analysis_mode'): mode,
                        t('total_groups'): len(selected_for_viz),
                        t('comparison_group'): comp_group or t('not_set'),
                        t('report_generated'): datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
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
                    
                    if mode_eng == "Body Weight" and 'weight_change_data' in locals():
                        for group_data in weight_change_data:
                            report_lines.append(f"\n{t('group')}: {group_data[t('group')]}")
                            if group_data[t('is_comparison')]:
                                report_lines.append(f"({t('comparison_group').upper()})")
                            weight_change_key = f"{t('mean_weight')} {t('change_g')}"
                            percent_change_key = f"{t('mean_weight')} {t('percent_change')}"
                            report_lines.append(f"{t('mean_weight')} {t('change_g')}: {group_data[weight_change_key]}")
                            report_lines.append(f"{t('mean_weight')} {t('percent_change')}: {group_data[percent_change_key]}")
                            report_lines.append(f"{t('status')}: {group_data[t('status')]}")
                    elif 'comparison_data' in locals():
                        for group_data in comparison_data:
                            report_lines.append(f"\n{t('group')}: {group_data[t('group')]}")
                            if group_data[t('is_comparison')]:
                                report_lines.append(f"({t('comparison_group').upper()})")
                            report_lines.append(f"{t('total_episodes')}: {group_data[t('total_episodes')]}")
                            report_lines.append(f"{t('affected_obs')}: {group_data[t('affected_obs')]}")
                        
                        if 'all_abnormal_episodes' in locals() and all_abnormal_episodes:
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
    
    if st.session_state.language == 'zh':
        st.markdown("""
    此增强型交互式FOB测试平台允许您：
    - **云端存储**：自动保存所有图表和数据到AWS S3
    - **用户认证**：安全的登录/注册系统
    - **项目持久化**：保存和加载完整的项目状态
    - **创建项目**，可自定义动物类型（小鼠、大鼠或自定义）
    - **指定每组动物数量**（灵活的组大小）
    - **一次创建多个组**（默认：每个项目5个组）
    - **指定对照组**作为参考
    - **一键为所有组的所有模式填充随机数据**
    - 为具有可自定义组大小的单个动物输入数据
    - **体重模式**：记录实验前后的体重，自动计算变化
    - **一般行为模式**：现在包括全面的健康状态观察
    - **综合报告**所有组的异常参数
    - **跟踪所有异常事件的起始和结束时间**
    - **视觉比较组**，突出显示对照组
    - **为所有分析模式生成图表**，支持下载和云端保存
    - 导出包含所有异常事件的详细报告
    - **完整的中英文界面支持**
    """)
    else:
        st.markdown("""
    This enhanced interactive FOB Test platform allows you to:
    - **Cloud Storage**: Automatically save all figures and data to AWS S3
    - **User Authentication**: Secure login/registration system
    - **Project Persistence**: Save and load complete project states
    - **Create projects** with customizable animal types (mice, rats, or custom)
    - **Specify the number of animals** per group (flexible group sizes)
    - **Create multiple groups at once** (default: 5 groups per project)
    - **Designate a comparison/control group** for reference
    - **Fill ALL groups across ALL modes with random data** with one click
    - Enter data for individual animals with customizable group sizes
    - **Body Weight mode**: Record weights before and after experiment with automatic change calculations
    - **General Behavior mode**: Now includes comprehensive health status observations
    - **Comprehensive reporting** of abnormal parameters across all groups
    - **Track onset and offset times** for all abnormal episodes
    - **Compare groups visually** with highlighted comparison group
    - **Generate plots for ALL analysis modes** with download and cloud save capability
    - Export detailed reports with all abnormal episodes
    - **Full Chinese language support** with language switcher
    """)

# ====================== MAIN APPLICATION ======================
def main():
    """Main application entry point"""
    
    if not check_authentication():
        show_auth_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
