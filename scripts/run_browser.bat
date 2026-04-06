@echo off
title NewsTrend Shadow Browser
echo [*] Starting Browser via D:\anaconda\anaconda\envs\AI\python.exe
"D:\anaconda\anaconda\envs\AI\python.exe" "E:\PycharmProject\AccioWork\NewsTrend\scripts\launch_browser.py"
if %errorlevel% neq 0 (
    echo.
    echo [!] ERROR: Browser failed to launch.
    pause
)
