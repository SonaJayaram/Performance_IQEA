@echo off
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
REM Set PYTHONPATH so Python can locate the root project modules
SET PYTHONPATH=%CD%

SET VENV_DIR=.venv
SET REQUIREMENTS=requirements.txt
SET INIT_DB_FILE=utilities\db_utils\init_db.py
SET STREAMLIT_SCRIPT=action_new_xpath.py
SET SETTINGS_FILE=config\settings.ini
SET POSTGRES_PATH=C:\postgresql\data
REM Check if virtual environment exists
IF NOT EXIST %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM Activate the virtual environment
CALL %VENV_DIR%\Scripts\activate

REM Install dependencies
IF EXIST %REQUIREMENTS% (
    python.exe -m pip install --upgrade pip
    echo Installing all dependencies...
    pip install -u -r %REQUIREMENTS%
) ELSE (
    echo No requirements.txt found, skipping installation.
)

REM Read source value from settings.ini
FOR /F "tokens=2 delims==" %%A IN ('findstr /R "^source *= *" "%SETTINGS_FILE%"') DO (
    SET "SOURCE=%%A"
)

REM Remove leading/trailing spaces
FOR /F "tokens=* delims= " %%A in ("!SOURCE!") DO SET SOURCE=%%A
REM Run init_db.py if source=database
IF /I "!SOURCE!"=="database" (
    REM Start the postgresql server
CALL pg_ctl -D %POSTGRES_PATH% -l logfile start
    echo Source is database. Running PostgreSQL initializer...
    python -m utilities.db_utils.init_db
)


REM Run the Streamlit script
IF EXIST %STREAMLIT_SCRIPT% (
    echo Running %STREAMLIT_SCRIPT%...
    set PYTHONUTF8=1
    streamlit run %STREAMLIT_SCRIPT%
) ELSE (
    echo %STREAMLIT_SCRIPT% not found!
)

REM Keep the window open
cmd /k
