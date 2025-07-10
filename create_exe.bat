@echo off
echo Creating executable for Behavioral Observation Dashboard...
echo.

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install required packages
pip install streamlit pandas numpy matplotlib seaborn pyinstaller

REM Create executable
pyinstaller --onefile --name BehaviorDashboard --add-data "venv/Lib/site-packages/streamlit;streamlit" --add-data "venv/Lib/site-packages/altair;altair" --hidden-import "pandas._libs.tslibs.timedeltas" --hidden-import "pandas._libs.tslibs.np_datetime" --hidden-import "pandas._libs.tslibs.base" --hidden-import "pandas._libs.skiplist" dashboard.py

echo.
echo Executable created in dist folder!
echo You can now distribute BehaviorDashboard.exe to others
pause