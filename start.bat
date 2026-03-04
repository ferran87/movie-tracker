@echo off
echo Stopping any running Streamlit instances...
taskkill /F /IM python3.14.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Starting Movie Tracker...
cd /d "%~dp0"
python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false --server.port 8501
