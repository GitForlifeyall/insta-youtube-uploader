@echo off
title YouTube Shorts Redroid Studio Web Control
cd /d "%~dp0"
echo ========================================================
echo   YOUTUBE SHORTS REDROID STUDIO - WEB CONTROL
echo   Starting server at http://127.0.0.1:8080 ...
echo ========================================================
py -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
pause
