@echo off
setlocal
cd /d "%~dp0"
if defined COMMERCE_PYTHON (
  set "COMMERCE_RUNNER=%COMMERCE_PYTHON%"
) else (
  set "COMMERCE_RUNNER=%USERPROFILE%\.local\commerce-sql\venv\Scripts\python.exe"
)
if not exist "%COMMERCE_RUNNER%" (
  echo Install the dbt environment using dbt\README.md.
  echo Set COMMERCE_PYTHON to that environment's Python executable.
  pause
  exit /b 1
)
"%COMMERCE_RUNNER%" src\run_dbt.py --compare-demo --docs
if errorlevel 1 (
  echo Build stopped. The previous published data pointer was preserved.
  pause
  exit /b 1
)
echo.
echo Verified local snapshot ready. Open docs\SQL_DBT_FIRST_LESSON.md next.
pause
