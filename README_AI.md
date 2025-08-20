# FOB Test Analysis Dashboard - Complete Guide

## 🎯 Overview

The **FOB Test Analysis Dashboard** is a comprehensive, AI-powered tool for analyzing Functional Observational Battery (FOB) test data. This professional-grade application combines intuitive data entry, advanced analytics, AI-powered insights, and automated report generation to streamline your research workflow.

## ✨ Key Features

### 📊 **Data Management & Analysis**
- **Multi-mode Support**: 6 FOB test modes (General Behavior, Autonomic Functions, Reflex Capabilities, Body Temperature, Body Weight, Convulsive Behaviors)
- **Project Management**: Create, manage, and organize multiple experimental projects
- **Real-time Data Entry**: Interactive worksheets with manual and auto-save modes
- **Statistical Analysis**: Comprehensive statistical summaries and comparative analysis
- **Data Export**: CSV, Excel, and comprehensive report exports

### 🤖 **AI-Powered Features**
- **AI Tutor**: Interactive guidance for dashboard usage and best practices
- **AI Chatbot**: File analysis and data interpretation assistance
- **AI Report Generation**: Professional scientific reports with insights
- **AI PowerPoint Creation**: Automated presentation generation with charts and analysis

### 📈 **Visualization & Reporting**
- **Interactive Charts**: Dynamic plots and comparative visualizations
- **Summary Views**: 6 specialized summary types for different analysis needs
- **PowerPoint Generation**: Professional presentations with templates
- **Export Capabilities**: Multiple format support for all outputs

### 🌐 **User Experience**
- **Bilingual Support**: English and Chinese interface
- **Responsive Design**: Optimized for different screen sizes
- **Intuitive Navigation**: Clean, professional interface
- **Real-time Updates**: Instant feedback and data validation

## 🚀 Quick Start

### 1. Installation
```bash
# Clone or download the project
cd EzVis

# Install dependencies
pip install -r requirements.txt

# Activate virtual environment (if using)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 2. Launch Application
```bash
streamlit run main1.py
```

### 3. First Steps
1. **Create a Project**: Use the sidebar to create your first FOB test project
2. **Select Analysis Mode**: Choose from 6 different FOB test modes
3. **Enter Data**: Use the interactive worksheets to input your experimental data
4. **Generate Analysis**: Access summaries and AI-powered insights

## 📋 Detailed Feature Guide

### 🏗️ **Project Management**

#### Creating Projects
- Click "➕ New Project" in the sidebar
- Configure project settings:
  - **Project Name**: Descriptive name for your experiment
  - **Animal Type**: Mouse, Rat, or Custom
  - **Animals per Group**: Number of animals in each experimental group
  - **Number of Groups**: Total experimental groups

#### Managing Projects
- **Project Selection**: Use the dropdown in the sidebar to switch between projects
- **Project Info**: View current project details and settings
- **Project Deletion**: Remove projects with the delete button

### 📝 **Data Entry System**

#### Worksheet Modes
1. **Manual Save Mode**: 
   - Edit data with full control
   - Use "💾 Save" button to apply changes
   - "🎲 Random" button for test data generation
   - "🔄 Reset" to restore original data

2. **Auto Save Mode**:
   - Changes applied automatically
   - Real-time data validation
   - Quick random data generation

#### Data Types by Mode
- **General Behavior**: Scoring system (0/4/8 with +/- modifiers)
- **Autonomic Functions**: Binary Normal/Abnormal assessment
- **Reflex Capabilities**: Binary Normal/Abnormal assessment
- **Body Temperature**: Numerical values in Celsius
- **Body Weight**: Before/after measurements in grams
- **Convulsive Behaviors**: Binary Normal/Abnormal assessment

### 📊 **Summary View System**

#### Accessing Summaries
1. Click "📋 View Summaries" in the sidebar
2. Select from 6 summary types:
   - **Mean Scores Summary**: Statistical overview of scores
   - **Comparative Analysis Report**: Group comparisons with control
   - **Group Summary**: Basic statistics for each group
   - **Abnormal Episodes by Group**: Detailed episode analysis
   - **Comparative Visualization**: Interactive charts and plots
   - **AI Report**: AI-generated comprehensive analysis

#### Summary Layout
- **Two-column view**: Worksheet on left, selected summary on right
- **Group selection**: Choose which groups to include in analysis
- **Export options**: Download summaries in various formats

### 🤖 **AI Tools**

#### AI Tutor
- **Purpose**: Learn how to use the dashboard effectively
- **Features**: 
  - Interactive chat interface
  - Quick question buttons
  - Step-by-step guidance
  - Best practices and tips

#### AI Chatbot
- **Purpose**: Analyze uploaded files and answer data questions
- **Features**:
  - Multi-file upload support
  - File content summarization
  - Data interpretation assistance
  - Integration with AI reports

#### AI Report Generation
- **Purpose**: Generate professional scientific reports
- **Features**:
  - Mode-specific analysis
  - Statistical insights
  - Biological significance interpretation
  - Recommendations and conclusions
  - Multi-language support (English/Chinese)

#### AI PowerPoint Creation
- **Purpose**: Generate professional presentations
- **Features**:
  - Automated slide creation
  - Chart integration
  - Professional templates
  - Comprehensive content generation
  - Download in PPTX format

### 📈 **Visualization Features**

#### Interactive Charts
- **Comparative Plots**: Group comparisons across time points
- **Statistical Summaries**: Mean, standard deviation, and sample sizes
- **Trend Analysis**: Time-series visualization
- **Export Options**: High-resolution PNG downloads

#### Data Tables
- **Formatted Displays**: Clean, professional data presentation
- **Sorting & Filtering**: Easy data exploration
- **Export Capabilities**: CSV and Excel formats

## 🔧 Technical Specifications

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 1GB free space
- **Internet**: Required for AI features

### Dependencies
```
streamlit>=1.28.0          # Web framework
pandas>=2.0.0              # Data processing
numpy>=1.24.0              # Numerical computing
matplotlib>=3.7.0          # Basic plotting
seaborn>=0.12.0            # Statistical visualization
plotly>=5.15.0             # Interactive charts
openpyxl>=3.1.0            # Excel file handling
pyarrow>=12.0.0            # Fast data processing
xlsxwriter>=3.1.0          # Excel writing
google-generativeai>=0.3.0 # AI integration
python-pptx>=0.6.21        # PowerPoint generation
Pillow>=9.5.0              # Image processing
```

### AI Integration
- **Model**: Google Gemini (Pro/Flash variants)
- **API**: Pre-configured for immediate use
- **Fallback**: Automatic model switching for reliability
- **Languages**: English and Chinese support

## 🎨 User Interface

### Sidebar Organization
- **Language Selection**: English/Chinese toggle
- **Project Management**: Create, select, and manage projects
- **AI Tools**: Access to all AI features
- **Summary Views**: Quick access to analysis summaries

### Main Content Area
- **Adaptive Layout**: Changes based on active features
- **Data Entry**: Interactive worksheets with validation
- **Analysis Display**: Dynamic summary and visualization areas
- **Export Options**: Multiple format downloads

### Responsive Design
- **Mobile Friendly**: Optimized for tablet and mobile use
- **Desktop Optimized**: Full-featured desktop experience
- **Cross-platform**: Works on Windows, Mac, and Linux

## 📚 Usage Examples

### Example 1: Basic FOB Test Analysis
1. Create a new project for "Toxicity Study 2024"
2. Select "General Behavior" mode
3. Enter data for control and treatment groups
4. Use "📋 View Summaries" to access "Mean Scores Summary"
5. Generate AI report for professional analysis
6. Export results as PowerPoint presentation

### Example 2: Comparative Study
1. Load existing project with multiple groups
2. Set control group using the comparison selector
3. Access "Comparative Analysis Report" summary
4. Use "Comparative Visualization" for charts
5. Generate comprehensive AI report
6. Download all results for publication

### Example 3: File Analysis
1. Upload research papers or data files via AI Chatbot
2. Get file summaries and insights
3. Use summarized content in AI report generation
4. Create comprehensive analysis including external data
5. Generate professional presentation

## 🔒 Security & Privacy

### Data Protection
- **Local Processing**: All data processing occurs locally
- **No External Storage**: Your data never leaves your system
- **Secure AI**: Uses Google's secure AI infrastructure
- **API Security**: Pre-configured, secure API access

### Privacy Features
- **Session-based**: Data cleared when browser closes
- **No Tracking**: No user behavior tracking
- **Open Source**: Transparent code for security review

## 🛠️ Troubleshooting

### Common Issues

#### Installation Problems
```bash
# Update pip
pip install --upgrade pip

# Install with specific versions
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.8+
```

#### Runtime Errors
- **Import Errors**: Ensure all dependencies are installed
- **Memory Issues**: Close other applications, increase system memory
- **Display Problems**: Check browser compatibility (Chrome/Firefox recommended)

#### AI Feature Issues
- **API Errors**: Check internet connection
- **Slow Response**: Normal for complex analysis (10-30 seconds)
- **Model Fallback**: Automatic switching between AI models

### Performance Optimization
- **Large Datasets**: Use data sampling for initial analysis
- **Multiple Projects**: Archive unused projects
- **Browser Cache**: Clear cache if experiencing issues

## 🔮 Future Enhancements

### Planned Features
- **Advanced Statistics**: Additional statistical tests and analysis
- **Custom Templates**: User-defined PowerPoint templates
- **Batch Processing**: Multiple file analysis
- **Cloud Integration**: Optional cloud storage and sharing
- **API Access**: Programmatic access to dashboard features

### Community Contributions
- **Open Source**: Welcome contributions and improvements
- **Documentation**: User guides and tutorials
- **Feature Requests**: Community-driven development

## 📞 Support & Resources

### Documentation
- **User Guide**: This comprehensive guide
- **API Documentation**: Technical implementation details
- **Video Tutorials**: Step-by-step usage demonstrations

### Community
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Community support and ideas
- **Contributions**: Code, documentation, and testing

### Professional Support
- **Research Applications**: Academic and industry use cases
- **Customization**: Tailored solutions for specific needs
- **Training**: Workshops and training sessions

---

## 🎉 Getting Started Checklist

- [ ] Install Python 3.8+
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Launch application: `streamlit run main1.py`
- [ ] Create your first project
- [ ] Enter sample data
- [ ] Explore summary views
- [ ] Generate your first AI report
- [ ] Create a PowerPoint presentation
- [ ] Export your results

**Ready to revolutionize your FOB test analysis? Start exploring the dashboard today!** 🚀
