@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0qa\rgs_mock_server.py" %*
  goto finished
)
where python >nul 2>&1
if not errorlevel 1 (
  python "%~dp0qa\rgs_mock_server.py" %*
  goto finished
)
set "RGS_TEST_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%RGS_TEST_PY%" (
  "%RGS_TEST_PY%" "%~dp0qa\rgs_mock_server.py" %*
  goto finished
)
echo Wymagany Python 3.12 lub nowszy.
pause
exit /b 1
:finished
if errorlevel 1 pause
