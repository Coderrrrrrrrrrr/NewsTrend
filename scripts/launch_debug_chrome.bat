@echo off
title NewsTrend Chrome Debugger
echo ======================================================
echo  [Xuanjing] Chrome Debug Mode Launcher V2.5.4
echo ======================================================

echo [*] Step 1: Cleaning existing Chrome processes...
taskkill /F /IM chrome.exe /T 2>nul
timeout /t 2 /nobreak >nul

echo [*] Step 2: Locating Chrome.exe via Registry...
set "CHROME_PATH="
for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" /ve 2^>nul') do set "CHROME_PATH=%%b"

if not defined CHROME_PATH (
    echo [!] Registry lookup failed, checking standard paths...
    if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
        set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
    ) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    )
)

if not defined CHROME_PATH (
    echo [ERROR] Could not find Chrome.exe!
    echo Please manually run: chrome.exe --remote-debugging-port=9222
    pause
    exit /b
)

echo [*] Found Chrome at: "%CHROME_PATH%"
echo [*] Step 3: Launching Chrome with --remote-debugging-port=9222...

start "" "%CHROME_PATH%" --remote-debugging-port=9222 --restore-last-session

echo.
echo ======================================================
echo  [SUCCESS] Chrome Debug Mode has been triggered.
echo  1. Please check if a Chrome window appeared.
echo  2. Verify: Visit http://127.0.0.1:9222 in Chrome.
echo  3. If you see JSON/text, you can start the Pulse now.
echo ======================================================
pause
