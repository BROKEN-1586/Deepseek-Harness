@echo off
rem ===== 每天 07:30 的零 token 体检（计划任务 ClearnDailyGate 调用；2026-10-28 建）=====
rem 只跑两个「只读」脚本：daily_gate.py 与 followup.py；产物在 D:\Clearn\_diag\
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "LOG=D:\Clearn\_diag\daily-0730.log"
set "PY=C:\Users\36578\AppData\Local\Programs\Python\Python314\python.exe"

echo. >> "%LOG%"
echo ===== %DATE% %TIME% ===== >> "%LOG%"

"%PY%" "D:\Clearn\tools\daily_gate.py" >> "%LOG%" 2>&1
echo ---- daily_gate rc=%errorlevel% ---- >> "%LOG%"

"%PY%" "D:\Clearn\tools\followup.py" >> "%LOG%" 2>&1
echo ---- followup rc=%errorlevel% ---- >> "%LOG%"
