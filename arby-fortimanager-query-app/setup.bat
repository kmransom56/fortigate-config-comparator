@echo off

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install requirements
pip install -r requirements.txt

REM Create .env file from .env.example if it doesn't exist
if not exist .env (
    copy .env.example .env
    echo Please edit the .env file with your FortiManager details.
)

REM Run the application
python app.py