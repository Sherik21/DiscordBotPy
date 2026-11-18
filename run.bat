@echo off
title Discord Music Bot (Sherik)
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)
if not exist .env (
    if exist .env.example (
        copy .env.example .env
    )
)
.venv\Scripts\python.exe -u main.py
pause
