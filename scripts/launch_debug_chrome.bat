@echo off
title [玄境] 启动“潜龙专用”调试版 Chrome (V2.5.5)
echo ======================================================
echo  [Xuanjing] Chrome Standalone Profile Mode
echo ======================================================

:: Use local project directory for the profile
set "PROJECT_ROOT=%~dp0.."
set "PROFILE_DIR=%PROJECT_ROOT%\data\chrome_profile"

if not exist "%PROFILE_DIR%" (
    echo [*] Creating dedicated profile directory...
    mkdir "%PROFILE_DIR%"
)

echo [*] Finding Chrome path via Registry...
set "CHROME_PATH="
for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" /ve 2^>nul') do set "CHROME_PATH=%%b"

if not defined CHROME_PATH (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
)

if not exist "%CHROME_PATH%" (
    echo [!] ERROR: Could not find Chrome.exe!
    pause
    exit /b
)

echo [*] Found Chrome at: "%CHROME_PATH%"
echo [*] Launching with DEDICATED profile: "%PROFILE_DIR%"
echo [*] Using Debug Port: 9222
echo.
echo ======================================================
echo  [IMPORTANT] 首次运行须知 (First Run Guide):
echo  1. 此窗口将弹出全新的 Chrome 浏览器（互不干扰）。
echo  2. 请在该窗口手动登录一次 X (Twitter)，勾选“记住我”。
echo  3. 只要该窗口不关闭，系统即可通过 CDP 协议进行“接管”采集。
echo  4. 若关闭该窗口，系统亦可通过“独立模式”静默运行（目录不再锁定）。
echo ======================================================

start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%PROFILE_DIR%" --restore-last-session
pause
