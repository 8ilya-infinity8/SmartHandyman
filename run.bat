@echo off
echo Starting Home Repair Assistant...
echo.
echo Checking if .env file exists...
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file with your GOOGLE_API_KEY
    echo Example: GOOGLE_API_KEY=your_key_here
    pause
    exit /b 1
)

echo Starting Streamlit application...
streamlit run main.py
