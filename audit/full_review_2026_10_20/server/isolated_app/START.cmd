@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if errorlevel 1 goto directory_error
if not exist "%~dp0server.py" goto missing_files

where py >nul 2>&1
if errorlevel 1 goto check_python
py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 goto run_py

:check_python
where python >nul 2>&1
if errorlevel 1 goto check_bundled
python -c "import sys; raise SystemExit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 goto run_python

:check_bundled
set "BUNDLED_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%BUNDLED_PY%" goto missing_python
"%BUNDLED_PY%" -c "import sys; raise SystemExit(sys.version_info < (3, 12))" >nul 2>&1
if errorlevel 1 goto missing_python
goto run_bundled

:run_py
py -3 "%~dp0server.py" %*
set "RESULT=%ERRORLEVEL%"
goto finished

:run_python
python "%~dp0server.py" %*
set "RESULT=%ERRORLEVEL%"
goto finished

:run_bundled
"%BUNDLED_PY%" "%~dp0server.py" %*
set "RESULT=%ERRORLEVEL%"
goto finished

:directory_error
echo Nie można otworzyć folderu testera. Wypakuj archiwum do własnego folderu i spróbuj ponownie.
set "RESULT=1"
goto finished

:missing_files
echo Brakuje pliku server.py. Wypakuj całe archiwum ZIP, a następnie uruchom START.cmd.
set "RESULT=1"
goto finished

:missing_python
echo Do uruchomienia testera potrzebny jest Python 3.12 lub nowszy.
echo Zainstaluj go z https://www.python.org/downloads/ i zaznacz opcję "Add python.exe to PATH".
echo Następnie uruchom ponownie START.cmd. Nie są potrzebne żadne dodatkowe pakiety.
set "RESULT=1"
goto finished

:finished
if "%RESULT%"=="0" exit /b 0
echo.
echo Tester zakończył działanie z błędem. Przeczytaj komunikat powyżej.
echo Jeśli port 8765 jest zajęty, zamknij wcześniejsze okno testera i spróbuj ponownie.
pause
exit /b %RESULT%
