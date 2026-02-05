@echo off
setlocal

.venv\Scripts\python tools\validate_contracts.py
if errorlevel 1 (
  echo.
  echo [FAIL] contracts validation failed
  exit /b 1
)

echo.
echo [OK] contracts validation passed
exit /b 0
