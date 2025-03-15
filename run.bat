@echo off
REM Run script for Windows

REM Activate virtual environment if not already activated
if "%VIRTUAL_ENV%"=="" (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

REM Run the application
python src\main.py 